package com.thesysm.mdetect.model

enum class DetectionMode {
    SERVER,
    ON_DEVICE
}

data class DetectionBox(
    val classId: Int,
    val className: String,
    val confidence: Float,
    val xMin: Float,
    val yMin: Float,
    val xMax: Float,
    val yMax: Float,
    val imageWidth: Int,
    val imageHeight: Int
)

data class ServerDetectionResult(
    val detections: List<DetectionBox>,
    val modelAvailable: Boolean,
    val message: String,
    val modelVersion: String?,
    val processingTimeMs: Long?,
    val logId: Long?
)

data class ModelMetadata(
    val modelVersion: String = "bundled-none",
    val inputSize: Int = 640,
    val classes: List<String> = emptyList(),
    val confidenceThreshold: Float = 0.5f,
    val iouThreshold: Float = 0.45f
)

data class AppSettings(
    val serverUrl: String,
    val detectionMode: DetectionMode = DetectionMode.SERVER,
    val frameIntervalMs: Long = 1000L,
    val confidenceThreshold: Float = 0.5f,
    val iouThreshold: Float = 0.45f,
    val username: String,
    val password: String
)

data class TokenState(
    val access: String = "",
    val refresh: String = ""
) {
    val hasAccess: Boolean get() = access.isNotBlank()
}
