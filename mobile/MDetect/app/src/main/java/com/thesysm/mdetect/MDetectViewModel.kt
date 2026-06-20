package com.thesysm.mdetect

import android.app.Application
import android.graphics.BitmapFactory
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.thesysm.mdetect.data.AuthRepository
import com.thesysm.mdetect.data.DetectionRepository
import com.thesysm.mdetect.data.ModelRepository
import com.thesysm.mdetect.data.SettingsRepository
import com.thesysm.mdetect.inference.OnDeviceDetector
import com.thesysm.mdetect.model.AppSettings
import com.thesysm.mdetect.model.AuthUserState
import com.thesysm.mdetect.model.DetectionBox
import com.thesysm.mdetect.model.DetectionMode
import com.thesysm.mdetect.model.ModelFileState
import com.thesysm.mdetect.model.ModelMetadata
import com.thesysm.mdetect.model.OnDeviceDebugState
import com.thesysm.mdetect.network.ApiClient
import com.thesysm.mdetect.network.DetectionHistoryItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import kotlin.system.measureTimeMillis

data class AppUiState(
    val loading: Boolean = true,
    val screen: AppScreen = AppScreen.SPLASH,
    val settings: AppSettings = AppSettings(
        serverUrl = BuildConfig.DEFAULT_SERVER_URL,
        username = BuildConfig.DEFAULT_USERNAME,
        password = BuildConfig.DEFAULT_PASSWORD
    ),
    val modelMetadata: ModelMetadata = ModelMetadata(),
    val serverStatus: String = "Unknown",
    val detectionStatus: String = "Idle",
    val networkStatus: String = "Unknown",
    val detections: List<DetectionBox> = emptyList(),
    val history: List<DetectionHistoryItem> = emptyList(),
    val fps: Float = 0f,
    val latencyMs: Long = 0L,
    val detecting: Boolean = false,
    val latestServerModel: ModelMetadata? = null,
    val modelFileState: ModelFileState = ModelFileState(),
    val onDeviceDebug: OnDeviceDebugState = OnDeviceDebugState(),
    val authUser: AuthUserState = AuthUserState(),
    val authStatus: String = "Disconnected",
    val authMessage: String = "",
    val offlineDetectionAllowed: Boolean = false,
    val loginFailurePromptVisible: Boolean = false,
    val cameraStatusOverlayVisible: Boolean = true
)

enum class AppScreen {
    SPLASH,
    LANDING,
    LOGIN,
    SIGN_UP,
    HOME,
    CAMERA,
    HISTORY,
    MODEL_UPDATE,
    SETTINGS
}

class MDetectViewModel(application: Application) : AndroidViewModel(application) {
    private val settingsRepository = SettingsRepository(application)
    private val apiClient = ApiClient(settingsRepository)
    private val authRepository = AuthRepository(settingsRepository, apiClient)
    private val modelRepository = ModelRepository(application, apiClient)
    private val detectionRepository = DetectionRepository(apiClient)
    private val onDeviceDetector = OnDeviceDetector(modelRepository)
    private var onDeviceFrameInFlight = false

    private val _uiState = MutableStateFlow(AppUiState())
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            settingsRepository.settingsFlow.collectLatest { settings ->
                _uiState.value = _uiState.value.copy(settings = settings)
            }
        }
        viewModelScope.launch {
            settingsRepository.authUserFlow.collectLatest { authUser ->
                _uiState.value = _uiState.value.copy(
                    authUser = authUser,
                    authStatus = if (authUser.connected) "Connected" else "Disconnected",
                    authMessage = authUser.message
                )
            }
        }
        bootstrap()
    }

    fun bootstrap() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, detectionStatus = "Starting", authStatus = "Disconnected")
            val session = authRepository.restoreSession()
            val health = runCatching { apiClient.api().health() }
            val connected = session.isSuccess
            _uiState.value = _uiState.value.copy(
                loading = false,
                screen = if (connected) AppScreen.HOME else AppScreen.LANDING,
                modelMetadata = modelRepository.currentMetadata(),
                modelFileState = modelRepository.localFileState(),
                serverStatus = if (health.getOrNull()?.isSuccessful == true) "Connected" else "Unavailable",
                networkStatus = if (connected) "Connected" else "Disconnected",
                authStatus = if (connected) "Connected" else "Disconnected",
                authMessage = session.getOrNull() ?: session.exceptionOrNull()?.message.orEmpty(),
                detectionStatus = if (connected) "Ready" else "Login required"
            )
        }
    }

    fun navigate(screen: AppScreen) {
        if (screen == AppScreen.MODEL_UPDATE && _uiState.value.offlineDetectionAllowed) {
            _uiState.value = _uiState.value.copy(networkStatus = "Model update is disabled in offline detection mode")
            return
        }
        _uiState.value = _uiState.value.copy(
            screen = screen,
            modelMetadata = if (screen == AppScreen.MODEL_UPDATE) modelRepository.currentMetadata() else _uiState.value.modelMetadata,
            modelFileState = if (screen == AppScreen.MODEL_UPDATE) modelRepository.localFileState() else _uiState.value.modelFileState,
        )
        if (screen == AppScreen.HISTORY) loadHistory()
    }

    fun saveSettings(settings: AppSettings) {
        viewModelScope.launch {
            settingsRepository.saveSettings(settings)
            _uiState.value = _uiState.value.copy(settings = settings, networkStatus = "Settings saved")
        }
    }

    fun testConnection() {
        viewModelScope.launch {
            val response = runCatching { apiClient.api().health() }.getOrNull()
            val status = if (response?.isSuccessful == true) "Connected" else "Unavailable"
            _uiState.value = _uiState.value.copy(serverStatus = status, networkStatus = "Server test: $status")
        }
    }

    fun login(username: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(networkStatus = "Logging in", authStatus = "Disconnected")
            val result = authRepository.login(username, password)
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(
                    screen = AppScreen.HOME,
                    networkStatus = "Connected",
                    authStatus = "Connected",
                    authMessage = result.getOrThrow(),
                    offlineDetectionAllowed = false,
                    loginFailurePromptVisible = false,
                    detectionStatus = "Ready"
                )
            } else {
                _uiState.value.copy(
                    networkStatus = "Login failed: ${result.exceptionOrNull()?.message}",
                    authStatus = "Login required",
                    authMessage = result.exceptionOrNull()?.message ?: "Login failed",
                    offlineDetectionAllowed = false,
                    loginFailurePromptVisible = true
                )
            }
        }
    }

    fun continueAfterLoginFailure() {
        _uiState.value = _uiState.value.copy(
            screen = AppScreen.HOME,
            settings = _uiState.value.settings.copy(detectionMode = DetectionMode.ON_DEVICE),
            modelMetadata = modelRepository.currentMetadata(),
            modelFileState = modelRepository.localFileState(),
            networkStatus = "Offline detection mode",
            authStatus = "Offline",
            authMessage = "로그인 실패로 모델 최신버전을 확인할 수 없습니다.",
            offlineDetectionAllowed = true,
            loginFailurePromptVisible = false,
            detectionStatus = "Ready"
        )
    }

    fun dismissLoginFailurePrompt() {
        _uiState.value = _uiState.value.copy(loginFailurePromptVisible = false)
    }

    fun signup(username: String, phoneNumber: String, password: String, confirmPassword: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(networkStatus = "Signing up")
            val result = authRepository.signup(username, phoneNumber, password, confirmPassword)
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(
                    screen = AppScreen.LOGIN,
                    networkStatus = "Signup requested",
                    authStatus = "Approval pending",
                    authMessage = result.getOrThrow()
                )
            } else {
                _uiState.value.copy(
                    networkStatus = "Signup failed: ${result.exceptionOrNull()?.message}",
                    authStatus = "Disconnected",
                    authMessage = result.exceptionOrNull()?.message ?: "Signup failed"
                )
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            val result = authRepository.logout()
            _uiState.value = _uiState.value.copy(
                screen = AppScreen.LANDING,
                authUser = AuthUserState(),
                authStatus = "Login required",
                authMessage = result.getOrNull().orEmpty(),
                offlineDetectionAllowed = false,
                loginFailurePromptVisible = false,
                networkStatus = result.getOrNull() ?: "Logout failed: ${result.exceptionOrNull()?.message}",
                detectionStatus = "Login required",
                detecting = false,
                detections = emptyList(),
                history = emptyList(),
            )
        }
    }

    fun checkLatestModel() {
        viewModelScope.launch {
            if (_uiState.value.offlineDetectionAllowed) {
                _uiState.value = _uiState.value.copy(networkStatus = "Model update is disabled in offline detection mode")
                return@launch
            }
            val auth = authRepository.refreshOrLogin()
            if (auth.isFailure) {
                _uiState.value = _uiState.value.copy(networkStatus = "Login failed: ${auth.exceptionOrNull()?.message}")
                return@launch
            }
            val result = modelRepository.checkLatestVersion()
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(
                    latestServerModel = result.getOrNull(),
                    modelFileState = modelRepository.localFileState(),
                    networkStatus = "Latest model checked",
                )
            } else {
                _uiState.value.copy(
                    modelFileState = modelRepository.localFileState(),
                    networkStatus = result.exceptionOrNull()?.message ?: "Latest model unavailable",
                )
            }
        }
    }

    fun downloadLatestModel() {
        viewModelScope.launch {
            if (_uiState.value.offlineDetectionAllowed) {
                _uiState.value = _uiState.value.copy(networkStatus = "Model update is disabled in offline detection mode")
                return@launch
            }
            val auth = authRepository.refreshOrLogin()
            if (auth.isFailure) {
                _uiState.value = _uiState.value.copy(networkStatus = "Login failed: ${auth.exceptionOrNull()?.message}")
                return@launch
            }
            val result = modelRepository.downloadLatestPackage()
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(
                    modelMetadata = result.getOrThrow(),
                    modelFileState = modelRepository.localFileState(),
                    networkStatus = "Model downloaded",
                )
            } else {
                _uiState.value.copy(
                    modelFileState = modelRepository.localFileState(),
                    networkStatus = "Model download failed: ${result.exceptionOrNull()?.message}",
                )
            }
        }
    }

    fun setDetecting(active: Boolean) {
        _uiState.value = _uiState.value.copy(
            detecting = active,
            detectionStatus = if (active) "Detecting" else "Stopped",
            detections = if (active) _uiState.value.detections else emptyList()
        )
        if (active && _uiState.value.settings.detectionMode == DetectionMode.SERVER) {
            viewModelScope.launch {
                val auth = authRepository.refreshOrLogin()
                if (auth.isFailure) {
                    _uiState.value = _uiState.value.copy(
                        detectionStatus = "Login failed: ${auth.exceptionOrNull()?.message}",
                        networkStatus = "Login failed"
                    )
                } else {
                    _uiState.value = _uiState.value.copy(networkStatus = "Authenticated")
                }
            }
        }
        if (active && _uiState.value.settings.detectionMode == DetectionMode.ON_DEVICE) {
            val loaded = onDeviceDetector.load()
            _uiState.value = _uiState.value.copy(
                detectionStatus = onDeviceDetector.statusMessage,
                onDeviceDebug = onDeviceDetector.debugState(),
                modelFileState = modelRepository.localFileState(),
                detections = if (loaded) _uiState.value.detections else emptyList(),
            )
        }
    }

    fun toggleCameraStatusOverlay() {
        _uiState.value = _uiState.value.copy(
            cameraStatusOverlayVisible = !_uiState.value.cameraStatusOverlayVisible
        )
    }

    fun processFrame(jpegBytes: ByteArray) {
        val state = _uiState.value
        if (!state.detecting) return
        viewModelScope.launch {
            when (state.settings.detectionMode) {
                DetectionMode.SERVER -> {
                    var detections: List<DetectionBox> = emptyList()
                    var statusMessage = "Server: waiting"
                    val elapsed = measureTimeMillis {
                        val result = detectionRepository.detectServer(jpegBytes)
                        result.onSuccess {
                            detections = it.detections
                            statusMessage = "Server: ${it.message} model_available=${it.modelAvailable} log_id=${it.logId ?: "-"}"
                        }
                        result.onFailure {
                            statusMessage = it.message ?: "Server detection failed"
                        }
                    }
                    _uiState.value = _uiState.value.copy(
                        detections = detections,
                        latencyMs = elapsed,
                        fps = if (elapsed > 0) 1000f / elapsed else 0f,
                        networkStatus = if (detections.isEmpty()) _uiState.value.networkStatus else "Server mode OK",
                        detectionStatus = statusMessage
                    )
                }
                DetectionMode.ON_DEVICE -> {
                    if (onDeviceFrameInFlight) return@launch
                    onDeviceFrameInFlight = true
                    var detections: List<DetectionBox> = emptyList()
                    var statusMessage = "On-device: waiting"
                    val elapsed = try {
                        measureTimeMillis {
                            val bitmap = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)
                            if (bitmap == null) {
                                statusMessage = "On-device: bitmap decode failed"
                            } else {
                                val result = onDeviceDetector.detect(
                                    bitmap = bitmap,
                                    confidenceThreshold = state.settings.confidenceThreshold,
                                    iouThreshold = state.settings.iouThreshold,
                                )
                                result.onSuccess {
                                    detections = it
                                    statusMessage = onDeviceDetector.statusMessage
                                }
                                result.onFailure {
                                    statusMessage = it.message ?: onDeviceDetector.statusMessage
                                }
                                bitmap.recycle()
                            }
                        }
                    } catch (exc: Exception) {
                        statusMessage = "On-device error: ${exc.message}"
                        0L
                    } finally {
                        onDeviceFrameInFlight = false
                    }
                    _uiState.value = _uiState.value.copy(
                        detections = detections,
                        latencyMs = elapsed,
                        fps = if (elapsed > 0) 1000f / elapsed else 0f,
                        detectionStatus = statusMessage,
                        onDeviceDebug = onDeviceDetector.debugState(),
                        modelFileState = modelRepository.localFileState(),
                    )
                }
            }
        }
    }

    fun loadHistory() {
        viewModelScope.launch {
            val result = detectionRepository.history()
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(history = result.getOrDefault(emptyList()))
            } else {
                _uiState.value.copy(history = emptyList(), networkStatus = "Server history API is not available")
            }
        }
    }
}
