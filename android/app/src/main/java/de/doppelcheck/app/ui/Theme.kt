package de.doppelcheck.app.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Traffic-light colours. Chosen dark enough that white text stays readable on them
// (contrast >= 4.5:1), because the target group often uses high brightness outdoors.
val VerdictRed = Color(0xFFB3261E)
// Amber, deliberately close to red: since the model moved, more phishing lands on yellow,
// and yellow must read as a warning. Dark enough that white text clears WCAG AA for normal
// text (4.6:1), because the in-app boxes use 20-22 sp body text and the target group is
// older users; the first amber (#BF8700) only reached 3.1:1.
val VerdictYellow = Color(0xFFA06A00)
val VerdictGreen = Color(0xFF1B5E20)
/** Not checked / verdict "unknown": neutral grey, so it can never be mistaken for green. */
val VerdictNeutral = Color(0xFF455A64)
val OnVerdict = Color.White

private val Light = lightColorScheme(primary = Color(0xFF0B3D6B), onPrimary = Color.White)
private val Dark = darkColorScheme(primary = Color(0xFF9BC4EA), onPrimary = Color(0xFF04263F))

/** Everything one step larger than the Material default: 20 sp is the smallest text used. */
private val LargeTypography = Typography(
    headlineLarge = TextStyle(fontSize = 34.sp, lineHeight = 40.sp, fontWeight = FontWeight.Bold),
    headlineMedium = TextStyle(fontSize = 28.sp, lineHeight = 34.sp, fontWeight = FontWeight.Bold),
    titleLarge = TextStyle(fontSize = 24.sp, lineHeight = 30.sp, fontWeight = FontWeight.SemiBold),
    bodyLarge = TextStyle(fontSize = 22.sp, lineHeight = 30.sp),
    bodyMedium = TextStyle(fontSize = 20.sp, lineHeight = 28.sp),
    labelLarge = TextStyle(fontSize = 22.sp, lineHeight = 28.sp, fontWeight = FontWeight.SemiBold),
)

@Composable
fun DoppelCheckTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) Dark else Light,
        typography = LargeTypography,
        content = content,
    )
}

// Only an explicit "green" is shown as safe. Anything else (e.g. the server's "unknown" when it
// found no message text) is neutral – an unexpected value must never turn into SICHER.
fun verdictColor(verdict: String): Color = when (verdict) {
    "red" -> VerdictRed
    "yellow" -> VerdictYellow
    "green" -> VerdictGreen
    else -> VerdictNeutral
}

fun verdictTitle(verdict: String): String = when (verdict) {
    "red" -> "ROT – Vorsicht, Betrug!"
    "yellow" -> "GELB – unklar, bitte nicht anklicken"
    "green" -> "GRÜN – sieht unbedenklich aus"
    else -> "Nicht geprüft"
}

/**
 * Extra sentence under `reason_de` for the yellow verdict. Yellow is not "probably fine":
 * it is the bucket most phishing lands in since the model changed, so it has to say what
 * to do. null for every other verdict.
 */
fun verdictAdvice(verdict: String): String? =
    if (verdict == "yellow") {
        "Wir sind nicht sicher. Öffnen Sie keine Links und fragen Sie im Zweifel bei der Firma nach – " +
            "über eine Nummer, die Sie selbst kennen."
    } else {
        null
    }

/** One-word verdict for the full-screen traffic-light panel and the notification title. */
fun verdictWord(verdict: String): String = when (verdict) {
    "red" -> "GEFAHR"
    "yellow" -> "UNKLAR"
    "green" -> "SICHER"
    else -> "NICHT GEPRÜFT"
}

fun levelWord(level: String): String = when (level) {
    "red" -> "gefährlich"
    "yellow" -> "verdächtig"
    else -> "unbedenklich"
}
