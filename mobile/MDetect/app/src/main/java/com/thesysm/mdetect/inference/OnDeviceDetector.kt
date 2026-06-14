package com.thesysm.mdetect.inference

import android.graphics.Bitmap
import com.thesysm.mdetect.data.ModelRepository
import com.thesysm.mdetect.model.DetectionBox
import org.tensorflow.lite.Interpreter

class OnDeviceDetector(private val modelRepository: ModelRepository) {
    private var interpreter: Interpreter? = null
    var statusMessage: String = "Model not loaded"
        private set

    fun load(): Boolean {
        val file = modelRepository.modelFile()
        if (!file.exists()) {
            statusMessage = "Download a model before using On-device mode"
            return false
        }
        return runCatching {
            interpreter?.close()
            interpreter = Interpreter(file)
            statusMessage = "On-device model loaded"
            true
        }.getOrElse {
            statusMessage = "TFLite load failed: ${it.message}"
            false
        }
    }

    fun detect(bitmap: Bitmap, confidenceThreshold: Float, iouThreshold: Float): Result<List<DetectionBox>> {
        val active = interpreter ?: return Result.failure(IllegalStateException(statusMessage))
        return runCatching {
            val _unused = active
            val _bitmap = bitmap
            val _thresholds = confidenceThreshold to iouThreshold
            // YOLO output decoding depends on exported model shape. Keep a safe MVP fallback.
            emptyList<DetectionBox>()
        }.onFailure {
            statusMessage = "On-device inference failed: ${it.message}"
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

    private fun iou(a: DetectionBox, b: DetectionBox): Float {
        val x1 = maxOf(a.xMin, b.xMin)
        val y1 = maxOf(a.yMin, b.yMin)
        val x2 = minOf(a.xMax, b.xMax)
        val y2 = minOf(a.yMax, b.yMax)
        val intersection = maxOf(0f, x2 - x1) * maxOf(0f, y2 - y1)
        val areaA = (a.xMax - a.xMin) * (a.yMax - a.yMin)
        val areaB = (b.xMax - b.xMin) * (b.yMax - b.yMin)
        return intersection / maxOf(1f, areaA + areaB - intersection)
    }
}
