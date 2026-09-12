package de.doppelcheck.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.core.content.IntentCompat
import de.doppelcheck.app.ui.DoppelCheckTheme
import de.doppelcheck.app.ui.ScanScreen
import de.doppelcheck.app.ui.SettingsScreen

class MainActivity : ComponentActivity() {

    private val viewModel: ScanViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            DoppelCheckTheme {
                Surface(modifier = Modifier.windowInsetsPadding(WindowInsets.systemBars)) {
                    var showSettings by remember { mutableStateOf(false) }
                    val input by viewModel.input.collectAsState()
                    val state by viewModel.state.collectAsState()
                    val baseUrl by viewModel.baseUrl.collectAsState()

                    if (showSettings) {
                        SettingsScreen(
                            baseUrl = baseUrl,
                            onSave = viewModel::saveBaseUrl,
                            onCheck = viewModel::checkConnection,
                            onBack = { showSettings = false },
                        )
                    } else {
                        ScanScreen(
                            input = input,
                            state = state,
                            serverConfigured = baseUrl.isNotBlank(),
                            onInputChange = viewModel::onInputChange,
                            onScan = { viewModel.scanText(input) },
                            onOpenSettings = { showSettings = true },
                        )
                    }
                }
            }
        }
        handleIntent(intent)
    }

    /** launchMode is singleTask, so a second share arrives here instead of in onCreate. */
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    /** Text or image shared from another app is scanned straight away. */
    private fun handleIntent(intent: Intent?) {
        if (intent == null || intent.action != Intent.ACTION_SEND) return
        val type = intent.type.orEmpty()
        when {
            type.startsWith("text/") ->
                intent.getStringExtra(Intent.EXTRA_TEXT)
                    ?.takeIf { it.isNotBlank() }
                    ?.let(viewModel::scanText)

            type.startsWith("image/") ->
                IntentCompat.getParcelableExtra(intent, Intent.EXTRA_STREAM, Uri::class.java)
                    ?.let(viewModel::scanImage)
        }
    }
}
