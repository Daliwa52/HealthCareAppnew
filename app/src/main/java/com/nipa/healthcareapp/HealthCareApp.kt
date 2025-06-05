package com.nipa.healthcareapp

import kotlinx.coroutines.tasks.await

import android.app.Application
import android.content.Context
import androidx.room.Room
import com.google.firebase.FirebaseApp
import com.google.firebase.analytics.FirebaseAnalytics
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.ktx.auth
import com.google.firebase.crashlytics.FirebaseCrashlytics
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import com.google.firebase.messaging.FirebaseMessaging
import com.nipa.healthcareapp.data.database.HealthCareDatabase
import com.nipa.healthcareapp.data.models.ClientHistoryItem
import com.nipa.healthcareapp.data.models.Notification
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicBoolean

class HealthCareApp : Application() {
    private val appScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private val isInitialized = AtomicBoolean(false)
    lateinit var database: HealthCareDatabase
    lateinit var firestore: FirebaseFirestore
    private val offlineData = mutableMapOf<String, Any>()

    override fun onCreate() {
        super.onCreate()
        
        appScope.launch {
            if (isInitialized.compareAndSet(false, true)) {
                initializeDatabase()
                initializeFirebase()
                initializeAnalytics()
                initializeCrashlytics()
                initializeMessaging()
                initializeOfflineSync()
            }
        }
    }

    private suspend fun initializeDatabase() {
        database = Room.databaseBuilder(
            applicationContext,
            HealthCareDatabase::class.java,
            "healthcare-db"
        ).build()
    }

    private suspend fun initializeFirebase() {
        FirebaseApp.initializeApp(this)
        firestore = Firebase.firestore
    }

    private suspend fun initializeAnalytics() {
        val analytics = FirebaseAnalytics.getInstance(this)
        analytics.setAnalyticsCollectionEnabled(true)
    }

    private suspend fun initializeCrashlytics() {
        val crashlytics = FirebaseCrashlytics.getInstance()
        crashlytics.setCrashlyticsCollectionEnabled(true)
    }

    private suspend fun initializeMessaging() {
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val token = task.result
                // Store token in shared preferences or database
            } else {
                // Handle error
            }
        }
    }

    private suspend fun initializeOfflineSync() {
        // Initialize offline data sync
        appScope.launch {
            try {
                // Sync initial data
                syncData()
            } catch (e: Exception) {
                // Log error but don't crash
                FirebaseCrashlytics.getInstance().recordException(e)
            }
        }
    }

    suspend fun syncData() {
        // Sync notifications
        syncNotifications()
        
        // Sync client history
        syncClientHistory()
    }

    private suspend fun syncNotifications() {
        val localNotifications = database.notificationDao().getAll()
        val remoteNotifications = firestore
            .collection("notifications")
            .whereEqualTo("userId", getCurrentUserId())
            .get()
            .await()
            .toObjects(com.nipa.healthcareapp.data.models.Notification::class.java)

        // Update local database
        database.notificationDao().insertAll(remoteNotifications)
        
        // Update offline data cache
        offlineData["notifications"] = remoteNotifications
    }

    private suspend fun syncClientHistory() {
        val localHistory = database.clientHistoryDao().getAll()
        val remoteHistory = firestore
            .collection("client_history")
            .whereEqualTo("providerId", getCurrentUserId())
            .get()
            .await()
            .toObjects(com.nipa.healthcareapp.data.models.ClientHistoryItem::class.java)

        // Update local database
        database.clientHistoryDao().insertAll(remoteHistory)
        
        // Update offline data cache
        offlineData["client_history"] = remoteHistory
    }

    private fun getCurrentUserId(): String {
        return FirebaseAuth.getInstance().currentUser?.uid ?: ""
    }

    fun getDataSynced(key: String): Any? {
        return offlineData[key]
    }

    fun clearOfflineData() {
        offlineData.clear()
    }
}
