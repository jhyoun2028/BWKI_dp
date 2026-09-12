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
val VerdictYellow = Color(0xFF8A5A00)
val VerdictGreen = Color(0xFF1B5E20)
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

fun verdictColor(verdict: String): Color = when (verdict) {
    "red" -> VerdictRed
    "yellow" -> VerdictYellow
    else -> VerdictGreen
}

fun verdictTitle(verdict: String): String = when (verdict) {
    "red" -> "ROT – Vorsicht, Betrug!"
    "yellow" -> "GELB – Bitte prüfen"
    else -> "GRÜN – sieht unbedenklich aus"
}

fun levelWord(level: String): String = when (level) {
    "red" -> "gefährlich"
    "yellow" -> "verdächtig"
    else -> "unbedenklich"
}
