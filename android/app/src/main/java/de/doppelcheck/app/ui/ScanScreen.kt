package de.doppelcheck.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.doppelcheck.app.ScanState
import de.doppelcheck.app.api.ScanResult

@Composable
fun ScanScreen(
    input: String,
    state: ScanState,
    serverConfigured: Boolean,
    onInputChange: (String) -> Unit,
    onScan: () -> Unit,
    onOpenSettings: () -> Unit,
    onNotifyContact: (ScanResult) -> Unit = {},
    speakResult: Boolean = false,
) {
    SpeakVerdict(state, speakResult)
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
            Text("DoppelCheck", style = MaterialTheme.typography.headlineLarge, modifier = Modifier.weight(1f))
            IconButton(onClick = onOpenSettings, modifier = Modifier.height(56.dp)) {
                Icon(Icons.Filled.Settings, contentDescription = "Einstellungen", modifier = Modifier.size(36.dp))
            }
        }
        Text(
            "Nachricht einfügen und auf „Prüfen“ tippen. Oder eine Nachricht aus einer anderen App hierher teilen.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 4.dp, bottom = 16.dp),
        )

        if (!serverConfigured) {
            Card(
                colors = CardDefaults.cardColors(containerColor = VerdictYellow),
                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
            ) {
                Text(
                    "Noch keine Serveradresse eingetragen. Bitte oben rechts auf das Zahnrad tippen.",
                    color = OnVerdict,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.padding(16.dp),
                )
            }
        }

        OutlinedTextField(
            value = input,
            onValueChange = onInputChange,
            label = { Text("Nachricht", style = MaterialTheme.typography.bodyMedium) },
            textStyle = MaterialTheme.typography.bodyLarge,
            minLines = 4,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(Modifier.height(16.dp))
        Button(
            onClick = onScan,
            enabled = state !is ScanState.Loading,
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(72.dp),
        ) {
            Text(
                if (state is ScanState.Loading) "Prüfe …" else "Prüfen",
                style = MaterialTheme.typography.labelLarge,
            )
        }

        Spacer(Modifier.height(20.dp))
        when (state) {
            is ScanState.Idle -> Unit
            is ScanState.Loading -> Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator()
                    Text("Prüfe …", style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(start = 16.dp))
                }
                Text(
                    "Das erste Prüfen kann bis zu einer Minute dauern. Bitte warten.",
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
            is ScanState.Failure -> MessageBox(VerdictYellow, "Das hat nicht geklappt", state.message)
            is ScanState.NotChecked -> MessageBox(VerdictNeutral, "Nicht geprüft", state.message)
            is ScanState.Success -> ResultBox(state.result, onNotifyContact)
        }
    }
}

@Composable
private fun MessageBox(background: Color, title: String, body: String) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(background)
            .padding(20.dp),
    ) {
        Text(title, style = MaterialTheme.typography.headlineMedium, color = OnVerdict)
        Text(body, style = MaterialTheme.typography.bodyLarge, color = OnVerdict, modifier = Modifier.padding(top = 8.dp))
    }
}

@Composable
private fun ResultBox(result: ScanResult, onNotifyContact: (ScanResult) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        MessageBox(verdictColor(result.verdict), verdictTitle(result.verdict), result.reasonDe)

        if (result.verdict == "red") {
            Button(
                onClick = { onNotifyContact(result) },
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth().height(72.dp),
            ) { Text("Angehörige informieren", style = MaterialTheme.typography.labelLarge) }
        }

        if (result.urls.isNotEmpty()) {
            Text("Gefundene Links", style = MaterialTheme.typography.titleLarge)
            result.urls.forEach { finding ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(
                            levelWord(finding.level).uppercase(),
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = verdictColor(finding.level),
                        )
                        Text(finding.url, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                        finding.reasons.forEach { reason ->
                            Text("• $reason", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                        }
                    }
                }
            }
            Text(
                "DoppelCheck öffnet keine Links. Tippen Sie selbst nichts an, was hier rot ist.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        result.text?.takeIf { it.isNotBlank() }?.let { recognised ->
            Text("Erkannter Text im Bild", style = MaterialTheme.typography.titleLarge)
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(recognised, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(16.dp))
            }
        }
    }
}
