package com.nipa.healthcareapp.services

import android.content.Context
import android.util.Log
import androidx.work.*
import com.nipa.healthcareapp.services.DataSyncService
import java.lang.Exception
import java.util.concurrent.TimeUnit

class DataSyncWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    companion object {
        private const val WORK_NAME = "DataSyncWorker"
        private const val TAG = "DataSyncWorker"

        fun startSync(context: Context) {
            val workManager = WorkManager.getInstance(context)
            
            // Create a work request with constraints
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val syncRequest = OneTimeWorkRequestBuilder<DataSyncWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    15 * 60 * 1000L, // 15 minutes in milliseconds
                    TimeUnit.MILLISECONDS
                )
                .build()

            // Enqueue the work
            workManager.enqueueUniqueWork(
                WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                syncRequest
            )
        }

        fun setupPeriodicSync(context: Context) {
            val workManager = WorkManager.getInstance(context)
            
            // Create periodic work request
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val syncRequest = PeriodicWorkRequestBuilder<DataSyncWorker>(
                15, // Run every 15 minutes
                TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    15 * 60 * 1000L, // 15 minutes in milliseconds
                    TimeUnit.MILLISECONDS
                )
                .build()

            // Enqueue the work
            workManager.enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.REPLACE,
                syncRequest
            )
        }
    }

    override suspend fun doWork(): Result {
        return try {
            // Just perform the sync work directly in this worker
            Log.d(TAG, "Starting data synchronization from worker")
            
            // Your sync logic would go here
            // For example, accessing Firestore and local database
            
            Log.d(TAG, "Data synchronization completed successfully")
            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Error during data synchronization", e)
            Result.retry()
        }
    }
}
