package de.doppelcheck.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.core.content.ContextCompat
import androidx.core.content.IntentCompat
import com.google.gson.Gson
import de.doppelcheck.app.api.ScanResult
import de.doppelcheck.app.scan.SystemSettings
import de.doppelcheck.app.ui.DoppelCheckTheme
import de.doppelcheck.app.ui.ScreenScanSetup
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
                    val setup by viewModel.setup.collectAsState()

                    if (showSettings) {
                        SettingsScreen(
                            baseUrl = baseUrl,
                            onSave = viewModel::saveBaseUrl,
                            onCheck = viewModel::checkConnection,
                            onBack = { showSettings = false },
                            screenScanSetup = {
                                ScreenScanSetup(
                                    status = setup,
                                    onOpenAccessibility = { SystemSettings.openAccessibility(this) },
                                    onOpenOverlay = { SystemSettings.openOverlayPermission(this) },
                                    onOpenAssistant = { SystemSettings.openAssistant(this) },
                                    onBubbleEnabledChange = viewModel::setBubbleEnabled,
                                )
                            },
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
        requestNotificationPermission()
    }

    override fun onResume() {
        super.onResume()
        viewModel.refreshSetup()
    }

    /** launchMode is singleTask, so a second share arrives here instead of in onCreate. */
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    /** Android 13+: the verdict of a screen scan is also posted as a notification. */
    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        val permission = Manifest.permission.POST_NOTIFICATIONS
        if (ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED) return
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }.launch(permission)
    }

    /** Text or image shared from another app is scanned straight away; a screen-scan result is shown. */
    private fun handleIntent(intent: Intent?) {
        if (intent?.action == ACTION_SHOW_RESULT) {
            intent.getStringExtra(EXTRA_RESULT_JSON)
                ?.let { runCatching { Gson().fromJson(it, ScanResult::class.java) }.getOrNull() }
                ?.let(viewModel::showResult)
            return
        }
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

    companion object {
        const val ACTION_SHOW_RESULT = "de.doppelcheck.app.SHOW_RESULT"
        const val EXTRA_RESULT_JSON = "result_json"
    }
}
