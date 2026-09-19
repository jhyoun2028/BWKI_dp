package de.doppelcheck.app.scan

/**
 * Drops UI chrome (buttons, toolbars, timestamps, input field …) from the collected screen text so
 * that only message text reaches the classifier. Rules come from real WhatsApp dumps
 * (`adb logcat -s DoppelCheckScan`), where the message itself sits in `id/top_message`,
 * `id/bottom_message`, `id/message_text` or `id/conversation_row_text`.
 *
 * Two stages, see [dropReasons]:
 *  1. chrome rules – generic first (class, clickable description, id suffix) so they also work in
 *     other messengers, then the WhatsApp id list as an extra deny layer,
 *  2. message blocks – of what survives, only the single longest non-clickable block and every
 *     block over [LONG_BLOCK_CHARS] characters are sent. Short leftovers (contact names,
 *     "online", "14:32", one-word labels) never reach the classifier, in any app.
 */
object ChromeFilter {

    /** A block this long is message text in any app; shorter leftovers are labels. */
    const val LONG_BLOCK_CHARS = 40

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

    /**
     * Why each entry is dropped, parallel to [entries]; null = sent to the classifier.
     * Stage 1 is [dropReason], stage 2 keeps only the message blocks ([messageBlocks]).
     */
    fun dropReasons(entries: List<ScreenTextCollector.Entry>): List<String?> {
        val chrome = entries.map(::dropReason)
        val survivors = entries.filterIndexed { i, _ -> chrome[i] == null }
        val blocks = messageBlocks(survivors).toSet()
        return entries.mapIndexed { i, entry ->
            chrome[i] ?: if (entry in blocks) null else "not-message-block"
        }
    }

    /**
     * The blocks that actually look like a message: the single longest non-clickable block plus
     * every block over [LONG_BLOCK_CHARS] characters, in on-screen order. Everything else is
     * dropped – a chat screen has one or two real messages and a dozen short labels.
     */
    fun messageBlocks(entries: List<ScreenTextCollector.Entry>): List<ScreenTextCollector.Entry> {
        val longest = entries.filterNot { it.clickable }.maxByOrNull { it.text.length }
        return entries.filter { it.text.length > LONG_BLOCK_CHARS || it == longest }
    }

    /** Why [entry] is chrome, or null if it survives stage 1. The reason is shown in the debug dump. */
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
