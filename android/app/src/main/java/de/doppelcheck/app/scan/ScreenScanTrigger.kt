package de.doppelcheck.app.scan

import android.content.Context
import android.widget.Toast

/** Entry point for triggers outside the accessibility service (the assistant gesture). */
object ScreenScanTrigger {

    fun request(context: Context, delayMs: Long) {
        val service = DoppelCheckAccessibilityService.instance
        if (service != null) {
            service.scanScreen(delayMs)
            return
        }
        Toast.makeText(
            context.applicationContext,
            "Bitte zuerst die Bedienungshilfe „DoppelCheck – Bildschirm prüfen“ einschalten.",
            Toast.LENGTH_LONG,
        ).show()
        SystemSettings.openAccessibility(context)
    }
}
