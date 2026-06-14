package com.thesysm.mdetect

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.thesysm.mdetect.data.AuthRepository
import com.thesysm.mdetect.data.DetectionRepository
import com.thesysm.mdetect.data.ModelRepository
import com.thesysm.mdetect.data.SettingsRepository
import com.thesysm.mdetect.inference.OnDeviceDetector
import com.thesysm.mdetect.model.AppSettings
import com.thesysm.mdetect.model.DetectionBox
import com.thesysm.mdetect.model.DetectionMode
import com.thesysm.mdetect.model.ModelMetadata
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
    val latestServerModel: ModelMetadata? = null
)

enum class AppScreen {
    SPLASH,
    LANDING,
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

    private val _uiState = MutableStateFlow(AppUiState())
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            settingsRepository.settingsFlow.collectLatest { settings ->
                _uiState.value = _uiState.value.copy(settings = settings)
            }
        }
        bootstrap()
    }

    fun bootstrap() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, detectionStatus = "Starting")
            val login = authRepository.ensureLoggedIn()
            val health = runCatching { apiClient.api().health() }
            _uiState.value = _uiState.value.copy(
                loading = false,
                screen = AppScreen.LANDING,
                modelMetadata = modelRepository.currentMetadata(),
                serverStatus = if (health.getOrNull()?.isSuccessful == true) "Connected" else "Unavailable",
                networkStatus = if (login.isSuccess) "Authenticated" else "Login failed: ${login.exceptionOrNull()?.message}",
                detectionStatus = "Ready"
            )
        }
    }

    fun navigate(screen: AppScreen) {
        _uiState.value = _uiState.value.copy(screen = screen)
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

    fun autoLogin() {
        viewModelScope.launch {
            val result = authRepository.autoLogin()
            _uiState.value = _uiState.value.copy(networkStatus = if (result.isSuccess) "Authenticated" else "Login failed: ${result.exceptionOrNull()?.message}")
        }
    }

    fun checkLatestModel() {
        viewModelScope.launch {
            val auth = authRepository.refreshOrLogin()
            if (auth.isFailure) {
                _uiState.value = _uiState.value.copy(networkStatus = "Login failed: ${auth.exceptionOrNull()?.message}")
                return@launch
            }
            val result = modelRepository.checkLatestVersion()
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(latestServerModel = result.getOrNull(), networkStatus = "Latest model checked")
            } else {
                _uiState.value.copy(networkStatus = result.exceptionOrNull()?.message ?: "Latest model unavailable")
            }
        }
    }

    fun downloadLatestModel() {
        viewModelScope.launch {
            val auth = authRepository.refreshOrLogin()
            if (auth.isFailure) {
                _uiState.value = _uiState.value.copy(networkStatus = "Login failed: ${auth.exceptionOrNull()?.message}")
                return@launch
            }
            val result = modelRepository.downloadLatestPackage()
            _uiState.value = if (result.isSuccess) {
                _uiState.value.copy(modelMetadata = result.getOrThrow(), networkStatus = "Model downloaded")
            } else {
                _uiState.value.copy(networkStatus = "Model download failed: ${result.exceptionOrNull()?.message}")
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
            onDeviceDetector.load()
        }
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
                    _uiState.value = _uiState.value.copy(detectionStatus = onDeviceDetector.statusMessage)
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
