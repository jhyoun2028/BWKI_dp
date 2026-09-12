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

    /** Full URL of an endpoint, e.g. endpoint("/scan") -> "https://abc.ngrok-free.app/scan". */
    fun endpoint(path: String): String = baseUrl.trimEnd('/') + path

    companion object {
        private const val PREFS = "doppelcheck"
        private const val KEY_BASE_URL = "base_url"

        /** Trim, drop a trailing slash and add https:// when the user typed only a host. */
        fun normalize(raw: String): String {
            val t = raw.trim().trimEnd('/')
            if (t.isEmpty()) return ""
            return if (t.startsWith("http://") || t.startsWith("https://")) t else "https://$t"
        }
    }
}
