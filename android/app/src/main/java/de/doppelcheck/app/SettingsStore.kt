package de.doppelcheck.app

import android.content.Context
import androidx.core.content.edit

/** Stores the API base URL in SharedPreferences. Empty by default – the user must set it. */
class SettingsStore(context: Context) {

    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    var baseUrl: String
        get() = prefs.getString(KEY_BASE_URL, "").orEmpty()
        set(value) = prefs.edit { putString(KEY_BASE_URL, normalize(value)) }

    val isConfigured: Boolean get() = baseUrl.isNotBlank()

    /** Whether the floating scan button is shown (needs the overlay permission as well). */
    var bubbleEnabled: Boolean
        get() = prefs.getBoolean(KEY_BUBBLE, true)
        set(value) = prefs.edit { putBoolean(KEY_BUBBLE, value) }

    /** Whether screen scans drop UI chrome before sending ([de.doppelcheck.app.scan.ChromeFilter]); A/B switch. */
    var chromeFilterEnabled: Boolean
        get() = prefs.getBoolean(KEY_CHROME_FILTER, true)
        set(value) = prefs.edit { putBoolean(KEY_CHROME_FILTER, value) }

    /** Optional relative/friend who can be warned about a red verdict; empty = feature off. */
    var contactName: String
        get() = prefs.getString(KEY_CONTACT_NAME, "").orEmpty()
        set(value) = prefs.edit { putString(KEY_CONTACT_NAME, value.trim()) }

    var contactPhone: String
        get() = prefs.getString(KEY_CONTACT_PHONE, "").orEmpty()
        set(value) = prefs.edit { putString(KEY_CONTACT_PHONE, normalizePhone(value)) }

    /** Only the number is required – without it there is nobody to write to. */
    val hasContact: Boolean get() = contactPhone.isNotBlank()

    /** Whether the verdict is read out loud when a result appears. Off by default. */
    var speakResult: Boolean
        get() = prefs.getBoolean(KEY_SPEAK_RESULT, false)
        set(value) = prefs.edit { putBoolean(KEY_SPEAK_RESULT, value) }

    /** Full URL of an endpoint, e.g. endpoint("/scan") -> "https://abc.ngrok-free.app/scan". */
    fun endpoint(path: String): String = baseUrl.trimEnd('/') + path

    companion object {
        private const val PREFS = "doppelcheck"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_BUBBLE = "bubble_enabled"
        private const val KEY_CHROME_FILTER = "chrome_filter_enabled"
        private const val KEY_CONTACT_NAME = "contact_name"
        private const val KEY_CONTACT_PHONE = "contact_phone"
        private const val KEY_SPEAK_RESULT = "speak_result"

        /** Trim, drop a trailing slash and add https:// when the user typed only a host. */
        fun normalize(raw: String): String {
            val t = raw.trim().trimEnd('/')
            if (t.isEmpty()) return ""
            return if (t.startsWith("http://") || t.startsWith("https://")) t else "https://$t"
        }

        /**
         * Keep digits and a leading "+", drop what people type for readability
         * (spaces, "/", "-", "(", ")"), so the number fits into an sms: URI.
         */
        fun normalizePhone(raw: String): String {
            val t = raw.trim()
            val plus = if (t.startsWith("+")) "+" else ""
            return plus + t.filter { it.isDigit() }
        }
    }
}
