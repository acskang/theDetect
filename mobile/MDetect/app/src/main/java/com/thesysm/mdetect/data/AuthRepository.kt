package com.thesysm.mdetect.data

import com.thesysm.mdetect.network.ApiClient
import com.thesysm.mdetect.network.LoginRequest
import com.thesysm.mdetect.network.RefreshRequest

class AuthRepository(
    private val settingsRepository: SettingsRepository,
    private val apiClient: ApiClient
) {
    suspend fun ensureLoggedIn(): Result<Unit> {
        val tokens = settingsRepository.currentTokens()
        if (!tokens.hasAccess) return autoLogin()
        return refreshOrLogin()
    }

    suspend fun autoLogin(): Result<Unit> = runCatching {
        val settings = settingsRepository.currentSettings()
        val response = apiClient.api().login(LoginRequest(settings.username, settings.password))
        if (!response.isSuccessful || response.body() == null) {
            error("Login failed: HTTP ${response.code()}")
        }
        val body = response.body()!!
        settingsRepository.saveTokens(body.access, body.refresh.orEmpty())
    }

    suspend fun refreshOrLogin(): Result<Unit> {
        val refresh = settingsRepository.currentTokens().refresh
        if (refresh.isNotBlank()) {
            val refreshed = runCatching {
                val response = apiClient.api().refresh(RefreshRequest(refresh))
                if (!response.isSuccessful || response.body() == null) error("Refresh failed: HTTP ${response.code()}")
                settingsRepository.saveAccess(response.body()!!.access)
            }
            if (refreshed.isSuccess) return refreshed
        }
        return autoLogin()
    }
}
