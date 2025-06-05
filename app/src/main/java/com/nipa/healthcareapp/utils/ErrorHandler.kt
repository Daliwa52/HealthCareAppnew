package com.nipa.healthcareapp.utils

import android.content.Context
import android.widget.Toast
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.firebase.crashlytics.FirebaseCrashlytics
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.PrintWriter
import java.io.StringWriter

class ErrorHandler(private val context: Context) {
    private val crashlytics = FirebaseCrashlytics.getInstance()
    private val coroutineScope = CoroutineScope(Dispatchers.Main)

    fun handleError(throwable: Throwable, message: String? = null) {
        coroutineScope.launch {
            val errorMessage = message ?: throwable.message ?: "An unexpected error occurred"
            
            // Show error to user
            MaterialAlertDialogBuilder(context)
                .setTitle("Error")
                .setMessage(errorMessage)
                .setPositiveButton("OK") { _, _ -> }
                .show()

            // Log to Crashlytics
            val stackTrace = StringWriter().apply {
                throwable.printStackTrace(PrintWriter(this))
            }.toString()

            crashlytics.recordException(throwable)
            crashlytics.log(stackTrace)
        }
    }

    fun showNetworkError() {
        handleError(Exception("No internet connection available"))
    }

    fun showAuthenticationError() {
        handleError(Exception("Authentication failed. Please try again."))
    }

    fun showPermissionError(permission: String) {
        handleError(Exception("Permission denied: $permission"))
    }
}
