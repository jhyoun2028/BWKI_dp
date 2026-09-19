package de.doppelcheck.app.api

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Single Retrofit instance. The base URL is a placeholder only – all calls pass a full
 * URL, see [DoppelCheckApi]. Every request carries `ngrok-skip-browser-warning: true`,
 * otherwise a free ngrok tunnel answers with an HTML interstitial instead of our JSON.
 */
object ApiClient {

    private const val PLACEHOLDER_BASE = "http://localhost/"
    const val NGROK_HEADER = "ngrok-skip-browser-warning"

    private val http: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)     // OCR on CPU can take a while on first use
        .writeTimeout(60, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .header(NGROK_HEADER, "true")
                .header("Accept", "application/json")
                .build()
            chain.proceed(request)
        }
        .build()

    val api: DoppelCheckApi = Retrofit.Builder()
        .baseUrl(PLACEHOLDER_BASE)
        .client(http)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(DoppelCheckApi::class.java)
}
