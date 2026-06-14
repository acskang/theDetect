package com.thesysm.mdetect.data

import android.content.Context
import android.util.Log
import com.google.gson.Gson
import com.thesysm.mdetect.model.ModelFileState
import com.thesysm.mdetect.model.ModelMetadata
import com.thesysm.mdetect.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.ResponseBody
import java.io.File

class ModelRepository(
    private val context: Context,
    private val apiClient: ApiClient
) {
    private val gson = Gson()
    private val currentDir = File(context.filesDir, "models/current")
    private val tempDir = File(context.filesDir, "models/tmp")

    fun currentMetadata(): ModelMetadata {
        val metadataFile = File(currentDir, "metadata.json")
        if (!metadataFile.exists()) return ModelMetadata()
        return runCatching {
            val json = gson.fromJson(metadataFile.readText(), Map::class.java)
            ModelMetadata(
                modelVersion = json["model_version"] as? String ?: "unknown",
                inputSize = (json["input_size"] as? Number)?.toInt() ?: 640,
                classes = (json["classes"] as? List<*>)?.mapNotNull { it as? String } ?: emptyList(),
                confidenceThreshold = (json["confidence_threshold"] as? Number)?.toFloat() ?: 0.5f,
                iouThreshold = (json["iou_threshold"] as? Number)?.toFloat() ?: 0.45f
            )
        }.getOrDefault(ModelMetadata())
    }

    fun modelFile(): File = File(currentDir, "model.tflite")
    fun labelsFile(): File = File(currentDir, "labels.txt")
    fun metadataFile(): File = File(currentDir, "metadata.json")

    fun localFileState(): ModelFileState {
        val model = modelFile()
        val labels = labelsFile()
        val metadata = metadataFile()
        return ModelFileState(
            modelExists = model.exists(),
            labelsExists = labels.exists(),
            metadataExists = metadata.exists(),
            labelsCount = if (labels.exists()) runCatching {
                labels.readLines().count { it.trim().isNotEmpty() }
            }.getOrDefault(0) else 0,
            modelBytes = if (model.exists()) model.length() else 0L,
        )
    }

    suspend fun checkLatestVersion(): Result<ModelMetadata> = runCatching {
        val response = apiClient.api().latestModel()
        if (!response.isSuccessful || response.body() == null) error("Latest model unavailable: HTTP ${response.code()}")
        val body = response.body()!!
        ModelMetadata(
            modelVersion = body.modelVersion,
            inputSize = body.inputSize,
            classes = body.classes,
            confidenceThreshold = body.confidenceThreshold,
            iouThreshold = body.iouThreshold
        )
    }

    suspend fun downloadLatestPackage(): Result<ModelMetadata> = withContext(Dispatchers.IO) {
        runCatching {
            val latestResponse = apiClient.api().latestModel()
            if (!latestResponse.isSuccessful || latestResponse.body() == null) {
                error("Latest model unavailable: HTTP ${latestResponse.code()}")
            }
            val latest = latestResponse.body()!!
            if (tempDir.exists()) tempDir.deleteRecursively()
            tempDir.mkdirs()
            Log.i(TAG, "Downloading model package version=${latest.modelVersion} temp=${tempDir.absolutePath}")
            downloadTo(latest.files.modelTflite, File(tempDir, "model.tflite"))
            downloadTo(latest.files.labels, File(tempDir, "labels.txt"))
            downloadTo(latest.files.metadata, File(tempDir, "metadata.json"))
            if (currentDir.exists()) currentDir.deleteRecursively()
            tempDir.renameTo(currentDir)
            Log.i(
                TAG,
                "Model package downloaded current=${currentDir.absolutePath} model=${modelFile().exists()} labels=${labelsFile().exists()} metadata=${metadataFile().exists()}"
            )
            currentMetadata()
        }
    }

    private suspend fun downloadTo(url: String, target: File) {
        val response = apiClient.api().downloadFile(url)
        if (!response.isSuccessful || response.body() == null) error("Download failed: $url HTTP ${response.code()}")
        response.body()!!.writeTo(target)
        Log.i(TAG, "Downloaded ${target.name} bytes=${target.length()} path=${target.absolutePath}")
    }

    private fun ResponseBody.writeTo(target: File) {
        target.outputStream().use { output ->
            byteStream().use { input -> input.copyTo(output) }
        }
    }

    companion object {
        private const val TAG = "MDetectModelUpdate"
    }
}
