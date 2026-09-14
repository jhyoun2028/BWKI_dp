package de.doppelcheck.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.doppelcheck.app.ScanState

private val LoadingBackground = Color(0xFF0B3D6B)
private val FailureBackground = Color(0xFF37474F)

private val WordStyle = TextStyle(fontSize = 64.sp, lineHeight = 72.sp, fontWeight = FontWeight.Black)
private val ReasonStyle = TextStyle(fontSize = 30.sp, lineHeight = 40.sp, fontWeight = FontWeight.SemiBold)
private val HintStyle = TextStyle(fontSize = 24.sp, lineHeight = 32.sp)
private val ButtonStyle = TextStyle(fontSize = 24.sp, fontWeight = FontWeight.Bold)

/**
 * Full-screen traffic-light panel for a screen scan: SICHER / VORSICHT / GEFAHR on the verdict
 * colour with `reason_de` below. Nothing on it is smaller than 24 sp.
 */
@Composable
fun VerdictPanel(state: ScanState, onClose: () -> Unit, onDetails: () -> Unit) {
    val background = when (state) {
        is ScanState.Success -> verdictColor(state.result.verdict)
        is ScanState.Failure -> FailureBackground
        else -> LoadingBackground
    }
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier
            .fillMaxSize()
            .background(background)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 28.dp, vertical = 40.dp),
    ) {
        when (state) {
            is ScanState.Success -> {
                Text(verdictWord(state.result.verdict), style = WordStyle, color = OnVerdict, textAlign = TextAlign.Center)
                Spacer(Modifier.height(24.dp))
                Text(state.result.reasonDe, style = ReasonStyle, color = OnVerdict, textAlign = TextAlign.Center)
            }
            is ScanState.Failure -> {
                Text("Prüfung nicht möglich", style = WordStyle.copy(fontSize = 40.sp, lineHeight = 48.sp), color = OnVerdict, textAlign = TextAlign.Center)
                Spacer(Modifier.height(24.dp))
                Text(state.message, style = ReasonStyle, color = OnVerdict, textAlign = TextAlign.Center)
            }
            else -> {
                CircularProgressIndicator(color = OnVerdict, strokeWidth = 6.dp, modifier = Modifier.size(96.dp))
                Spacer(Modifier.height(32.dp))
                Text("Prüfe …", style = WordStyle.copy(fontSize = 48.sp, lineHeight = 56.sp), color = OnVerdict)
                Spacer(Modifier.height(16.dp))
                Text(
                    "Das erste Prüfen kann bis zu einer Minute dauern. Das Ergebnis kommt auch als Benachrichtigung.",
                    style = HintStyle,
                    color = OnVerdict,
                    textAlign = TextAlign.Center,
                )
            }
        }

        Spacer(Modifier.height(40.dp))
        Button(
            onClick = onClose,
            shape = RoundedCornerShape(20.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = background),
            modifier = Modifier.fillMaxWidth().height(80.dp),
        ) { Text("Schließen", style = ButtonStyle) }

        if (state is ScanState.Success) {
            Spacer(Modifier.height(16.dp))
            OutlinedButton(
                onClick = onDetails,
                shape = RoundedCornerShape(20.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = OnVerdict),
                modifier = Modifier.fillMaxWidth().height(72.dp),
            ) { Text("Details in der App", style = ButtonStyle) }
        }
    }
}
