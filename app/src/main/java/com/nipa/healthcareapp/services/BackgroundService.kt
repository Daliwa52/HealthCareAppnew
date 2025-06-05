package com.nipa.healthcareapp.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.nipa.healthcareapp.R
import kotlinx.coroutines.*

class BackgroundService : Service() {
    private val CHANNEL_ID = "background_service_channel"
    private val NOTIFICATION_ID = 1002
    private val job = Job()
    private val serviceScope = CoroutineScope(Dispatchers.Main + job)

    companion object {
        fun startService(context: Context) {
            val startIntent = Intent(context, BackgroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(startIntent)
            } else {
                context.startService(startIntent)
            }
        }

        fun stopService(context: Context) {
            val stopIntent = Intent(context, BackgroundService::class.java)
            context.stopService(stopIntent)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())

        serviceScope.launch {
            while (isActive) {
                try {
                    // Perform background operations here
                    syncData()
                    delay(5000) // Check every 5 seconds
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
    }

    private suspend fun syncData() {
        // TODO: Implement data syncing logic
    }

    override fun onDestroy() {
        super.onDestroy()
        job.cancel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Background Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val notificationBuilder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Healthcare App")
            .setContentText("Syncing data in background...")
            .setSmallIcon(R.drawable.ic_sync)
            .setPriority(NotificationCompat.PRIORITY_LOW)

        return notificationBuilder.build()
    }
}
