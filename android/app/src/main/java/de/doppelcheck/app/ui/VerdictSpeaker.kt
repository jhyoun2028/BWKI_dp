package de.doppelcheck.app.ui

import android.content.Context
import android.speech.tts.TextToSpeech
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import de.doppelcheck.app.ScanState
import de.doppelcheck.app.api.ScanResult
import java.util.Locale

/**
 * Reads the verdict out loud ("Gefahr. <reason_de>") for users who find the screen hard to read.
 *
 * The engine is built on the first sentence only, so nothing is started while the setting is
 * off. Every failure – no engine, no German voice – is silent: the panel stays readable, and
 * an old person should never be confronted with a technical error message.
 */
class VerdictSpeaker(context: Context) {

    private val appContext = context.applicationContext
    private var tts: TextToSpeech? = null
    private var ready = false
    private var failed = false
    private var pending: String? = null

    fun speak(text: String) {
        if (failed) return
        val engine = tts
        if (engine == null) {
            // First sentence: build the engine and say it as soon as onInit reports success.
            pending = text
            tts = TextToSpeech(appContext, ::onInit)
            return
        }
        if (ready) engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, UTTERANCE_ID) else pending = text
    }

    /** Stops an ongoing sentence and frees the engine; safe to call more than once. */
    fun release() {
        pending = null
        ready = false
        tts?.let {
            it.stop()
            it.shutdown()
        }
        tts = null
    }

    /** Runs on the main thread after [speak] has stored the engine in [tts]. */
    private fun onInit(status: Int) {
        val engine = tts
        if (status != TextToSpeech.SUCCESS || engine == null || engine.setLanguage(Locale.GERMAN) in NO_LANGUAGE) {
            failed = true          // no engine or no German voice: stay silent, never show an error
            pending = null
            return
        }
        ready = true
        pending?.let { engine.speak(it, TextToSpeech.QUEUE_FLUSH, null, UTTERANCE_ID) }
        pending = null
    }

    private companion object {
        const val UTTERANCE_ID = "verdict"
        val NO_LANGUAGE = setOf(TextToSpeech.LANG_MISSING_DATA, TextToSpeech.LANG_NOT_SUPPORTED)
    }
}

/** Spoken form of a result: the traffic-light word, then the plain-German sentence. */
fun spokenVerdict(result: ScanResult): String = "${verdictWord(result.verdict)}. ${result.reasonDe}"

/**
 * Speaks the verdict once when a result appears, if [enabled]. The engine belongs to the
 * composition: it is released as soon as the result screen closes.
 */
@Composable
fun SpeakVerdict(state: ScanState, enabled: Boolean) {
    val context = LocalContext.current
    val speaker = remember { VerdictSpeaker(context) }
    DisposableEffect(speaker) {
        onDispose { speaker.release() }
    }
    LaunchedEffect(state, enabled) {
        if (enabled && state is ScanState.Success) speaker.speak(spokenVerdict(state.result))
    }
}
