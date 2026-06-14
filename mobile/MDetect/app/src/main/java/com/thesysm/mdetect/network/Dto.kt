package com.thesysm.mdetect.network

import com.google.gson.annotations.SerializedName

data class LoginRequest(val username: String, val password: String)
data class RefreshRequest(val refresh: String)
data class SignupRequest(
    val username: String,
    @SerializedName("phone_number") val phoneNumber: String,
    val password: String,
    @SerializedName("confirm_password") val confirmPassword: String
)
data class SessionRefreshRequest(
    val refresh: String,
    @SerializedName("device_token") val deviceToken: String
)
data class LogoutRequest(
    val refresh: String,
    @SerializedName("device_token") val deviceToken: String
)
data class TokenResponse(val access: String, val refresh: String? = null)
data class AuthUserDto(
    val id: Long,
    val username: String,
    @SerializedName("phone_number") val phoneNumber: String,
    @SerializedName("approval_status") val approvalStatus: String
)
data class AuthResponse(
    val access: String,
    val refresh: String,
    val user: AuthUserDto,
    @SerializedName("device_token") val deviceToken: String? = null,
    val message: String? = null
)
data class SignupResponse(
    val registered: Boolean,
    @SerializedName("approval_status") val approvalStatus: String? = null,
    val message: String? = null
)
data class SessionRefreshResponse(
    val connected: Boolean,
    val access: String? = null,
    val refresh: String? = null,
    val user: AuthUserDto? = null,
    val message: String? = null,
    val reason: String? = null
)
data class LogoutResponse(
    @SerializedName("logged_out") val loggedOut: Boolean,
    val message: String? = null
)
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
