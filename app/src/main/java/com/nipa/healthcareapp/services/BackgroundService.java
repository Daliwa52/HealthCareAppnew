package com.nipa.healthcareapp.services;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat; // For ContextCompat.startForegroundService

import com.nipa.healthcareapp.MainActivity; // Assuming MainActivity.java
import com.nipa.healthcareapp.R; // For icons

public class BackgroundService extends Service {

    private static final String TAG = "BackgroundService";
    private static final String CHANNEL_ID = "background_service_channel";
    private static final String CHANNEL_NAME = "Background Service"; // Added for channel
    private static final int NOTIFICATION_ID = 1002;

    private volatile Thread backgroundThread;

    // Static methods to start and stop the service
    public static void startService(Context context) {
        Intent serviceIntent = new Intent(context, BackgroundService.class);
        ContextCompat.startForegroundService(context, serviceIntent);
    }

    public static void stopService(Context context) {
        Intent serviceIntent = new Intent(context, BackgroundService.class);
        context.stopService(serviceIntent);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "onCreate");
        createNotificationChannel();
        Notification notification = createNotification();
        startForeground(NOTIFICATION_ID, notification);

        // Initialize and start the background thread
        backgroundThread = new Thread(() -> {
            Log.d(TAG, "Background thread started.");
            while (!Thread.currentThread().isInterrupted()) {
                try {
                    syncData();
                    Thread.sleep(5000); // 5 seconds delay
                } catch (InterruptedException e) {
                    Log.w(TAG, "Background thread interrupted during sleep.");
                    Thread.currentThread().interrupt(); // Preserve interrupt status
                    break; // Exit loop if interrupted
                } catch (Exception e) {
                    Log.e(TAG, "Error in background task", e);
                    // Optionally, add a shorter delay before retrying on other exceptions
                    // or implement more sophisticated error handling.
                }
            }
            Log.d(TAG, "Background thread finishing.");
        });
        backgroundThread.setName("BackgroundService-SyncThread");
        backgroundThread.start();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "onStartCommand");
        // We want this service to continue running until it is explicitly stopped, so return sticky.
        return START_STICKY;
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        // This is not a bound service, so return null
        return null;
    }

    private void syncData() {
        // Placeholder for data synchronization logic
        Log.d(TAG, "syncData called - performing synchronization...");
        // Example:
        // HealthCareDatabase db = HealthCareDatabase.getDatabase(getApplicationContext());
        // List<ClientHistoryItem> unsyncedItems = db.clientHistoryDao().getUnsynced();
        // if (!unsyncedItems.isEmpty()) {
        //     Log.d(TAG, "Found " + unsyncedItems.size() + " unsynced items.");
        //     // ... actual sync logic with a remote server ...
        // } else {
        //     Log.d(TAG, "No items to sync.");
        // }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "onDestroy - stopping background thread.");
        if (backgroundThread != null) {
            backgroundThread.interrupt();
            try {
                backgroundThread.join(1000); // Wait for the thread to die for max 1 second
                Log.d(TAG, "Background thread joined.");
            } catch (InterruptedException e) {
                Log.w(TAG, "Interrupted while waiting for background thread to join.");
                Thread.currentThread().interrupt();
            }
            backgroundThread = null;
        }
        Log.d(TAG, "Service destroyed.");
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel serviceChannel = new NotificationChannel(
                    CHANNEL_ID,
                    CHANNEL_NAME, // User visible channel name
                    NotificationManager.IMPORTANCE_LOW // Low importance for background service
            );
            serviceChannel.setDescription("Channel for Background Service notifications");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(serviceChannel);
                Log.d(TAG, "Notification channel created.");
            } else {
                Log.e(TAG, "NotificationManager is null, cannot create channel.");
            }
        }
    }

    private Notification createNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class); // Or your desired activity
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this,
                0,
                notificationIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Background Service Active")
                .setContentText("Performing background operations...")
                .setSmallIcon(R.mipmap.ic_launcher) // Replace with your app's icon
                .setContentIntent(pendingIntent)
                .setOngoing(true) // Makes the notification non-dismissible
                .build();
    }
}
