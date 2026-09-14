package de.doppelcheck.app.api

import android.util.Log
import de.doppelcheck.app.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Single Retrofit instance. The base URL is a placeholder only – all calls pass a full
 * URL, see [DoppelCheckApi]. Every request carries `ngrok-skip-browser-warning: true`,
 * otherwise a free ngrok tunnel answers with an HTML interstitial instead of our JSON.
 *
 * Logcat (filter by tag `DoppelCheck`): the resolved URL of every request is always logged;
 * full request/response logging (headers + bodies) is added in debug builds only, because
 * the bodies contain the user's messages.
 */
object ApiClient {

    private const val PLACEHOLDER_BASE = "http://localhost/"
    const val NGROK_HEADER = "ngrok-skip-browser-warning"
    const val LOG_TAG = "DoppelCheck"

    private val http: OkHttpClient = OkHttpClient.Builder()
        // A DistilBERT server loads its model on the first request (30+ s).
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)     // kept above 60 s: first OCR call on CPU can take longer
        .writeTimeout(60, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .header(NGROK_HEADER, "true")
                .header("Accept", "application/json")
                .build()
            Log.i(LOG_TAG, "→ ${request.method} ${request.url}")
            chain.proceed(request)
        }
        .apply {
            if (BuildConfig.DEBUG) {
                addInterceptor(
                    HttpLoggingInterceptor { message -> Log.d(LOG_TAG, message) }
                        .setLevel(HttpLoggingInterceptor.Level.BODY),
                )
            }
        }
        .build()

    val api: DoppelCheckApi = Retrofit.Builder()
        .baseUrl(PLACEHOLDER_BASE)
        .client(http)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(DoppelCheckApi::class.java)
}
