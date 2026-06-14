package com.thesysm.mdetect.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.thesysm.mdetect.BuildConfig
import com.thesysm.mdetect.model.AppSettings
import com.thesysm.mdetect.model.DetectionMode
import com.thesysm.mdetect.model.TokenState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "mdetect_settings")

class SettingsRepository(private val context: Context) {
    private object Keys {
        val SERVER_URL = stringPreferencesKey("server_url")
        val DETECTION_MODE = stringPreferencesKey("detection_mode")
        val FRAME_INTERVAL = longPreferencesKey("frame_interval")
        val CONFIDENCE = floatPreferencesKey("confidence_threshold")
        val IOU = floatPreferencesKey("iou_threshold")
        val USERNAME = stringPreferencesKey("username")
        val PASSWORD = stringPreferencesKey("password")
        val ACCESS = stringPreferencesKey("access_token")
        val REFRESH = stringPreferencesKey("refresh_token")
    }

    val settingsFlow: Flow<AppSettings> = context.dataStore.data.map { prefs ->
        AppSettings(
            serverUrl = prefs[Keys.SERVER_URL] ?: BuildConfig.DEFAULT_SERVER_URL,
            detectionMode = runCatching { DetectionMode.valueOf(prefs[Keys.DETECTION_MODE] ?: DetectionMode.SERVER.name) }.getOrDefault(DetectionMode.SERVER),
            frameIntervalMs = prefs[Keys.FRAME_INTERVAL] ?: 1000L,
            confidenceThreshold = prefs[Keys.CONFIDENCE] ?: 0.5f,
            iouThreshold = prefs[Keys.IOU] ?: 0.45f,
            username = prefs[Keys.USERNAME] ?: BuildConfig.DEFAULT_USERNAME,
            password = prefs[Keys.PASSWORD] ?: BuildConfig.DEFAULT_PASSWORD
        )
    }

    val tokenFlow: Flow<TokenState> = context.dataStore.data.map { prefs ->
        TokenState(
            access = prefs[Keys.ACCESS] ?: "",
            refresh = prefs[Keys.REFRESH] ?: ""
        )
    }

    suspend fun currentSettings(): AppSettings = settingsFlow.first()
    suspend fun currentTokens(): TokenState = tokenFlow.first()

    suspend fun saveSettings(settings: AppSettings) {
        context.dataStore.edit { prefs ->
            prefs[Keys.SERVER_URL] = settings.serverUrl.trimEnd('/')
            prefs[Keys.DETECTION_MODE] = settings.detectionMode.name
            prefs[Keys.FRAME_INTERVAL] = settings.frameIntervalMs
            prefs[Keys.CONFIDENCE] = settings.confidenceThreshold
            prefs[Keys.IOU] = settings.iouThreshold
            prefs[Keys.USERNAME] = settings.username
            prefs[Keys.PASSWORD] = settings.password
        }
    }

    suspend fun saveTokens(access: String, refresh: String) {
        context.dataStore.edit { prefs ->
            prefs[Keys.ACCESS] = access
            prefs[Keys.REFRESH] = refresh
        }
    }

    suspend fun saveAccess(access: String) {
        context.dataStore.edit { prefs -> prefs[Keys.ACCESS] = access }
    }
}
