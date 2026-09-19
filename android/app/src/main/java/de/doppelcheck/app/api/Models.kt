package de.doppelcheck.app.api

import com.google.gson.annotations.SerializedName

/** One link found in the message, as rated by the server's rule-based URL check. */
data class UrlFinding(
    val url: String = "",
    val level: String = "green",          // "red" | "yellow" | "green"
    val reasons: List<String> = emptyList(),
    val trusted: Boolean = false,
)

/** Response of POST /scan-text and POST /scan. `text` is only set by /scan (OCR result). */
data class ScanResult(
    val verdict: String = "green",        // "red" | "yellow" | "green"
    val score: Double = 0.0,
    @SerializedName("reason_de") val reasonDe: String = "",
    val urls: List<UrlFinding> = emptyList(),
    val model: String = "",
    val text: String? = null,
)

/** Response of GET /health. */
data class HealthResult(
    val status: String = "",
    val model: String = "",
    val ocr: Boolean = false,
)

/** Request body of POST /scan-text. */
data class TextRequest(val text: String)

/** FastAPI reports errors as {"detail": "..."}. */
data class ErrorBody(val detail: String? = null)
