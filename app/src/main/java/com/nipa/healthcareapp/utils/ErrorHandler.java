package com.nipa.healthcareapp.utils;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.firebase.crashlytics.FirebaseCrashlytics;
import java.io.PrintWriter;
import java.io.StringWriter;

public class ErrorHandler {

    private final Context context;
    private final FirebaseCrashlytics crashlytics;

    public ErrorHandler(Context context) {
        // Using application context can help prevent leaks if original context is an Activity
        this.context = context.getApplicationContext();
        this.crashlytics = FirebaseCrashlytics.getInstance();
    }

    // Main error handling method, message parameter is optional
    public void handleError(Throwable throwable, String customMessage) {
        // Determine the message to show
        final String displayMessage;
        if (customMessage != null && !customMessage.isEmpty()) {
            displayMessage = customMessage;
        } else if (throwable != null && throwable.getMessage() != null && !throwable.getMessage().isEmpty()) {
            displayMessage = throwable.getMessage();
        } else {
            displayMessage = "An unexpected error occurred.";
        }

        // Ensure UI operations (dialog) are on the main thread
        new Handler(Looper.getMainLooper()).post(() -> {
            if (context != null) {
                new MaterialAlertDialogBuilder(context)
                        .setTitle("Error")
                        .setMessage(displayMessage)
                        .setPositiveButton(android.R.string.ok, (dialog, which) -> dialog.dismiss())
                        .show();
            } else {
                // Fallback logging if context is somehow not available
                System.err.println("ErrorHandler: Context was null. Cannot show dialog. Message: " + displayMessage);
            }

            // Log to Crashlytics after attempting to notify user
            // Ensure throwable is not null before recording
            if (throwable != null) {
                StringWriter sw = new StringWriter();
                throwable.printStackTrace(new PrintWriter(sw));
                String stackTrace = sw.toString();

                crashlytics.recordException(throwable); // Records the exception object
                crashlytics.log(stackTrace); // Logs the raw stack trace string, as in Kotlin
            } else if (customMessage != null) {
                // If no throwable, but there's a custom message, log that as a non-fatal event/message
                crashlytics.log("Handled error with custom message only: " + customMessage);
            }
        });
    }

    // Overload for just a throwable, derives message from throwable
    public void handleError(Throwable throwable) {
        handleError(throwable, null); // Pass null for customMessage
    }

    public void showNetworkError() {
        handleError(new Exception("No internet connection available. Please check your connection and try again."));
    }

    public void showAuthenticationError() {
        handleError(new Exception("Authentication failed. Please try again."));
    }

    public void showPermissionError(String permission) {
        handleError(new Exception("Permission denied: " + permission + ". Please grant the necessary permissions in app settings."));
    }
}
