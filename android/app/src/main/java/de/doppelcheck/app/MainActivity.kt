package de.doppelcheck.app

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
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
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import androidx.core.content.IntentCompat
import com.google.gson.Gson
import de.doppelcheck.app.api.ScanResult
import de.doppelcheck.app.contact.TrustedContact
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
                    val showSettings by viewModel.showSettings.collectAsState()
                    val input by viewModel.input.collectAsState()
                    val state by viewModel.state.collectAsState()
                    val baseUrl by viewModel.baseUrl.collectAsState()
                    val setup by viewModel.setup.collectAsState()
                    val contact by viewModel.contact.collectAsState()
                    val speakResult by viewModel.speakResult.collectAsState()

                    if (showSettings) {
                        SettingsScreen(
                            baseUrl = baseUrl,
                            contactName = contact.name,
                            contactPhone = contact.phone,
                            speakResult = speakResult,
                            onSave = viewModel::saveBaseUrl,
                            onSaveContact = viewModel::saveContact,
                            onSpeakResultChange = viewModel::setSpeakResult,
                            onCheck = viewModel::checkConnection,
                            onBack = viewModel::closeSettings,
                            screenScanSetup = {
                                ScreenScanSetup(
                                    status = setup,
                                    onOpenAccessibility = { SystemSettings.openAccessibility(this) },
                                    onOpenOverlay = { SystemSettings.openOverlayPermission(this) },
                                    onOpenAssistant = { SystemSettings.openAssistant(this) },
                                    onBubbleEnabledChange = viewModel::setBubbleEnabled,
                                    onChromeFilterEnabledChange = viewModel::setChromeFilterEnabled,
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
                            onOpenSettings = viewModel::openSettings,
                            onNotifyContact = { result -> notifyContact(result) },
                            speakResult = speakResult,
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

    /**
     * Opens the SMS app with a pre-filled warning for the trusted contact. Without a stored
     * contact [TrustedContact.intent] returns the settings instead, so the button always does
     * something. Nothing is sent until the user presses send in the SMS app.
     */
    private fun notifyContact(result: ScanResult) {
        val intent = TrustedContact.intent(this, result.reasonDe)
        runCatching { startActivity(intent) }.onFailure {
            Toast.makeText(this, "Keine SMS-App gefunden.", Toast.LENGTH_LONG).show()
        }
    }

    /** Text or image shared from another app is scanned straight away; a screen-scan result is shown. */
    private fun handleIntent(intent: Intent?) {
        if (intent?.action == ACTION_OPEN_SETTINGS) {
            viewModel.openSettings()
            return
        }
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
        const val ACTION_OPEN_SETTINGS = "de.doppelcheck.app.OPEN_SETTINGS"
        const val EXTRA_RESULT_JSON = "result_json"

        /** Opens the app directly on the settings screen (used when no contact is stored yet). */
        fun settingsIntent(context: Context): Intent =
            Intent(context, MainActivity::class.java)
                .setAction(ACTION_OPEN_SETTINGS)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
}
