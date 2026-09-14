package de.doppelcheck.app.tile

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService
import de.doppelcheck.app.MainActivity
import de.doppelcheck.app.scan.DoppelCheckAccessibilityService

/**
 * Quick Settings tile: one tap closes the panel and checks what is on screen.
 * If the accessibility service is not switched on yet, the tap opens DoppelCheck instead.
 * Add it once via the pencil icon in the Quick Settings panel.
 */
class ScanTileService : TileService() {

    override fun onStartListening() {
        super.onStartListening()
        qsTile?.apply {
            state = Tile.STATE_INACTIVE
            label = "DoppelCheck"
            subtitle = "Bildschirm prüfen"
            updateTile()
        }
    }

    override fun onClick() {
        super.onClick()
        val service = DoppelCheckAccessibilityService.instance
        if (service == null) {
            openApp()
            return
        }
        if (isLocked) unlockAndRun { scanBehindPanel(service) } else scanBehindPanel(service)
    }

    private fun scanBehindPanel(service: DoppelCheckAccessibilityService) {
        service.closeNotificationShade()
        // While the panel covers the screen the app window is not reachable; wait for it to close.
        service.scanScreen(delayMs = PANEL_CLOSE_DELAY_MS)
    }

    private fun openApp() {
        val intent = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
        // From Android 14 the Intent overload throws; a PendingIntent is required.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            val pending = PendingIntent.getActivity(
                this, 0, intent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
            )
            startActivityAndCollapse(pending)
        } else {
            @Suppress("DEPRECATION")
            startActivityAndCollapse(intent)
        }
    }

    private companion object {
        const val PANEL_CLOSE_DELAY_MS = 600L
    }
}
