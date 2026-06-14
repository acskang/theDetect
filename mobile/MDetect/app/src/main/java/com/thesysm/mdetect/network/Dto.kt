package com.thesysm.mdetect.network

import com.google.gson.annotations.SerializedName

data class LoginRequest(val username: String, val password: String)
data class RefreshRequest(val refresh: String)
data class TokenResponse(val access: String, val refresh: String? = null)
data class HealthResponse(val status: String, val service: String)

data class LatestModelResponse(
    @SerializedName("model_version") val modelVersion: String,
    @SerializedName("input_size") val inputSize: Int,
    val classes: List<String>,
    @SerializedName("confidence_threshold") val confidenceThreshold: Float,
    @SerializedName("iou_threshold") val iouThreshold: Float,
    val files: ModelFiles
)

data class ModelFiles(
    @SerializedName("model_tflite") val modelTflite: String,
    val labels: String,
    val metadata: String
)

data class ServerDetectResponse(
    val mode: String?,
    @SerializedName("model_version") val modelVersion: String?,
    @SerializedName("model_available") val modelAvailable: Boolean? = null,
    @SerializedName("processing_time_ms") val processingTimeMs: Long?,
    @SerializedName("image_width") val imageWidth: Int?,
    @SerializedName("image_height") val imageHeight: Int?,
    val detections: List<DetectionDto> = emptyList(),
    val message: String? = null,
    @SerializedName("log_id") val logId: Long? = null
)

data class DetectionDto(
    @SerializedName("class_id") val classId: Int,
    @SerializedName("class_name") val className: String,
    val confidence: Float,
    val box: BoxDto
)

data class BoxDto(
    @SerializedName("x_min") val xMin: Float,
    @SerializedName("y_min") val yMin: Float,
    @SerializedName("x_max") val xMax: Float,
    @SerializedName("y_max") val yMax: Float
)

data class DetectionHistoryItem(
    val id: Long? = null,
    val mode: String? = null,
    @SerializedName("model_version") val modelVersion: String? = null,
    @SerializedName("top_class") val topClass: String? = null,
    @SerializedName("top_confidence") val topConfidence: Float? = null,
    @SerializedName("created_at") val createdAt: String? = null
)

data class DetectionHistoryResponse(
    val results: List<DetectionHistoryItem> = emptyList()
)
