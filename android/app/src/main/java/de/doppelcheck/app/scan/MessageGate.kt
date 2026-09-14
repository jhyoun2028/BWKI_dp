package de.doppelcheck.app.scan

/**
 * "Is this even a message?" – checked on the collected screen text BEFORE anything is sent.
 *
 * The classifier was only trained on messages. Launcher labels, page indicators and widget text
 * ("Instagram, 148 Benachrichtigungen", "Seite 1 von 4, Schaltfläche") are not messages and
 * produced red verdicts, so such screens are never sent to the server.
 *
 * Passes if at least one holds:
 *  - one text block of >= [MIN_BLOCK] characters from a node that is not clickable and not a
 *    control ([isControlClass]),
 *  - a URL, or
 *  - a phone number,
 * where URL and phone number only count in text that does not come from a control.
 */
object MessageGate {

    const val MIN_BLOCK = 25

    /** Result plus the rule that decided it, for the debug dump. */
    data class Result(val passed: Boolean, val rule: String)

    /** Controls and pictures, never message text: their labels are UI chrome. */
    private val CONTROL_CLASSES = setOf("Button", "ImageButton", "ImageView", "EditText")

    // Scheme / hxxp / www, or a bare domain whose top-level domain is written in lower case
    // ("dhl-paket.top/x", "dhl[.]de"). Lower case only, so "Hallo.Wie" does not count.
    private val URL = Regex(
        "(?:(?i:https?|hxxps?)://|(?i:www)\\.)\\S+" +
            "|(?<![\\p{L}\\p{N}@.-])(?:[A-Za-z0-9-]+(?:\\.|\\[\\.]))+[a-z]{2,24}(?![\\p{L}\\p{N}])",
    )

    // Starts with + or 0, then 7–15 digits with optional single space, slash or dash between them:
    // "+49 151 2345678", "0151/2345678", "010-1234-5678". Times, dates and counters do not match.
    private val PHONE = Regex("(?<![\\p{L}\\p{N}+])(?:\\+|0)\\d(?:[ /-]?\\d){6,14}(?!\\d)")

    /** True for Button, ImageButton, ImageView, EditText (any package prefix). */
    fun isControlClass(className: String?): Boolean =
        className != null && className.substringAfterLast('.') in CONTROL_CLASSES

    fun hasUrl(text: String): Boolean = URL.containsMatchIn(text)

    fun hasPhoneNumber(text: String): Boolean = PHONE.containsMatchIn(text)

    fun check(entries: List<ScreenTextCollector.Entry>): Result {
        val content = entries.filterNot { isControlClass(it.className) }
        return when {
            content.any { !it.clickable && it.text.length >= MIN_BLOCK } -> Result(true, "block>=$MIN_BLOCK")
            content.any { hasUrl(it.text) } -> Result(true, "url")
            content.any { hasPhoneNumber(it.text) } -> Result(true, "phone")
            else -> Result(false, "no block>=$MIN_BLOCK, no url, no phone")
        }
    }
}
