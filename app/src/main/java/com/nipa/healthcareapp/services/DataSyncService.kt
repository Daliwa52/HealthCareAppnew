package com.nipa.healthcareapp.services

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import com.google.firebase.auth.ktx.auth
import com.nipa.healthcareapp.data.database.HealthCareDatabase
import com.nipa.healthcareapp.data.models.Notification
import com.nipa.healthcareapp.data.models.ClientHistoryItem
import kotlinx.coroutines.tasks.await
import java.lang.Exception

class DataSyncService(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    private val TAG = "DataSyncService"
    private val database = HealthCareDatabase.getDatabase(context)
    private val firestore = Firebase.firestore

    override suspend fun doWork(): Result {
        return try {
            Log.d(TAG, "Starting data synchronization")
            
            // Sync notifications
            syncNotifications()
            
            // Sync client history
            syncClientHistory()
            
            // Sync offline changes
            syncOfflineChanges()
            
            Log.d(TAG, "Data synchronization completed successfully")
            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Error during data synchronization", e)
            Result.retry()
        }
    }

    private suspend fun syncNotifications() {
        Log.d(TAG, "Syncing notifications")
        
        try {
            // Get local notifications
            val localNotifications: List<Notification> = database.notificationDao().getAll()
            
            // Get remote notifications
            val remoteNotificationsQuery = firestore
                .collection("notifications")
                .whereEqualTo("userId", getCurrentUserId())
                .get()
                .await()
            
            val remoteNotificationsList: List<Notification> = remoteNotificationsQuery
                .toObjects(Notification::class.java)
            
            // Update local database
            database.notificationDao().insertAll(remoteNotificationsList)
            
            // Delete local notifications that don't exist in remote
            val localIdsList: List<String> = localNotifications.map { notification -> notification.id }
            val remoteIdsList: List<String> = remoteNotificationsList.map { notification -> notification.id }
            
            val idsToDelete: List<String> = localIdsList.filterNot { localId -> remoteIdsList.contains(localId) }
            
            if (idsToDelete.isNotEmpty()) {
                database.notificationDao().deleteByIds(idsToDelete)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error syncing notifications", e)
        }
    }

    private suspend fun syncClientHistory() {
        Log.d(TAG, "Syncing client history")
        
        try {
            // Get local history
            val localHistory: List<ClientHistoryItem> = database.clientHistoryDao().getAll()
            
            // Get remote history
            val remoteHistoryQuery = firestore
                .collection("client_history")
                .whereEqualTo("providerId", getCurrentUserId())
                .get()
                .await()
            
            val remoteHistoryList: List<ClientHistoryItem> = remoteHistoryQuery
                .toObjects(ClientHistoryItem::class.java)
            
            // Update local database
            database.clientHistoryDao().insertAll(remoteHistoryList)
            
            // Delete local items that don't exist in remote
            val localIdsList: List<String> = localHistory.map { item -> item.id }
            val remoteIdsList: List<String> = remoteHistoryList.map { item -> item.id }
            
            val idsToDelete: List<String> = localIdsList.filterNot { localId -> remoteIdsList.contains(localId) }
            
            if (idsToDelete.isNotEmpty()) {
                database.clientHistoryDao().deleteByIds(idsToDelete)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error syncing client history", e)
        }
    }

    private suspend fun syncOfflineChanges() {
        Log.d(TAG, "Syncing offline changes")
        
        try {
            // Get and sync unsynced notifications
            val unsyncedNotifications: List<Notification> = database.notificationDao().getUnsynced()
            Log.d(TAG, "Found ${unsyncedNotifications.size} unsynced notifications")
            
            for (notification in unsyncedNotifications) {
                try {
                    firestore.collection("notifications")
                        .document(notification.id)
                        .set(notification)
                        .await()
                    
                    // Mark as synced and update
                    val updatedNotification = notification.copy(synced = true)
                    database.notificationDao().update(updatedNotification)
                    
                    Log.d(TAG, "Synced notification ${notification.id}")
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to sync notification ${notification.id}", e)
                }
            }
            
            // Get and sync unsynced client history
            val unsyncedHistory: List<ClientHistoryItem> = database.clientHistoryDao().getUnsynced()
            Log.d(TAG, "Found ${unsyncedHistory.size} unsynced history items")
            
            for (historyItem in unsyncedHistory) {
                try {
                    firestore.collection("client_history")
                        .document(historyItem.id)
                        .set(historyItem)
                        .await()
                    
                    // Mark as synced and update
                    val updatedHistoryItem = historyItem.copy(synced = true)
                    database.clientHistoryDao().update(updatedHistoryItem)
                    
                    Log.d(TAG, "Synced history item ${historyItem.id}")
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to sync history item ${historyItem.id}", e)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in syncOfflineChanges", e)
        }
    }

    private fun getCurrentUserId(): String {
        return Firebase.auth.currentUser?.uid ?: ""
    }
}
