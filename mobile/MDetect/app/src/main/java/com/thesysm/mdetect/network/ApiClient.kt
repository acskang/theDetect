package com.thesysm.mdetect.network

import com.thesysm.mdetect.data.SettingsRepository
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class ApiClient(private val settingsRepository: SettingsRepository) {
    @Volatile private var baseUrl: String = ""
    @Volatile private var retrofit: Retrofit? = null

    suspend fun api(): MDetectApi {
        val settings = settingsRepository.currentSettings()
        val normalized = normalizeBaseUrl(settings.serverUrl)
        if (retrofit == null || normalized != baseUrl) {
            baseUrl = normalized
            retrofit = createRetrofit(normalized)
        }
        return retrofit!!.create(MDetectApi::class.java)
    }

    private fun createRetrofit(url: String): Retrofit {
        val authInterceptor = Interceptor { chain ->
            val token = runBlocking { settingsRepository.currentTokens().access }
            val request = if (token.isNotBlank()) {
                chain.request().newBuilder().header("Authorization", "Bearer $token").build()
            } else {
                chain.request()
            }
            chain.proceed(request)
        }
        val logging = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build()
        return Retrofit.Builder()
            .baseUrl(url)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    private fun normalizeBaseUrl(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }
}
