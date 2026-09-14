package de.doppelcheck.app.scan

import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.compose.ui.graphics.toArgb
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.gson.Gson
import de.doppelcheck.app.MainActivity
import de.doppelcheck.app.R
import de.doppelcheck.app.api.ScanResult
import de.doppelcheck.app.ui.verdictColor
import de.doppelcheck.app.ui.verdictWord

/** Posts the result of a screen scan as a system notification. */
class VerdictNotifier(private val context: Context) {

    init {
        val channel = NotificationChannel(CHANNEL_ID, "Prüfergebnis", NotificationManager.IMPORTANCE_HIGH).apply {
            description = "Ergebnis, nachdem Sie den Bildschirm mit DoppelCheck geprüft haben"
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    fun showResult(result: ScanResult) {
        post(
            title = "${verdictWord(result.verdict)} – DoppelCheck",
            text = result.reasonDe,
            color = verdictColor(result.verdict).toArgb(),
            contentIntent = resultIntent(context, result),
        )
    }

    fun showFailure(message: String) {
        val openApp = Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        post(title = "DoppelCheck – Prüfung nicht möglich", text = message, color = null, contentIntent = openApp)
    }

    @SuppressLint("MissingPermission") // checked via areNotificationsEnabled()
    private fun post(title: String, text: String, color: Int?, contentIntent: Intent) {
        // False when notifications are off or, on Android 13+, POST_NOTIFICATIONS was not granted.
        // The overlay is then the only output.
        val manager = NotificationManagerCompat.from(context)
        if (!manager.areNotificationsEnabled()) return

        val pending = PendingIntent.getActivity(
            context, 0, contentIntent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pending)
            .setAutoCancel(true)
            .apply { color?.let(::setColor) }
            .build()
        manager.notify(NOTIFICATION_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "scan_result"
        private const val NOTIFICATION_ID = 1

        /** Opens DoppelCheck with [result] shown, including the list of found links. */
        fun resultIntent(context: Context, result: ScanResult): Intent =
            Intent(context, MainActivity::class.java)
                .setAction(MainActivity.ACTION_SHOW_RESULT)
                .putExtra(MainActivity.EXTRA_RESULT_JSON, Gson().toJson(result))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
}
