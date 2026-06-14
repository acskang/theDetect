package com.thesysm.mdetect.data

import com.thesysm.mdetect.network.ApiClient
import com.thesysm.mdetect.network.LoginRequest
import com.thesysm.mdetect.network.LogoutRequest
import com.thesysm.mdetect.network.RefreshRequest
import com.thesysm.mdetect.network.SessionRefreshRequest
import com.thesysm.mdetect.network.SignupRequest

class AuthRepository(
    private val settingsRepository: SettingsRepository,
    private val apiClient: ApiClient
) {
    private fun responseError(prefix: String, code: Int, raw: String?): String {
        val detail = raw?.takeIf { it.isNotBlank() }?.take(240)
        return if (detail.isNullOrBlank()) "$prefix: HTTP $code" else "$prefix: HTTP $code $detail"
    }

    suspend fun restoreSession(): Result<String> = runCatching {
        val tokens = settingsRepository.currentTokens()
        if (!tokens.canRestoreSession) error("Login required")
        val response = apiClient.api().sessionRefresh(SessionRefreshRequest(tokens.refresh, tokens.deviceToken))
        val body = response.body()
        if (!response.isSuccessful || body == null || !body.connected || body.user == null || body.access.isNullOrBlank() || body.refresh.isNullOrBlank()) {
            settingsRepository.clearAuthSession(body?.message ?: "Session expired")
            error(body?.message ?: responseError("Session refresh failed", response.code(), response.errorBody()?.string()))
        }
        settingsRepository.saveAuthSession(
            access = body.access,
            refresh = body.refresh,
            deviceToken = tokens.deviceToken,
            userId = body.user.id,
            username = body.user.username,
            phoneNumber = body.user.phoneNumber,
            approvalStatus = body.user.approvalStatus,
            message = body.message ?: "${body.user.username}님, 반갑습니다"
        )
        body.message ?: "${body.user.username}님, 반갑습니다"
    }

    suspend fun login(username: String, password: String): Result<String> = runCatching {
        val response = apiClient.api().login(LoginRequest(username, password))
        if (!response.isSuccessful || response.body() == null) {
            error(responseError("Login failed", response.code(), response.errorBody()?.string()))
        }
        val body = response.body()!!
        settingsRepository.saveAuthSession(
            access = body.access,
            refresh = body.refresh,
            deviceToken = body.deviceToken,
            userId = body.user.id,
            username = body.user.username,
            phoneNumber = body.user.phoneNumber,
            approvalStatus = body.user.approvalStatus,
            message = body.message ?: "${body.user.username}님, 반갑습니다"
        )
        body.message ?: "${body.user.username}님, 반갑습니다"
    }

    suspend fun signup(username: String, phoneNumber: String, password: String, confirmPassword: String): Result<String> = runCatching {
        val response = apiClient.api().signup(SignupRequest(username, phoneNumber, password, confirmPassword))
        val body = response.body()
        if (!response.isSuccessful || body == null || !body.registered) {
            error(body?.message ?: responseError("Signup failed", response.code(), response.errorBody()?.string()))
        }
        body.message ?: "가입 신청이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다."
    }

    suspend fun logout(): Result<String> = runCatching {
        val tokens = settingsRepository.currentTokens()
        var message = "로그아웃되었습니다."
        if (tokens.refresh.isNotBlank() && tokens.deviceToken.isNotBlank()) {
            val serverLogout = runCatching {
                val response = apiClient.api().logout(LogoutRequest(tokens.refresh, tokens.deviceToken))
                val body = response.body()
                if (!response.isSuccessful || body == null || !body.loggedOut) {
                    error(body?.message ?: responseError("Server logout failed", response.code(), response.errorBody()?.string()))
                }
                body.message ?: "로그아웃되었습니다."
            }
            message = serverLogout.getOrElse {
                "로컬 로그아웃되었습니다. 서버 세션 해제는 실패했을 수 있습니다."
            }
        }
        settingsRepository.logout()
        message
    }

    suspend fun refreshOrLogin(): Result<Unit> {
        val refresh = settingsRepository.currentTokens().refresh
        if (refresh.isNotBlank()) {
            val refreshed = runCatching {
                val response = apiClient.api().refresh(RefreshRequest(refresh))
                if (!response.isSuccessful || response.body() == null) error("Refresh failed: HTTP ${response.code()}")
                val body = response.body()!!
                if (body.refresh.isNullOrBlank()) {
                    settingsRepository.saveAccess(body.access)
                } else {
                    settingsRepository.saveTokens(body.access, body.refresh)
                }
            }
            if (refreshed.isSuccess) return refreshed
        }
        return restoreSession().map { }
    }
}
