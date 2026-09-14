package de.doppelcheck.app.scan

import android.util.Log
import de.doppelcheck.app.BuildConfig

/**
 * Debug builds only: writes the exact collected screen text to Logcat, one line per node,
 * so the text filter can be designed from real app trees instead of guesses.
 *
 *     adb logcat -s DoppelCheckScan
 *
 * Line format: `#<n> d=<depth> <className> id=<viewIdResourceName> [click] [desc] | <text>`.
 * Line breaks inside a node's text are shown as `\n` so each node stays on one Logcat line.
 * Release builds log nothing – the dump contains the user's messages.
 */
object ScanDebugLog {

    const val TAG = "DoppelCheckScan"

    /** Logcat truncates a single entry at ~4 kB; longer texts are split into numbered parts. */
    private const val CHUNK = 3000

    fun dump(packageName: CharSequence?, entries: List<ScreenTextCollector.Entry>, sentText: String) {
        if (!BuildConfig.DEBUG) return
        Log.d(TAG, "===== BEGIN SCAN package=$packageName nodes=${entries.size} chars=${sentText.length} =====")
        entries.forEachIndexed { index, entry ->
            val flags = buildString {
                if (entry.clickable) append(" [click]")
                if (entry.fromDescription) append(" [desc]")
            }
            val header = "#$index d=${entry.depth} ${entry.className} id=${entry.viewId}$flags | "
            val body = entry.text.replace("\n", "\\n")
            body.chunked(CHUNK).forEachIndexed { part, chunk ->
                Log.d(TAG, if (part == 0) header + chunk else "#$index (cont. $part) | $chunk")
            }
        }
        Log.d(TAG, "===== END SCAN =====")
    }
}
