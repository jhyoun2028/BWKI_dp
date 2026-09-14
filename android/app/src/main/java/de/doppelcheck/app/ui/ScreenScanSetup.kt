package de.doppelcheck.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/** What the one-time setup of "Bildschirm prüfen" has reached so far. */
data class SetupStatus(
    val accessibilityOn: Boolean = false,
    val overlayAllowed: Boolean = false,
    val bubbleEnabled: Boolean = true,
)

/** Settings section: status and shortcuts to the system screens needed for the screen scan. */
@Composable
fun ScreenScanSetup(
    status: SetupStatus,
    onOpenAccessibility: () -> Unit,
    onOpenOverlay: () -> Unit,
    onBubbleEnabledChange: (Boolean) -> Unit,
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text("Bildschirm prüfen einrichten", style = MaterialTheme.typography.headlineMedium)
        Text(
            "Einmalig nötig, damit der runde Knopf und die Kachel den Bildschirm prüfen können. " +
                "Gelesen wird nur, wenn Sie selbst tippen.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 8.dp),
        )

        SetupStep(
            title = "1. Bedienungshilfe",
            done = status.accessibilityOn,
            doneText = "eingeschaltet",
            todoText = "aus – unter „Installierte Apps“ DoppelCheck einschalten",
            buttonText = "Bedienungshilfen öffnen",
            onClick = onOpenAccessibility,
        )
        SetupStep(
            title = "2. Über anderen Apps anzeigen",
            done = status.overlayAllowed,
            doneText = "erlaubt",
            todoText = "nicht erlaubt – für den runden Knopf und die große Ampel nötig",
            buttonText = "Erlaubnis öffnen",
            onClick = onOpenOverlay,
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth().padding(top = 20.dp),
        ) {
            Text(
                "Runden Knopf anzeigen",
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.weight(1f),
            )
            Switch(checked = status.bubbleEnabled, onCheckedChange = onBubbleEnabledChange)
        }
    }
}

@Composable
private fun SetupStep(
    title: String,
    done: Boolean,
    doneText: String,
    todoText: String,
    buttonText: String,
    onClick: () -> Unit,
) {
    Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 20.dp))
    Text(
        if (done) "✓ $doneText" else todoText,
        style = MaterialTheme.typography.bodyLarge,
        fontWeight = if (done) FontWeight.Bold else FontWeight.Normal,
        color = if (done) VerdictGreen else MaterialTheme.colorScheme.onSurface,
        modifier = Modifier.padding(top = 4.dp),
    )
    if (!done) {
        OutlinedButton(
            onClick = onClick,
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(64.dp).padding(top = 8.dp),
        ) { Text(buttonText, style = MaterialTheme.typography.labelLarge) }
    }
}
