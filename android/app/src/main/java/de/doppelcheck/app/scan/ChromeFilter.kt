package de.doppelcheck.app.scan

/**
 * Drops UI chrome (buttons, toolbars, timestamps, input field …) from the collected screen text so
 * that only message text reaches the classifier. Rules come from real WhatsApp dumps
 * (`adb logcat -s DoppelCheckScan`), where the message itself sits in `id/top_message`,
 * `id/bottom_message`, `id/message_text` or `id/conversation_row_text`.
 *
 * Generic rules first (class, clickable description, id suffix) so it also works in other
 * messengers; the WhatsApp id list is an extra deny layer on top.
 */
object ChromeFilter {

    /** WhatsApp chrome seen in the dumps that the generic rules do not all catch. */
    private val WHATSAPP_CHROME_IDS = setOf(
        "whatsapp_toolbar_home", "conversation_contact_name", "conversation_contact_status",
        "conversation_row_date_divider", "info", "contact_photo", "signals", "add_btn_fmx",
        "action_button", "emoji_picker_btn", "entry", "input_attach_button", "camera_btn",
        "voice_note_btn", "date", "menuitem_overflow",
    )

    /** Id endings that mark controls, bars, avatars, dividers, timestamps and input fields. */
    private val CHROME_ID_SUFFIXES = listOf(
        "_btn", "_button", "toolbar", "_icon", "photo", "divider", "date", "entry", "overflow",
    )

    /** Why [entry] is chrome, or null if it is kept. The reason is shown in the debug dump. */
    fun dropReason(entry: ScreenTextCollector.Entry): String? {
        if (MessageGate.isControlClass(entry.className)) return "control-class"
        // Clickable content descriptions are accessibility hints of controls,
        // e.g. "Sprachnachricht, Schaltfläche. Doppeltippen und halten …" or "Weitere Optionen".
        if (entry.fromDescription && entry.clickable) return "clickable-description"
        val id = idName(entry.viewId) ?: return null
        if (id in WHATSAPP_CHROME_IDS) return "whatsapp-id"
        CHROME_ID_SUFFIXES.firstOrNull { id.endsWith(it) }?.let { return "id-suffix:$it" }
        return null
    }

    /** "com.whatsapp:id/message_text" -> "message_text"; null if the node has no id. */
    private fun idName(viewId: String?): String? =
        viewId?.substringAfterLast('/')?.lowercase()?.takeIf { it.isNotEmpty() }
}
