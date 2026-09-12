package de.doppelcheck.app

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import de.doppelcheck.app.api.ApiClient
import de.doppelcheck.app.api.ErrorBody
import de.doppelcheck.app.api.HealthResult
import de.doppelcheck.app.api.ScanResult
import de.doppelcheck.app.api.TextRequest
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.HttpException
import java.io.IOException

sealed interface ScanState {
    data object Idle : ScanState
    data object Loading : ScanState
    data class Success(val result: ScanResult) : ScanState
    data class Failure(val message: String) : ScanState
}

class ScanViewModel(app: Application) : AndroidViewModel(app) {

    private val settings = SettingsStore(app)

    private val _state = MutableStateFlow<ScanState>(ScanState.Idle)
    val state: StateFlow<ScanState> = _state.asStateFlow()

    private val _input = MutableStateFlow("")
    val input: StateFlow<String> = _input.asStateFlow()

    private val _baseUrl = MutableStateFlow(settings.baseUrl)
    val baseUrl: StateFlow<String> = _baseUrl.asStateFlow()

    fun onInputChange(value: String) {
        _input.value = value
    }

    fun saveBaseUrl(value: String) {
        settings.baseUrl = value
        _baseUrl.value = settings.baseUrl
    }

    fun reset() {
        _state.value = ScanState.Idle
    }

    /** Scan typed or shared text. */
    fun scanText(text: String) {
        _input.value = text
        val trimmed = text.trim()
        if (trimmed.isEmpty()) {
            _state.value = ScanState.Failure("Bitte zuerst eine Nachricht einfügen.")
            return
        }
        launchScan { ApiClient.api.scanText(settings.endpoint("/scan-text"), TextRequest(trimmed)) }
    }

    /** Scan a shared screenshot: the server runs OCR and returns the recognised text too. */
    fun scanImage(uri: Uri) {
        launchScan {
            val resolver = getApplication<Application>().contentResolver
            val bytes = withContext(Dispatchers.IO) {
                resolver.openInputStream(uri)?.use { it.readBytes() }
            } ?: throw IOException("Das Bild konnte nicht gelesen werden.")
            val mime = resolver.getType(uri) ?: "image/png"
            val part = MultipartBody.Part.createFormData(
                "file", "screenshot", bytes.toRequestBody(mime.toMediaTypeOrNull()),
            )
            ApiClient.api.scanImage(settings.endpoint("/scan"), part)
        }
    }

    /** Settings screen: check that the configured address answers. */
    fun checkConnection(onResult: (String) -> Unit) {
        if (!settings.isConfigured) {
            onResult("Bitte zuerst eine Serveradresse eintragen.")
            return
        }
        viewModelScope.launch {
            onResult(
                try {
                    val h: HealthResult = ApiClient.api.health(settings.endpoint("/health"))
                    "Verbindung steht. Modell: ${h.model}, Texterkennung: ${if (h.ocr) "bereit" else "nicht verfügbar"}."
                } catch (e: Exception) {
                    "Keine Verbindung: ${describe(e)}"
                },
            )
        }
    }

    private fun launchScan(onCall: suspend () -> ScanResult) {
        if (!settings.isConfigured) {
            _state.value = ScanState.Failure(
                "Noch keine Serveradresse eingetragen. Bitte oben rechts in den Einstellungen nachholen.",
            )
            return
        }
        _state.value = ScanState.Loading
        viewModelScope.launch {
            _state.value = try {
                ScanState.Success(onCall())
            } catch (e: Exception) {
                ScanState.Failure(describe(e))
            }
        }
    }

    private fun describe(e: Exception): String = when (e) {
        is HttpException -> {
            val detail = runCatching {
                Gson().fromJson(e.response()?.errorBody()?.string(), ErrorBody::class.java)?.detail
            }.getOrNull()
            detail ?: "Der Server antwortete mit Fehler ${e.code()}."
        }
        is IOException -> "Server nicht erreichbar. Läuft er, und stimmt die Adresse?"
        else -> e.message ?: "Unbekannter Fehler."
    }
}
