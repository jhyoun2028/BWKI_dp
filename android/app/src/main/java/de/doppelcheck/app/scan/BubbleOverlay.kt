package de.doppelcheck.app.scan

import android.annotation.SuppressLint
import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.provider.Settings
import android.util.TypedValue
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import android.widget.ImageView
import de.doppelcheck.app.R
import kotlin.math.hypot

/**
 * Round floating button drawn over other apps (SYSTEM_ALERT_WINDOW). Tap = [onTap],
 * drag = move it out of the way. Plain View instead of Compose: it is a single icon.
 */
class BubbleOverlay(private val context: Context, private val onTap: () -> Unit) {

    private val windowManager = context.getSystemService(WindowManager::class.java)
    private var view: View? = null

    fun show() {
        if (view != null || !Settings.canDrawOverlays(context)) return
        val size = dp(BUBBLE_DP)
        val metrics = context.resources.displayMetrics
        val params = WindowManager.LayoutParams(
            size,
            size,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = metrics.widthPixels - size - dp(12)
            y = metrics.heightPixels / 3
        }
        val bubble = createBubbleView(params)
        windowManager.addView(bubble, params)
        view = bubble
    }

    fun hide() {
        view?.let(windowManager::removeView)
        view = null
    }

    private fun createBubbleView(params: WindowManager.LayoutParams): View =
        ImageView(context).apply {
            setImageResource(R.drawable.ic_shield)
            imageTintList = ColorStateList.valueOf(Color.WHITE)
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(BUBBLE_COLOR)
                setStroke(dp(3), Color.WHITE)
            }
            val padding = dp(16)
            setPadding(padding, padding, padding, padding)
            contentDescription = "DoppelCheck: Bildschirm prüfen"
            setOnClickListener { onTap() }
            setOnTouchListener(DragToMove(params))
        }

    /** Moves the window while dragging; a touch that never passed the slop counts as a click. */
    private inner class DragToMove(private val params: WindowManager.LayoutParams) : View.OnTouchListener {
        private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop
        private var downX = 0f
        private var downY = 0f
        private var startX = 0
        private var startY = 0
        private var dragging = false

        @SuppressLint("ClickableViewAccessibility") // performClick() is called on ACTION_UP
        override fun onTouch(v: View, event: MotionEvent): Boolean {
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX
                    downY = event.rawY
                    startX = params.x
                    startY = params.y
                    dragging = false
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - downX
                    val dy = event.rawY - downY
                    if (!dragging && hypot(dx, dy) > touchSlop) dragging = true
                    if (dragging) {
                        params.x = startX + dx.toInt()
                        params.y = startY + dy.toInt()
                        windowManager.updateViewLayout(v, params)
                    }
                }
                MotionEvent.ACTION_UP -> if (!dragging) v.performClick()
            }
            return true
        }
    }

    private fun dp(value: Int): Int = TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP, value.toFloat(), context.resources.displayMetrics,
    ).toInt()

    private companion object {
        const val BUBBLE_DP = 72                       // well above the 64 dp minimum touch target
        val BUBBLE_COLOR = Color.parseColor("#0B3D6B") // app primary colour
    }
}
