package com.nipa.healthcareapp.utils;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log; // For logging

import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.firebase.crashlytics.FirebaseCrashlytics;
import com.nipa.healthcareapp.R; // Assuming R.string resources for dialog

public class ErrorHandler {

    private static final String TAG = "ErrorHandler"; // For logging
    private final Context context;
    private final FirebaseCrashlytics crashlytics;

    public ErrorHandler(Context context) {
        this.context = context;
        this.crashlytics = FirebaseCrashlytics.getInstance();
    }

    // Overloaded method for convenience, matching Kotlin's default parameter
    public void handleError(Throwable throwable) {
        handleError(throwable, null);
    }

    public void handleError(Throwable throwable, String customMessage) {
        // Log to Crashlytics
        crashlytics.recordException(throwable);
        if (customMessage != null && !customMessage.isEmpty()) {
            crashlytics.log("Custom error message: " + customMessage);
        }
        Log.e(TAG, customMessage != null ? customMessage : "An error occurred", throwable);

        // Ensure UI operations are on the main thread
        new Handler(Looper.getMainLooper()).post(() -> {
            String dialogMessage = customMessage != null ? customMessage : "An unexpected error occurred. Please try again.";
            String dialogTitle = "Error"; // Or use context.getString(R.string.error_title);

            // Check if context is valid (e.g., Activity is not finishing)
            if (context == null) {
                 Log.e(TAG, "Context is null, cannot show error dialog.");
                 return;
            }

            try {
                new MaterialAlertDialogBuilder(context)
                        .setTitle(dialogTitle)
                        .setMessage(dialogMessage + "\n\n" + (throwable != null ? "Details: " + throwable.getMessage() : ""))
                        .setPositiveButton(R.string.ok, (dialog, which) -> { // Assuming R.string.ok exists
                            dialog.dismiss();
                        })
                        .show();
            } catch (Exception dialogException) {
                Log.e(TAG, "Failed to show error dialog", dialogException);
                // Consider a fallback, e.g., a Toast, if the dialog fails
                // Toast.makeText(context, dialogMessage, Toast.LENGTH_LONG).show();
            }
        });
    }

    // Example of another utility method that might exist in such a class
    public void logWarning(String message) {
        Log.w(TAG, message);
        crashlytics.log("Warning: " + message);
    }
}
