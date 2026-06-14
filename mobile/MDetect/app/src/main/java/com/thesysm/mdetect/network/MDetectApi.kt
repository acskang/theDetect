package com.thesysm.mdetect.network

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Streaming
import retrofit2.http.Url

interface MDetectApi {
    @GET("api/health/")
    suspend fun health(): Response<HealthResponse>

    @POST("api/auth/login/")
    suspend fun login(@Body body: LoginRequest): Response<TokenResponse>

    @POST("api/auth/refresh/")
    suspend fun refresh(@Body body: RefreshRequest): Response<TokenResponse>

    @GET("api/models/android/latest/")
    suspend fun latestModel(): Response<LatestModelResponse>

    @Streaming
    @GET
    suspend fun downloadFile(@Url url: String): Response<ResponseBody>

    @Multipart
    @POST("api/detect/server/")
    suspend fun detectServer(
        @Part image: MultipartBody.Part,
        @Part("device_info") deviceInfo: RequestBody,
        @Part("app_version") appVersion: RequestBody
    ): Response<ServerDetectResponse>

    @GET("api/detection-logs/?limit=20")
    suspend fun detectionHistory(): Response<DetectionHistoryResponse>
}
