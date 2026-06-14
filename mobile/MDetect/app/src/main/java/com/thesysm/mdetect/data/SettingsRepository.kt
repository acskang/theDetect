package com.thesysm.mdetect.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.thesysm.mdetect.BuildConfig
import com.thesysm.mdetect.model.AppSettings
import com.thesysm.mdetect.model.AuthUserState
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
        val DEVICE_TOKEN = stringPreferencesKey("device_token")
        val USER_ID = longPreferencesKey("user_id")
        val AUTH_USERNAME = stringPreferencesKey("auth_username")
        val PHONE_NUMBER = stringPreferencesKey("phone_number")
        val APPROVAL_STATUS = stringPreferencesKey("approval_status")
        val CONNECTED = stringPreferencesKey("connected_status")
        val AUTH_MESSAGE = stringPreferencesKey("auth_message")
    }

    val settingsFlow: Flow<AppSettings> = context.dataStore.data.map { prefs ->
        AppSettings(
            serverUrl = prefs[Keys.SERVER_URL] ?: BuildConfig.DEFAULT_SERVER_URL,
            detectionMode = runCatching { DetectionMode.valueOf(prefs[Keys.DETECTION_MODE] ?: DetectionMode.SERVER.name) }.getOrDefault(DetectionMode.SERVER),
            frameIntervalMs = prefs[Keys.FRAME_INTERVAL] ?: 1000L,
            confidenceThreshold = prefs[Keys.CONFIDENCE] ?: 0.5f,
            iouThreshold = prefs[Keys.IOU] ?: 0.45f,
            username = prefs[Keys.USERNAME] ?: BuildConfig.DEFAULT_USERNAME,
            password = ""
        )
    }

    val tokenFlow: Flow<TokenState> = context.dataStore.data.map { prefs ->
        TokenState(
            access = prefs[Keys.ACCESS] ?: "",
            refresh = prefs[Keys.REFRESH] ?: "",
            deviceToken = prefs[Keys.DEVICE_TOKEN] ?: ""
        )
    }

    val authUserFlow: Flow<AuthUserState> = context.dataStore.data.map { prefs ->
        AuthUserState(
            id = prefs[Keys.USER_ID] ?: 0L,
            username = prefs[Keys.AUTH_USERNAME] ?: "",
            phoneNumber = prefs[Keys.PHONE_NUMBER] ?: "",
            approvalStatus = prefs[Keys.APPROVAL_STATUS] ?: "",
            connected = prefs[Keys.CONNECTED] == "connected",
            message = prefs[Keys.AUTH_MESSAGE] ?: ""
        )
    }

    suspend fun currentSettings(): AppSettings = settingsFlow.first()
    suspend fun currentTokens(): TokenState = tokenFlow.first()
    suspend fun currentAuthUser(): AuthUserState = authUserFlow.first()

    suspend fun saveSettings(settings: AppSettings) {
        context.dataStore.edit { prefs ->
            prefs[Keys.SERVER_URL] = settings.serverUrl.trimEnd('/')
            prefs[Keys.DETECTION_MODE] = settings.detectionMode.name
            prefs[Keys.FRAME_INTERVAL] = settings.frameIntervalMs
            prefs[Keys.CONFIDENCE] = settings.confidenceThreshold
            prefs[Keys.IOU] = settings.iouThreshold
        }
    }

    suspend fun saveTokens(access: String, refresh: String) {
        context.dataStore.edit { prefs ->
            prefs[Keys.ACCESS] = access
            prefs[Keys.REFRESH] = refresh
        }
    }

    suspend fun saveAuthSession(
        access: String,
        refresh: String,
        deviceToken: String?,
        userId: Long,
        username: String,
        phoneNumber: String,
        approvalStatus: String,
        message: String
    ) {
        context.dataStore.edit { prefs ->
            prefs[Keys.ACCESS] = access
            prefs[Keys.REFRESH] = refresh
            if (!deviceToken.isNullOrBlank()) prefs[Keys.DEVICE_TOKEN] = deviceToken
            prefs[Keys.USER_ID] = userId
            prefs[Keys.AUTH_USERNAME] = username
            prefs[Keys.PHONE_NUMBER] = phoneNumber
            prefs[Keys.APPROVAL_STATUS] = approvalStatus
            prefs[Keys.CONNECTED] = "connected"
            prefs[Keys.AUTH_MESSAGE] = message
        }
    }

    suspend fun saveAccess(access: String) {
        context.dataStore.edit { prefs -> prefs[Keys.ACCESS] = access }
    }

    suspend fun clearAuthSession(message: String = "Login required") {
        context.dataStore.edit { prefs ->
            prefs.remove(Keys.ACCESS)
            prefs.remove(Keys.REFRESH)
            prefs.remove(Keys.DEVICE_TOKEN)
            prefs.remove(Keys.USER_ID)
            prefs.remove(Keys.AUTH_USERNAME)
            prefs.remove(Keys.PHONE_NUMBER)
            prefs.remove(Keys.APPROVAL_STATUS)
            prefs.remove(Keys.CONNECTED)
            prefs.remove(Keys.AUTH_MESSAGE)
            prefs.remove(Keys.USERNAME)
            prefs.remove(Keys.PASSWORD)
            if (message.isNotBlank()) prefs[Keys.AUTH_MESSAGE] = message
        }
    }

    suspend fun logout() {
        clearAuthSession("")
    }
}
