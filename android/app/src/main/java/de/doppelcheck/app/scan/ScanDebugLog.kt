package de.doppelcheck.app.scan

import android.util.Log
import de.doppelcheck.app.BuildConfig
import de.doppelcheck.app.api.ApiClient

/**
 * Debug builds only: writes the exact collected screen text to Logcat, one line per node,
 * so the text filter can be designed from real app trees instead of guesses.
 *
 *     adb logcat -s DoppelCheckScan
 *
 * Line format: `#<n> KEEP|DROP(<reason>) d=<depth> <className> id=<viewIdResourceName> [click] [desc] | <text>`.
 * Line breaks inside a node's text are shown as `\n` so each node stays on one Logcat line.
 * Release builds log nothing – the dump contains the user's messages.
 */
object ScanDebugLog {

    const val TAG = "DoppelCheckScan"

    /** Logcat truncates a single entry at ~4 kB; longer texts are split into numbered parts. */
    private const val CHUNK = 3000

    /**
     * [dropReasons] is parallel to [entries] (null = kept by [ChromeFilter]). With the filter off
     * the reasons are still shown as "would drop", so both A/B variants can be compared.
     * [sentText] is what is (or would be) sent. [notes]: gate etc., printed before the END marker.
     */
    fun dump(
        packageName: CharSequence?,
        entries: List<ScreenTextCollector.Entry>,
        dropReasons: List<String?>,
        filterEnabled: Boolean,
        sentText: String,
        notes: List<String> = emptyList(),
    ) {
        if (!BuildConfig.DEBUG) return
        Log.d(
            TAG,
            "===== BEGIN SCAN package=$packageName nodes=${entries.size} filter=${if (filterEnabled) "on" else "off"} " +
                "dropped=${dropReasons.count { it != null }} sentChars=${sentText.length} =====",
        )
        entries.forEachIndexed { index, entry ->
            val flags = buildString {
                if (entry.clickable) append(" [click]")
                if (entry.fromDescription) append(" [desc]")
            }
            val decision = when {
                dropReasons[index] == null -> "KEEP"
                filterEnabled -> "DROP(${dropReasons[index]})"
                else -> "KEEP(would drop: ${dropReasons[index]})"
            }
            val header = "#$index $decision d=${entry.depth} ${entry.className} id=${entry.viewId}$flags | "
            val body = entry.text.replace("\n", "\\n")
            body.chunked(CHUNK).forEachIndexed { part, chunk ->
                Log.d(TAG, if (part == 0) header + chunk else "#$index (cont. $part) | $chunk")
            }
        }
        notes.forEach { Log.d(TAG, "-- $it") }
        Log.d(TAG, "===== END SCAN =====")
    }

    /**
     * The exact text handed to POST /scan-text, logged right before the request under the API tag
     * (`adb logcat -s DoppelCheck`) so it sits next to the request line and is easy to read on its
     * own, separate from the node dump above. Line breaks are shown as `\n`.
     */
    fun dumpSentText(text: String) {
        if (!BuildConfig.DEBUG) return
        Log.i(ApiClient.LOG_TAG, "===== BEGIN TEXT SENT TO /scan-text chars=${text.length} =====")
        text.replace("\n", "\\n").chunked(CHUNK).forEachIndexed { part, chunk ->
            Log.i(ApiClient.LOG_TAG, if (part == 0) chunk else "(cont. $part) $chunk")
        }
        Log.i(ApiClient.LOG_TAG, "===== END TEXT SENT =====")
    }
}
