package com.thesysm.mdetect.inference

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.Log
import com.thesysm.mdetect.data.ModelRepository
import com.thesysm.mdetect.model.DetectionBox
import com.thesysm.mdetect.model.ModelMetadata
import com.thesysm.mdetect.model.OnDeviceDebugState
import com.google.gson.Gson
import org.tensorflow.lite.DataType
import org.tensorflow.lite.Interpreter
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.roundToInt

class OnDeviceDetector(private val modelRepository: ModelRepository) {
    private var interpreter: Interpreter? = null
    private var metadata: ModelMetadata = ModelMetadata()
    private var labels: List<String> = emptyList()
    private var inputShape: IntArray = intArrayOf(1, 640, 640, 3)
    private var inputDataType: DataType = DataType.FLOAT32
    private var outputShapes: List<IntArray> = emptyList()
    private var outputDataTypes: List<DataType> = emptyList()
    private var labelWarning: String = ""
    private var debugState: OnDeviceDebugState = OnDeviceDebugState()
    var statusMessage: String = "Model not loaded"
        private set

    fun debugState(): OnDeviceDebugState = debugState

    fun load(): Boolean {
        val file = modelRepository.modelFile()
        if (!file.exists()) {
            statusMessage = "Download model package first"
            debugState = OnDeviceDebugState(status = statusMessage, lastError = statusMessage)
            Log.w(TAG, "Missing model.tflite path=${file.absolutePath}")
            return false
        }
        return runCatching {
            interpreter?.close()
            Log.i(
                TAG,
                "Loading model model=${file.absolutePath} labels=${modelRepository.labelsFile().absolutePath} metadata=${modelRepository.metadataFile().absolutePath}"
            )
            metadata = loadMetadata()
            labels = loadLabels(metadata)
            val loaded = Interpreter(file)
            interpreter = loaded
            inputShape = loaded.getInputTensor(0).shape()
            inputDataType = loaded.getInputTensor(0).dataType()
            outputShapes = (0 until loaded.outputTensorCount).map { loaded.getOutputTensor(it).shape() }
            outputDataTypes = (0 until loaded.outputTensorCount).map { loaded.getOutputTensor(it).dataType() }
            statusMessage = buildLoadStatus()
            debugState = buildDebugState(status = statusMessage)
            Log.i(TAG, statusMessage)
            true
        }.getOrElse {
            statusMessage = "TFLite load failed: ${it.message}"
            debugState = buildDebugState(status = statusMessage, lastError = it.message ?: it.javaClass.simpleName)
            Log.e(TAG, "TFLite load failed path=${file.absolutePath} error=${it.message}", it)
            false
        }
    }

    fun detect(bitmap: Bitmap, confidenceThreshold: Float, iouThreshold: Float): Result<List<DetectionBox>> {
        val active = interpreter ?: return Result.failure(IllegalStateException(statusMessage))
        return runCatching {
            if (active.outputTensorCount != 1) {
                error("Unsupported TFLite output count: ${active.outputTensorCount}. Raw single-output YOLO is required.")
            }
            if (inputShape.size != 4 || inputShape[0] != 1 || inputShape[3] != 3) {
                error("Unsupported input tensor shape: ${inputShape.contentToString()}. Expected [1, size, size, 3].")
            }
            if (outputDataTypes.firstOrNull() != DataType.FLOAT32) {
                error("Unsupported output tensor dtype: ${outputDataTypes.firstOrNull()}. Expected FLOAT32.")
            }
            val inputSize = inputShape[1].takeIf { it > 0 } ?: metadata.inputSize
            val preprocessed = preprocess(bitmap, inputSize, inputDataType)
            val outputShape = outputShapes.firstOrNull() ?: error("Missing output tensor.")
            val output = allocateFloatOutput(outputShape)
            val startedAt = System.currentTimeMillis()
            active.run(preprocessed.input, output)
            val inferenceMs = System.currentTimeMillis() - startedAt
            val threshold = confidenceThreshold.takeIf { it > 0f } ?: metadata.confidenceThreshold
            val nmsThreshold = iouThreshold.takeIf { it > 0f } ?: metadata.iouThreshold
            val layout = inferOutputLayout(outputShape, labels.size)
            val decoderLayout = layout.description()
            Log.i(TAG, "Decoder layout=$decoderLayout threshold=$threshold iou=$nmsThreshold")
            val decoded = decodeYoloOutput(
                output = output,
                outputShape = outputShape,
                labels = labels,
                transform = preprocessed.transform,
                confidenceThreshold = threshold,
            )
            val selected = nms(decoded, nmsThreshold).take(MAX_DETECTIONS)
            statusMessage = "On-device ok objects=${selected.size}"
            debugState = buildDebugState(
                status = statusMessage,
                decoderLayout = decoderLayout,
                detectionsCount = selected.size,
            )
            Log.i(
                TAG,
                "Inference ok model=${metadata.modelVersion} time_ms=$inferenceMs decoded=${decoded.size} selected=${selected.size} input=${inputShape.contentToString()} output=${outputShape.contentToString()}"
            )
            selected
        }.onFailure {
            statusMessage = "On-device inference failed: ${it.message}"
            debugState = buildDebugState(status = statusMessage, lastError = it.message ?: it.javaClass.simpleName)
            Log.e(TAG, "Inference failed error=${it.message}", it)
        }
    }

    fun nms(boxes: List<DetectionBox>, iouThreshold: Float): List<DetectionBox> {
        val sorted = boxes.sortedByDescending { it.confidence }.toMutableList()
        val selected = mutableListOf<DetectionBox>()
        while (sorted.isNotEmpty()) {
            val current = sorted.removeAt(0)
            selected += current
            sorted.removeAll { it.classId == current.classId && iou(current, it) > iouThreshold }
        }
        return selected
    }

    internal fun iou(a: DetectionBox, b: DetectionBox): Float {
        val x1 = maxOf(a.xMin, b.xMin)
        val y1 = maxOf(a.yMin, b.yMin)
        val x2 = minOf(a.xMax, b.xMax)
        val y2 = minOf(a.yMax, b.yMax)
        val intersection = maxOf(0f, x2 - x1) * maxOf(0f, y2 - y1)
        val areaA = (a.xMax - a.xMin) * (a.yMax - a.yMin)
        val areaB = (b.xMax - b.xMin) * (b.yMax - b.yMin)
        return intersection / maxOf(1f, areaA + areaB - intersection)
    }

    private fun loadMetadata(): ModelMetadata {
        val metadataFile = modelRepository.metadataFile()
        if (!metadataFile.exists()) {
            Log.w(TAG, "metadata.json missing path=${metadataFile.absolutePath}")
            return ModelMetadata()
        }
        return runCatching {
            val json = Gson().fromJson(metadataFile.readText(), Map::class.java)
            ModelMetadata(
                modelVersion = json["model_version"] as? String ?: "unknown",
                inputSize = (json["input_size"] as? Number)?.toInt() ?: 640,
                classes = (json["classes"] as? List<*>)?.mapNotNull { it as? String } ?: emptyList(),
                confidenceThreshold = (json["confidence_threshold"] as? Number)?.toFloat() ?: 0.5f,
                iouThreshold = (json["iou_threshold"] as? Number)?.toFloat() ?: 0.45f
            )
        }.getOrElse {
            Log.e(TAG, "metadata.json parse failed path=${metadataFile.absolutePath} error=${it.message}", it)
            ModelMetadata()
        }
    }

    private fun loadLabels(metadata: ModelMetadata): List<String> {
        val labelsFile = modelRepository.labelsFile()
        val fileLabels = runCatching {
            labelsFile.readLines().map { it.trim() }.filter { it.isNotEmpty() }
        }.getOrElse {
            Log.w(TAG, "labels.txt read failed path=${labelsFile.absolutePath} error=${it.message}")
            emptyList()
        }
        if (!labelsFile.exists()) {
            Log.w(TAG, "labels.txt missing path=${labelsFile.absolutePath}")
        }
        val metadataLabels = metadata.classes
        if (fileLabels.isNotEmpty() && metadataLabels.isNotEmpty() && fileLabels != metadataLabels) {
            labelWarning = " labels/metadata mismatch"
            Log.w(TAG, "labels.txt count/order differs from metadata classes. labels=${fileLabels.size} metadata=${metadataLabels.size}")
        } else {
            labelWarning = ""
        }
        return fileLabels.ifEmpty { metadataLabels }
    }

    private fun buildLoadStatus(): String {
        val warning = if (labels.isEmpty()) " labels missing" else ""
        return "On-device model loaded version=${metadata.modelVersion} input=${inputShape.contentToString()} $inputDataType outputs=${
            outputShapes.mapIndexed { index, shape -> "${shape.contentToString()} ${outputDataTypes[index]}" }
        } metadata_input=${metadata.inputSize} labels=${labels.size}$warning$labelWarning"
    }

    private fun buildDebugState(
        status: String,
        decoderLayout: String = debugState.decoderLayout,
        detectionsCount: Int = debugState.detectionsCount,
        lastError: String = "",
    ): OnDeviceDebugState {
        return OnDeviceDebugState(
            status = status,
            modelVersion = metadata.modelVersion,
            inputShape = inputShape.contentToString(),
            inputDtype = inputDataType.toString(),
            outputCount = outputShapes.size,
            outputShapes = outputShapes.joinToString { it.contentToString() }.ifBlank { "-" },
            outputDtypes = outputDataTypes.joinToString { it.toString() }.ifBlank { "-" },
            decoderLayout = decoderLayout,
            labelsCount = labels.size,
            metadataInputSize = metadata.inputSize,
            detectionsCount = detectionsCount,
            lastError = lastError,
        )
    }

    private fun preprocess(bitmap: Bitmap, inputSize: Int, dataType: DataType): PreprocessedInput {
        val transform = letterboxTransform(bitmap.width, bitmap.height, inputSize)
        val target = Bitmap.createBitmap(inputSize, inputSize, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(target)
        canvas.drawColor(Color.BLACK)
        val resized = Bitmap.createScaledBitmap(bitmap, transform.resizedWidth, transform.resizedHeight, true)
        canvas.drawBitmap(resized, transform.padX, transform.padY, Paint(Paint.FILTER_BITMAP_FLAG))
        if (resized !== bitmap) resized.recycle()

        val input = when (dataType) {
            DataType.FLOAT32 -> floatInputBuffer(target)
            DataType.UINT8 -> uint8InputBuffer(target)
            else -> {
                target.recycle()
                error("Unsupported input tensor dtype: $dataType. FLOAT32 and UINT8 are supported.")
            }
        }
        target.recycle()
        return PreprocessedInput(input, transform)
    }

    private fun floatInputBuffer(bitmap: Bitmap): ByteBuffer {
        val buffer = ByteBuffer.allocateDirect(4 * bitmap.width * bitmap.height * 3).order(ByteOrder.nativeOrder())
        val pixels = IntArray(bitmap.width * bitmap.height)
        bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)
        pixels.forEach { pixel ->
            buffer.putFloat(Color.red(pixel) / 255f)
            buffer.putFloat(Color.green(pixel) / 255f)
            buffer.putFloat(Color.blue(pixel) / 255f)
        }
        buffer.rewind()
        return buffer
    }

    private fun uint8InputBuffer(bitmap: Bitmap): ByteBuffer {
        val buffer = ByteBuffer.allocateDirect(bitmap.width * bitmap.height * 3).order(ByteOrder.nativeOrder())
        val pixels = IntArray(bitmap.width * bitmap.height)
        bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)
        pixels.forEach { pixel ->
            buffer.put(Color.red(pixel).toByte())
            buffer.put(Color.green(pixel).toByte())
            buffer.put(Color.blue(pixel).toByte())
        }
        buffer.rewind()
        return buffer
    }

    private fun allocateFloatOutput(shape: IntArray): Any {
        if (shape.size != 3 || shape[0] != 1) {
            error("Unsupported output tensor shape: ${shape.contentToString()}. Expected [1, channels, boxes] or [1, boxes, channels].")
        }
        return Array(shape[0]) { Array(shape[1]) { FloatArray(shape[2]) } }
    }

    internal fun decodeYoloOutput(
        output: Any,
        outputShape: IntArray,
        labels: List<String>,
        transform: LetterboxTransform,
        confidenceThreshold: Float,
    ): List<DetectionBox> {
        @Suppress("UNCHECKED_CAST")
        val array = output as? Array<Array<FloatArray>>
            ?: error("Unsupported output container.")
        val first = array.firstOrNull() ?: return emptyList()
        val layout = inferOutputLayout(outputShape, labels.size)
        val decoded = mutableListOf<DetectionBox>()
        for (boxIndex in 0 until layout.boxes) {
            val values = FloatArray(layout.channels) { channel ->
                if (layout.channelsFirst) first[channel][boxIndex] else first[boxIndex][channel]
            }
            decodeCandidate(values, labels, transform, confidenceThreshold)?.let(decoded::add)
        }
        return decoded
    }

    internal fun inferOutputLayout(shape: IntArray, labelsCount: Int): OutputLayout {
        if (shape.size != 3 || shape[0] != 1) {
            error("Unsupported output tensor shape: ${shape.contentToString()}")
        }
        fun plausibleChannels(value: Int): Boolean {
            if (value < 5) return false
            if (labelsCount > 0 && (value == labelsCount + 4 || value == labelsCount + 5)) return true
            return value <= 512
        }
        val second = shape[1]
        val third = shape[2]
        return when {
            plausibleChannels(second) && third > second -> OutputLayout(channelsFirst = true, channels = second, boxes = third)
            plausibleChannels(third) && second > third -> OutputLayout(channelsFirst = false, channels = third, boxes = second)
            plausibleChannels(second) -> OutputLayout(channelsFirst = true, channels = second, boxes = third)
            plausibleChannels(third) -> OutputLayout(channelsFirst = false, channels = third, boxes = second)
            else -> error("Unsupported YOLO output shape: ${shape.contentToString()} labels=$labelsCount")
        }
    }

    private fun decodeCandidate(
        values: FloatArray,
        labels: List<String>,
        transform: LetterboxTransform,
        confidenceThreshold: Float,
    ): DetectionBox? {
        val classCountFromLabels = labels.size
        val hasObjectness = when {
            classCountFromLabels > 0 -> values.size == classCountFromLabels + 5
            values.size == 85 -> true
            else -> false
        }
        val classStart = if (hasObjectness) 5 else 4
        if (values.size <= classStart) return null
        var bestClass = 0
        var bestScore = Float.NEGATIVE_INFINITY
        for (index in classStart until values.size) {
            if (values[index] > bestScore) {
                bestScore = values[index]
                bestClass = index - classStart
            }
        }
        val objectness = if (hasObjectness) values[4] else 1f
        val confidence = objectness * bestScore
        if (!confidence.isFinite() || confidence < confidenceThreshold) return null

        val inputSize = transform.inputSize.toFloat()
        val normalized = values[0] <= 1.5f && values[1] <= 1.5f && values[2] <= 1.5f && values[3] <= 1.5f
        val cx = if (normalized) values[0] * inputSize else values[0]
        val cy = if (normalized) values[1] * inputSize else values[1]
        val width = if (normalized) values[2] * inputSize else values[2]
        val height = if (normalized) values[3] * inputSize else values[3]
        if (width <= 1f || height <= 1f) return null

        val restored = restoreBox(
            xMinModel = cx - width / 2f,
            yMinModel = cy - height / 2f,
            xMaxModel = cx + width / 2f,
            yMaxModel = cy + height / 2f,
            transform = transform,
        )
        if (restored.width < 2f || restored.height < 2f) return null
        return DetectionBox(
            classId = bestClass,
            className = labels.getOrNull(bestClass) ?: "class_$bestClass",
            confidence = confidence,
            xMin = restored.xMin,
            yMin = restored.yMin,
            xMax = restored.xMax,
            yMax = restored.yMax,
            imageWidth = transform.originalWidth,
            imageHeight = transform.originalHeight,
        )
    }

    internal fun restoreBox(
        xMinModel: Float,
        yMinModel: Float,
        xMaxModel: Float,
        yMaxModel: Float,
        transform: LetterboxTransform,
    ): RestoredBox {
        val xMin = ((xMinModel - transform.padX) / transform.scale).coerceIn(0f, transform.originalWidth.toFloat())
        val yMin = ((yMinModel - transform.padY) / transform.scale).coerceIn(0f, transform.originalHeight.toFloat())
        val xMax = ((xMaxModel - transform.padX) / transform.scale).coerceIn(0f, transform.originalWidth.toFloat())
        val yMax = ((yMaxModel - transform.padY) / transform.scale).coerceIn(0f, transform.originalHeight.toFloat())
        return RestoredBox(
            xMin = minOf(xMin, xMax),
            yMin = minOf(yMin, yMax),
            xMax = maxOf(xMin, xMax),
            yMax = maxOf(yMin, yMax),
        )
    }

    internal fun letterboxTransform(originalWidth: Int, originalHeight: Int, inputSize: Int): LetterboxTransform {
        val scale = minOf(inputSize.toFloat() / originalWidth.toFloat(), inputSize.toFloat() / originalHeight.toFloat())
        val resizedWidth = (originalWidth * scale).roundToInt().coerceIn(1, inputSize)
        val resizedHeight = (originalHeight * scale).roundToInt().coerceIn(1, inputSize)
        return LetterboxTransform(
            originalWidth = originalWidth,
            originalHeight = originalHeight,
            inputSize = inputSize,
            scale = scale,
            padX = (inputSize - resizedWidth) / 2f,
            padY = (inputSize - resizedHeight) / 2f,
            resizedWidth = resizedWidth,
            resizedHeight = resizedHeight,
        )
    }

    data class LetterboxTransform(
        val originalWidth: Int,
        val originalHeight: Int,
        val inputSize: Int,
        val scale: Float,
        val padX: Float,
        val padY: Float,
        val resizedWidth: Int,
        val resizedHeight: Int,
    )

    data class RestoredBox(
        val xMin: Float,
        val yMin: Float,
        val xMax: Float,
        val yMax: Float,
    ) {
        val width: Float get() = xMax - xMin
        val height: Float get() = yMax - yMin
    }

    internal data class OutputLayout(
        val channelsFirst: Boolean,
        val channels: Int,
        val boxes: Int,
    ) {
        fun description(): String = if (channelsFirst) {
            "channels_first channels=$channels boxes=$boxes"
        } else {
            "boxes_first channels=$channels boxes=$boxes"
        }
    }

    private data class PreprocessedInput(
        val input: ByteBuffer,
        val transform: LetterboxTransform,
    )

    companion object {
        private const val TAG = "MDetectOnDevice"
        private const val MAX_DETECTIONS = 50
    }
}
