package de.doppelcheck.app.api

import com.google.gson.Gson
import retrofit2.HttpException
import java.io.IOException

/** German, user-facing description of a failed API call (status code and server detail included). */
fun describeError(e: Exception): String = when (e) {
    is HttpException -> {
        // The error body can be read only once, so keep it for both parsing and display.
        val raw = runCatching { e.response()?.errorBody()?.string() }.getOrNull().orEmpty()
        val detail = runCatching { Gson().fromJson(raw, ErrorBody::class.java)?.detail }.getOrNull()
        buildString {
            append("Der Server antwortete mit Fehler ${e.code()}.")
            when {
                detail != null -> append(" ").append(detail)
                raw.isNotBlank() -> append(" Antwort: ").append(raw.trim().take(200))
            }
        }
    }
    is IOException -> "Server nicht erreichbar. Läuft er, und stimmt die Adresse?"
    else -> e.message ?: "Unbekannter Fehler."
}
