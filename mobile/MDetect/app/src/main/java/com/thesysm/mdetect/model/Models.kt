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

data class ModelFileState(
    val modelExists: Boolean = false,
    val labelsExists: Boolean = false,
    val metadataExists: Boolean = false,
    val labelsCount: Int = 0,
    val modelBytes: Long = 0L
) {
    val summary: String
        get() = "model=${yesNo(modelExists)} labels=${yesNo(labelsExists)} metadata=${yesNo(metadataExists)} labels_count=$labelsCount"

    private fun yesNo(value: Boolean): String = if (value) "yes" else "no"
}

data class OnDeviceDebugState(
    val status: String = "Model not loaded",
    val modelVersion: String = "bundled-none",
    val inputShape: String = "-",
    val inputDtype: String = "-",
    val outputCount: Int = 0,
    val outputShapes: String = "-",
    val outputDtypes: String = "-",
    val decoderLayout: String = "-",
    val labelsCount: Int = 0,
    val metadataInputSize: Int = 640,
    val detectionsCount: Int = 0,
    val lastError: String = ""
)

data class AppSettings(
    val serverUrl: String,
    val detectionMode: DetectionMode = DetectionMode.ON_DEVICE,
    val frameIntervalMs: Long = 1000L,
    val confidenceThreshold: Float = 0.5f,
    val iouThreshold: Float = 0.45f,
    val username: String,
    val password: String
)

data class TokenState(
    val access: String = "",
    val refresh: String = "",
    val deviceToken: String = ""
) {
    val hasAccess: Boolean get() = access.isNotBlank()
    val canRestoreSession: Boolean get() = refresh.isNotBlank() && deviceToken.isNotBlank()
}

data class AuthUserState(
    val id: Long = 0L,
    val username: String = "",
    val phoneNumber: String = "",
    val approvalStatus: String = "",
    val connected: Boolean = false,
    val message: String = ""
)
