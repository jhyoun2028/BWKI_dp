package de.doppelcheck.app.scan

import android.content.Context
import android.graphics.PixelFormat
import android.provider.Settings
import android.view.KeyEvent
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.platform.ComposeView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.setViewTreeLifecycleOwner
import androidx.savedstate.SavedStateRegistry
import androidx.savedstate.SavedStateRegistryController
import androidx.savedstate.SavedStateRegistryOwner
import androidx.savedstate.setViewTreeSavedStateRegistryOwner
import de.doppelcheck.app.ScanState
import de.doppelcheck.app.SettingsStore
import de.doppelcheck.app.ui.DoppelCheckTheme
import de.doppelcheck.app.ui.VerdictPanel

/**
 * Full-screen window over the current app that shows [VerdictPanel]. Uses the overlay
 * permission (SYSTEM_ALERT_WINDOW); without it, falls back to an accessibility overlay,
 * which [context] – the accessibility service – may always draw.
 */
class ResultOverlay(
    private val context: Context,
    private val onDetails: (ScanState.Success) -> Unit,
    private val onNotifyContact: (ScanState.Success) -> Unit = {},
) {

    private val windowManager = context.getSystemService(WindowManager::class.java)
    private val state = mutableStateOf<ScanState>(ScanState.Loading)
    // Read once per scan, not on every recomposition: the user cannot change it while it shows.
    private val speakResult = mutableStateOf(false)
    private var root: FrameLayout? = null
    private var owner: OverlayLifecycleOwner? = null

    val isShowing: Boolean get() = root != null

    /** Shows the panel in [newState], or updates it if it is already on screen. */
    fun show(newState: ScanState) {
        state.value = newState
        if (root != null) return
        speakResult.value = SettingsStore(context).speakResult

        val lifecycleOwner = OverlayLifecycleOwner().also { it.start() }
        val composeView = ComposeView(context).apply {
            setViewTreeLifecycleOwner(lifecycleOwner)
            setViewTreeSavedStateRegistryOwner(lifecycleOwner)
            setContent {
                DoppelCheckTheme {
                    VerdictPanel(
                        state = state.value,
                        onClose = ::hide,
                        onDetails = { (state.value as? ScanState.Success)?.let { hide(); onDetails(it) } },
                        // Hide first: the SMS app must come up in front, not behind the overlay.
                        onNotifyContact = { (state.value as? ScanState.Success)?.let { hide(); onNotifyContact(it) } },
                        speakResult = speakResult.value,
                    )
                }
            }
        }
        val container = BackKeyFrame(context, onBack = ::hide).apply { addView(composeView) }
        container.setViewTreeLifecycleOwner(lifecycleOwner)
        container.setViewTreeSavedStateRegistryOwner(lifecycleOwner)

        windowManager.addView(container, layoutParams())
        root = container
        owner = lifecycleOwner
    }

    fun hide() {
        root?.let(windowManager::removeView)
        owner?.destroy()
        root = null
        owner = null
    }

    private fun layoutParams(): WindowManager.LayoutParams {
        val type = if (Settings.canDrawOverlays(context)) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY
        }
        // Focusable on purpose (no FLAG_NOT_FOCUSABLE) so the back key reaches BackKeyFrame.
        return WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            type,
            0,
            PixelFormat.OPAQUE,
        )
    }

    /** Closes the overlay on the system back key, as users expect from any full-screen view. */
    private class BackKeyFrame(context: Context, private val onBack: () -> Unit) : FrameLayout(context) {
        override fun dispatchKeyEvent(event: KeyEvent): Boolean {
            if (event.keyCode == KeyEvent.KEYCODE_BACK) {
                if (event.action == KeyEvent.ACTION_UP) onBack()
                return true
            }
            return super.dispatchKeyEvent(event)
        }
    }

    /** Compose needs a lifecycle and saved-state owner; a window outside an Activity has neither. */
    private class OverlayLifecycleOwner : SavedStateRegistryOwner {
        private val registry = LifecycleRegistry(this)
        private val savedState = SavedStateRegistryController.create(this)

        override val lifecycle: Lifecycle get() = registry
        override val savedStateRegistry: SavedStateRegistry get() = savedState.savedStateRegistry

        fun start() {
            savedState.performRestore(null)
            registry.currentState = Lifecycle.State.RESUMED
        }

        fun destroy() {
            registry.currentState = Lifecycle.State.DESTROYED
        }
    }
}
