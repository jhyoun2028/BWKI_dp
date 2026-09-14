package de.doppelcheck.app.assist

import android.app.Activity
import android.os.Bundle
import de.doppelcheck.app.scan.ScreenScanTrigger

/**
 * Receives ACTION_ASSIST, i.e. the assistant gesture (long-press Home, swipe from a bottom
 * corner) once DoppelCheck is the default digital assistant app. It has no UI: it asks the
 * accessibility service for the same screen scan as the bubble and finishes immediately.
 *
 * Deliberately no VoiceInteractionService: that would require declaring a speech recognizer,
 * and Android makes an assistant's recognizer the system default – breaking voice input
 * elsewhere. An exported ACTION_ASSIST activity alone qualifies for the assistant role.
 */
class AssistActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // The delay lets the gesture animation end so the app underneath is the active window again.
        ScreenScanTrigger.request(this, delayMs = GESTURE_SETTLE_DELAY_MS)
        finish()
    }

    private companion object {
        const val GESTURE_SETTLE_DELAY_MS = 400L
    }
}
