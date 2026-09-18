package de.doppelcheck.app.contact

import android.content.Context
import android.content.Intent
import android.net.Uri
import de.doppelcheck.app.MainActivity
import de.doppelcheck.app.SettingsStore

/**
 * "Angehörige informieren": hands a pre-filled warning to the user's SMS app.
 *
 * ACTION_SENDTO with an sms: URI needs NO SMS permission – the message is only put into the
 * SMS app's editor, and the user has to press send themselves. DoppelCheck never sends
 * anything on its own and never reads the address book.
 */
object TrustedContact {

    /** Text of the warning; [reasonDe] is the plain-German sentence from the server. */
    fun warningText(reasonDe: String): String =
        "DoppelCheck-Warnung: Ich habe eine verdächtige Nachricht erhalten. $reasonDe"

    /**
     * Intent that opens the SMS app with recipient and text filled in, or – if no contact is
     * stored – the DoppelCheck settings, so the user can add one.
     *
     * Both "smsto:" and "sms:" address SMS apps; "smsto:" is the documented scheme for
     * ACTION_SENDTO, "sms:" is the fallback for apps that only register that one.
     */
    fun intent(context: Context, reasonDe: String): Intent {
        val settings = SettingsStore(context)
        if (!settings.hasContact) return MainActivity.settingsIntent(context)
        val body = warningText(reasonDe)
        val smsTo = sendTo("smsto", settings.contactPhone, body)
        return if (smsTo.resolveActivity(context.packageManager) != null) {
            smsTo
        } else {
            sendTo("sms", settings.contactPhone, body)
        }
    }

    private fun sendTo(scheme: String, phone: String, body: String): Intent =
        Intent(Intent.ACTION_SENDTO, Uri.fromParts(scheme, phone, null))
            // "sms_body" is what SMS apps read; EXTRA_TEXT is accepted by some of them as well.
            .putExtra("sms_body", body)
            .putExtra(Intent.EXTRA_TEXT, body)
}
