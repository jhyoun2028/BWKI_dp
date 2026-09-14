package de.doppelcheck.app.scan

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.view.accessibility.AccessibilityWindowInfo
import de.doppelcheck.app.ScanState
import de.doppelcheck.app.SettingsStore
import de.doppelcheck.app.api.ApiClient
import de.doppelcheck.app.api.TextRequest
import de.doppelcheck.app.api.describeError
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelChildren
import kotlinx.coroutines.launch

/**
 * Reads the text of the app the user is looking at – but only when explicitly asked to.
 *
 * `res/xml/accessibility_service_config.xml` declares no event types, so the system never
 * delivers accessibility events to this service: nothing is observed or captured in the
 * background. Text is read only in [scanScreen], which is called by the floating bubble,
 * the Quick Settings tile and the assistant gesture. The text is sent to POST /scan-text
 * and kept nowhere else.
 */
class DoppelCheckAccessibilityService : AccessibilityService() {

    private val handler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var scanJob: Job? = null
    private var bubble: BubbleOverlay? = null
    private val resultOverlay by lazy { ResultOverlay(this, onDetails = ::openDetails) }
    private val notifier by lazy { VerdictNotifier(this) }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        bubble = BubbleOverlay(this) { scanScreen() }
        updateBubble()
    }

    override fun onUnbind(intent: Intent?): Boolean {
        shutDown()
        return super.onUnbind(intent)
    }

    override fun onDestroy() {
        shutDown()
        super.onDestroy()
    }

    private fun shutDown() {
        instance = null
        handler.removeCallbacksAndMessages(null)
        scope.coroutineContext.cancelChildren()
        resultOverlay.hide()
        bubble?.hide()
        bubble = null
    }

    /** Not subscribed to any event type (see class doc), so there is nothing to handle. */
    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit

    override fun onInterrupt() = Unit

    /** Shows or hides the bubble according to the user's switch and the overlay permission. */
    fun updateBubble() {
        if (SettingsStore(this).bubbleEnabled && Settings.canDrawOverlays(this)) bubble?.show() else bubble?.hide()
    }

    /** Explicit trigger: read the screen after [delayMs] (time for a panel to close) and check it. */
    fun scanScreen(delayMs: Long = 0) {
        handler.postDelayed({ onScreenText(collectScreenText()) }, delayMs)
    }

    /** Closes the Quick Settings panel so the app underneath becomes visible again. */
    fun closeNotificationShade() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            performGlobalAction(GLOBAL_ACTION_DISMISS_NOTIFICATION_SHADE)
        } else {
            performGlobalAction(GLOBAL_ACTION_BACK)
        }
    }

    /** Sends the screen text to POST /scan-text and shows the verdict as overlay and notification. */
    private fun onScreenText(text: String) {
        if (scanJob?.isActive == true) {
            // A tap while the previous check is still running brings its progress back.
            resultOverlay.show(ScanState.Loading)
            return
        }
        val settings = SettingsStore(this)
        when {
            !settings.isConfigured -> showFailure(
                "Noch keine Serveradresse eingetragen. Bitte in der DoppelCheck-App unter Einstellungen nachholen.",
            )
            text.isBlank() -> showFailure("Auf dem Bildschirm wurde kein Text gefunden.")
            else -> scanJob = scope.launch {
                resultOverlay.show(ScanState.Loading)
                try {
                    val result = ApiClient.api.scanText(settings.endpoint("/scan-text"), TextRequest(text))
                    notifier.showResult(result)
                    // Closed while waiting: the notification alone is enough, do not pop up again.
                    if (resultOverlay.isShowing) resultOverlay.show(ScanState.Success(result))
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    val message = describeError(e)
                    notifier.showFailure(message)
                    if (resultOverlay.isShowing) resultOverlay.show(ScanState.Failure(message))
                }
            }
        }
    }

    private fun showFailure(message: String) {
        notifier.showFailure(message)
        resultOverlay.show(ScanState.Failure(message))
    }

    private fun openDetails(success: ScanState.Success) {
        startActivity(VerdictNotifier.resultIntent(this, success.result))
    }

    /** Visible text of the foreground app window, newline-joined. Empty if no window is found. */
    fun collectScreenText(): String {
        val root = targetRoot() ?: return ""
        return ScreenTextCollector.collect(root)
    }

    /**
     * Root node of the app window the user is looking at. Our own windows (bubble, result
     * overlay) and system UI are ignored: touching the bubble can make it the "active" window.
     */
    private fun targetRoot(): AccessibilityNodeInfo? {
        val appWindows = windows
            .filter { it.type == AccessibilityWindowInfo.TYPE_APPLICATION }
            .mapNotNull { window -> window.root?.let { root -> window to root } }
            .filter { (_, root) -> root.packageName != packageName }
        val chosen = appWindows.firstOrNull { it.first.isActive }
            ?: appWindows.firstOrNull { it.first.isFocused }
            ?: appWindows.firstOrNull()
        return chosen?.second ?: rootInActiveWindow?.takeIf { it.packageName != packageName }
    }

    companion object {
        /** The running service, or null while it is switched off in the accessibility settings. */
        @Volatile
        var instance: DoppelCheckAccessibilityService? = null
            private set
    }
}
