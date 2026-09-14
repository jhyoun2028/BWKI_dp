package de.doppelcheck.app.scan

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.Settings

/** Opens the system screens needed for the one-time setup of the screen scan. */
object SystemSettings {

    fun openAccessibility(context: Context) =
        start(context, Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))

    fun openOverlayPermission(context: Context) = start(
        context,
        Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:${context.packageName}")),
    )

    private fun start(context: Context, intent: Intent) {
        context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }
}
