package de.doppelcheck.app.scan

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.view.accessibility.AccessibilityWindowInfo

/**
 * Reads the text of the app the user is looking at – but only when explicitly asked to.
 *
 * `res/xml/accessibility_service_config.xml` declares no event types, so the system never
 * delivers accessibility events to this service: nothing is observed or captured in the
 * background. The only way text is read is a call to [collectScreenText].
 */
class DoppelCheckAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onUnbind(intent: Intent?): Boolean {
        instance = null
        return super.onUnbind(intent)
    }

    override fun onDestroy() {
        instance = null
        super.onDestroy()
    }

    /** Not subscribed to any event type (see class doc), so there is nothing to handle. */
    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit

    override fun onInterrupt() = Unit

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
