package de.doppelcheck.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SettingsScreen(
    baseUrl: String,
    onSave: (String) -> Unit,
    onCheck: ((String) -> Unit) -> Unit,
    onBack: () -> Unit,
) {
    var value by remember { mutableStateOf(baseUrl) }
    var status by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
    ) {
        Text("Einstellungen", style = MaterialTheme.typography.headlineLarge)
        Text(
            "Adresse des DoppelCheck-Servers. Die ngrok-Adresse ändert sich bei jedem Start des Servers.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 8.dp, bottom = 16.dp),
        )

        OutlinedTextField(
            value = value,
            onValueChange = { value = it },
            label = { Text("Serveradresse", style = MaterialTheme.typography.bodyMedium) },
            placeholder = { Text("https://xxxx.ngrok-free.app", style = MaterialTheme.typography.bodyMedium) },
            textStyle = MaterialTheme.typography.bodyLarge,
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            "Ohne „https://“ ergänzen wir es automatisch. Ein Schrägstrich am Ende ist egal.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 8.dp),
        )

        Spacer(Modifier.height(20.dp))
        Button(
            onClick = { onSave(value); status = "Gespeichert." },
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(64.dp),
        ) { Text("Speichern", style = MaterialTheme.typography.labelLarge) }

        Spacer(Modifier.height(12.dp))
        OutlinedButton(
            onClick = { onSave(value); status = "Prüfe Verbindung …"; onCheck { status = it } },
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(64.dp),
        ) { Text("Verbindung testen", style = MaterialTheme.typography.labelLarge) }

        if (status.isNotBlank()) {
            Text(status, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(top = 20.dp))
        }

        Spacer(Modifier.height(24.dp))
        OutlinedButton(
            onClick = onBack,
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(64.dp),
        ) { Text("Zurück", style = MaterialTheme.typography.labelLarge) }
    }
}
