package de.doppelcheck.app.api

import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Url

/**
 * The server address is configured by the user at runtime, so every call takes the
 * full URL via @Url instead of relying on Retrofit's fixed base URL.
 */
interface DoppelCheckApi {

    @GET
    suspend fun health(@Url url: String): HealthResult

    @POST
    suspend fun scanText(@Url url: String, @Body body: TextRequest): ScanResult

    @Multipart
    @POST
    suspend fun scanImage(@Url url: String, @Part file: MultipartBody.Part): ScanResult
}
