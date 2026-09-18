package de.doppelcheck.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

@Composable
fun SettingsScreen(
    baseUrl: String,
    contactName: String,
    contactPhone: String,
    speakResult: Boolean,
    onSave: (String) -> Unit,
    onSaveContact: (String, String) -> Unit,
    onSpeakResultChange: (Boolean) -> Unit,
    onCheck: ((String) -> Unit) -> Unit,
    onBack: () -> Unit,
    screenScanSetup: @Composable () -> Unit = {},
) {
    var value by remember { mutableStateOf(baseUrl) }
    var status by remember { mutableStateOf("") }
    var name by remember { mutableStateOf(contactName) }
    var phone by remember { mutableStateOf(contactPhone) }
    var contactStatus by remember { mutableStateOf("") }

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

        Spacer(Modifier.height(32.dp))
        Text("Vorlesen", style = MaterialTheme.typography.headlineMedium)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
        ) {
            Column(modifier = Modifier.weight(1f).padding(end = 16.dp)) {
                Text("Ergebnis vorlesen", style = MaterialTheme.typography.bodyLarge)
                Text(
                    "Die Ampel und der Hinweissatz werden auf Deutsch vorgelesen, sobald das Ergebnis erscheint.",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            Switch(checked = speakResult, onCheckedChange = onSpeakResultChange)
        }

        Spacer(Modifier.height(32.dp))
        Text("Angehörige informieren", style = MaterialTheme.typography.headlineMedium)
        Text(
            "Bei einer roten Warnung können Sie diese Person mit einer SMS informieren. " +
                "Die SMS wird nur vorbereitet – abgeschickt wird sie erst, wenn Sie in der SMS-App auf Senden tippen. " +
                "Ohne Nummer bleibt der Knopf aus.",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 8.dp, bottom = 16.dp),
        )
        OutlinedTextField(
            value = name,
            onValueChange = { name = it },
            label = { Text("Name (freiwillig)", style = MaterialTheme.typography.bodyMedium) },
            placeholder = { Text("z. B. Tochter Anna", style = MaterialTheme.typography.bodyMedium) },
            textStyle = MaterialTheme.typography.bodyLarge,
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = phone,
            onValueChange = { phone = it },
            label = { Text("Handynummer", style = MaterialTheme.typography.bodyMedium) },
            placeholder = { Text("z. B. 0151 23456789", style = MaterialTheme.typography.bodyMedium) },
            textStyle = MaterialTheme.typography.bodyLarge,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(12.dp))
        Button(
            onClick = {
                onSaveContact(name, phone)
                contactStatus = if (phone.isBlank()) "Keine Nummer gespeichert." else "Gespeichert."
            },
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(64.dp),
        ) { Text("Person speichern", style = MaterialTheme.typography.labelLarge) }
        if (contactStatus.isNotBlank()) {
            Text(contactStatus, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(top = 16.dp))
        }

        Spacer(Modifier.height(32.dp))
        screenScanSetup()

        Spacer(Modifier.height(24.dp))
        OutlinedButton(
            onClick = onBack,
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().height(64.dp),
        ) { Text("Zurück", style = MaterialTheme.typography.labelLarge) }
    }
}
