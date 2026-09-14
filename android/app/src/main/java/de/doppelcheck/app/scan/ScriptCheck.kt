package de.doppelcheck.app.scan

import java.lang.Character.UnicodeScript

/**
 * The classifier knows only German and English. Text in another writing system would still get
 * a score – a meaningless one – so it is not sent. A script count is enough for that: it does
 * not tell German from English, it only spots text that is clearly neither.
 */
object ScriptCheck {

    /** More than this share of letters in an unsupported script → not checked. */
    private const val MAX_UNSUPPORTED_SHARE = 0.20

    /** Hangul, CJK (Han, Hiragana, Katakana) and Cyrillic. */
    private val UNSUPPORTED = setOf(
        UnicodeScript.HANGUL, UnicodeScript.HAN, UnicodeScript.HIRAGANA, UnicodeScript.KATAKANA,
        UnicodeScript.CYRILLIC,
    )

    data class Result(
        val supported: Boolean,
        /** Script with the most letters, e.g. LATIN or HANGUL; null if there are no letters. */
        val dominant: UnicodeScript?,
        val unsupportedShare: Double,
        val letters: Int,
    )

    fun check(text: String): Result {
        val counts = HashMap<UnicodeScript, Int>()
        text.codePoints().filter(Character::isLetter).forEach { cp ->
            counts.merge(UnicodeScript.of(cp), 1, Int::plus)
        }
        val letters = counts.values.sum()
        val unsupported = counts.filterKeys { it in UNSUPPORTED }.values.sum()
        val share = if (letters == 0) 0.0 else unsupported.toDouble() / letters
        return Result(
            supported = share <= MAX_UNSUPPORTED_SHARE,
            dominant = counts.maxByOrNull { it.value }?.key,
            unsupportedShare = share,
            letters = letters,
        )
    }
}
