package com.thesysm.mdetect.data

import android.os.Build
import com.thesysm.mdetect.BuildConfig
import com.thesysm.mdetect.model.DetectionBox
import com.thesysm.mdetect.model.ServerDetectionResult
import com.thesysm.mdetect.network.ApiClient
import com.thesysm.mdetect.network.DetectionHistoryItem
import com.thesysm.mdetect.network.ServerDetectResponse
import com.google.gson.Gson
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

class DetectionRepository(private val apiClient: ApiClient) {
    private val gson = Gson()

    suspend fun detectServer(jpegBytes: ByteArray): Result<ServerDetectionResult> = runCatching {
        val body = jpegBytes.toRequestBody("image/jpeg".toMediaType())
        val part = MultipartBody.Part.createFormData("image", "frame.jpg", body)
        val deviceInfo = "${Build.MANUFACTURER} ${Build.MODEL} / Android ${Build.VERSION.RELEASE}"
        val response = apiClient.api().detectServer(
            image = part,
            deviceInfo = deviceInfo.toRequestBody("text/plain".toMediaType()),
            appVersion = BuildConfig.VERSION_NAME.toRequestBody("text/plain".toMediaType())
        )
        if (!response.isSuccessful || response.body() == null) {
            val errorMessage = response.errorBody()?.string()?.let { body ->
                runCatching { gson.fromJson(body, ServerDetectResponse::class.java).message }.getOrNull()
            }
            error(errorMessage ?: "Server detection API not available: HTTP ${response.code()}")
        }
        val bodyResponse = response.body()!!
        if (bodyResponse.modelAvailable == false) {
            error(bodyResponse.message ?: "No active server model is available.")
        }
        val width = bodyResponse.imageWidth ?: 1
        val height = bodyResponse.imageHeight ?: 1
        val detections = bodyResponse.detections.map {
            DetectionBox(
                classId = it.classId,
                className = it.className,
                confidence = it.confidence,
                xMin = it.box.xMin,
                yMin = it.box.yMin,
                xMax = it.box.xMax,
                yMax = it.box.yMax,
                imageWidth = width,
                imageHeight = height
            )
        }
        ServerDetectionResult(
            detections = detections,
            modelAvailable = bodyResponse.modelAvailable ?: true,
            message = bodyResponse.message ?: "ok",
            modelVersion = bodyResponse.modelVersion,
            processingTimeMs = bodyResponse.processingTimeMs,
            logId = bodyResponse.logId
        )
    }

    suspend fun history(): Result<List<DetectionHistoryItem>> = runCatching {
        val response = apiClient.api().detectionHistory()
        if (!response.isSuccessful || response.body() == null) {
            error("Detection history API is not available: HTTP ${response.code()}")
        }
        response.body()!!.results
    }
}
