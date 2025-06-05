package com.nipa.healthcareapp.services;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

import com.google.android.gms.tasks.Task;
import com.google.android.gms.tasks.Tasks;
import com.google.firebase.firestore.CollectionReference;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.QuerySnapshot;
import com.nipa.healthcareapp.data.database.HealthCareDatabase;
import com.nipa.healthcareapp.data.models.ClientHistoryItem;
import com.nipa.healthcareapp.data.models.Notification;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
// import java.util.stream.Collectors; // Not strictly needed for this simplified version

public class DataSyncWorker extends Worker {

    private static final String TAG = "DataSyncWorker";
    private final HealthCareDatabase database;
    private final FirebaseFirestore firestore;
    // Define Firestore collection names as constants
    private static final String NOTIFICATIONS_COLLECTION = "notifications";
    private static final String CLIENT_HISTORY_COLLECTION = "client_history";
    // private static final String USERS_COLLECTION = "users"; // Example

    public DataSyncWorker(@NonNull Context context, @NonNull WorkerParameters workerParams) {
        super(context, workerParams);
        database = HealthCareDatabase.getDatabase(context);
        firestore = FirebaseFirestore.getInstance();
    }

    @NonNull
    @Override
    public Result doWork() {
        Log.d(TAG, "Data sync work started.");
        try {
            // String userId = getInputData().getString("USER_ID_KEY");
            // if (userId == null || userId.isEmpty()) {
            //     Log.e(TAG, "User ID is missing. Cannot sync.");
            //     return Result.failure();
            // }

            syncNotifications(); // Pass userId if needed
            syncClientHistory(); // Pass userId if needed
            syncOfflineChanges(); // Pass userId if needed

            Log.d(TAG, "Data sync work finished successfully.");
            return Result.success();
        } catch (Exception e) {
            Log.e(TAG, "Error during data sync work", e);
            if (e instanceof ExecutionException || e instanceof InterruptedException) {
                Log.w(TAG, "Sync failed due to task execution/interruption, retrying.");
                return Result.retry();
            }
            // For other types of errors, you might want to fail permanently
            // or retry based on the specific error.
            return Result.failure();
        }
    }

    private void syncNotifications() throws ExecutionException, InterruptedException {
        Log.d(TAG, "Syncing notifications...");
        CollectionReference notificationsRef = firestore.collection(NOTIFICATIONS_COLLECTION);
        // Example: Fetch from Firestore (simplified)
        Task<QuerySnapshot> fetchTask = notificationsRef.get();
        QuerySnapshot firestoreSnapshot = Tasks.await(fetchTask);

        List<Notification> firestoreNotifications = new ArrayList<>();
        for (DocumentSnapshot document : firestoreSnapshot.getDocuments()) {
            Notification notification = document.toObject(Notification.class);
            if (notification != null) {
                notification.setSynced(true); // Mark as synced as it's from Firestore
                firestoreNotifications.add(notification);
            }
        }
        if (!firestoreNotifications.isEmpty()) {
            Log.d(TAG, "Fetched " + firestoreNotifications.size() + " notifications from Firestore. Inserting/Updating locally.");
            database.notificationDao().insertAll(firestoreNotifications); // Assumes insertAll handles conflicts (e.g., REPLACE)
        }

        // Example: Push local unsynced notifications to Firestore
        List<Notification> localUnsynced = database.notificationDao().getUnsynced();
        if (!localUnsynced.isEmpty()) {
            Log.d(TAG, "Found " + localUnsynced.size() + " local unsynced notifications to push.");
            for (Notification notification : localUnsynced) {
                Task<Void> pushTask = notificationsRef.document(notification.getId()).set(notification);
                Tasks.await(pushTask);
                notification.setSynced(true);
                database.notificationDao().update(notification);
            }
        }
        Log.d(TAG, "Notifications sync complete.");
    }

    private void syncClientHistory() throws ExecutionException, InterruptedException {
        Log.d(TAG, "Syncing client history...");
        CollectionReference historyRef = firestore.collection(CLIENT_HISTORY_COLLECTION);

        Task<QuerySnapshot> fetchTask = historyRef.get();
        QuerySnapshot firestoreSnapshot = Tasks.await(fetchTask);

        List<ClientHistoryItem> firestoreHistoryItems = new ArrayList<>();
        for (DocumentSnapshot document : firestoreSnapshot.getDocuments()) {
            ClientHistoryItem item = document.toObject(ClientHistoryItem.class);
            if (item != null) {
                item.setSynced(true);
                firestoreHistoryItems.add(item);
            }
        }
        if (!firestoreHistoryItems.isEmpty()) {
            Log.d(TAG, "Fetched " + firestoreHistoryItems.size() + " client history items from Firestore. Inserting/Updating locally.");
            database.clientHistoryDao().insertAll(firestoreHistoryItems);
        }

        List<ClientHistoryItem> localUnsynced = database.clientHistoryDao().getUnsynced();
        if (!localUnsynced.isEmpty()) {
            Log.d(TAG, "Found " + localUnsynced.size() + " local unsynced client history items to push.");
            for (ClientHistoryItem item : localUnsynced) {
                Task<Void> pushTask = historyRef.document(item.getId()).set(item);
                Tasks.await(pushTask);
                item.setSynced(true);
                database.clientHistoryDao().update(item);
            }
        }
        Log.d(TAG, "Client history sync complete.");
    }

    private void syncOfflineChanges() throws ExecutionException, InterruptedException {
        Log.d(TAG, "Syncing other offline changes (if any)...");
        // Placeholder for other data models that need syncing.
        // Follow the pattern in syncNotifications() or syncClientHistory().
        Log.d(TAG, "Offline changes sync complete.");
    }
}
