package com.nipa.healthcareapp.utils;

import android.os.Bundle; // For FirebaseAnalytics params
import android.util.Log;

import androidx.annotation.Nullable; // For nullable Throwable

import com.google.firebase.analytics.FirebaseAnalytics;
import com.google.firebase.crashlytics.FirebaseCrashlytics;

import java.util.Collections; // For emptyMap
import java.util.Map;

public final class Logger { // Made final with private constructor

    private static final String APP_TAG = "HealthCareApp"; // Renamed from TAG for clarity
    private static final FirebaseCrashlytics crashlytics = FirebaseCrashlytics.getInstance();
    private static FirebaseAnalytics analytics; // Initialized to null

    // Private constructor to prevent instantiation
    private Logger() {}

    public static void initAnalytics(FirebaseAnalytics firebaseAnalytics) {
        analytics = firebaseAnalytics;
    }

    public static void d(String providedTag, String message) {
        Log.d(APP_TAG, providedTag + ": " + message);
    }

    public static void i(String providedTag, String message) {
        String logMsg = providedTag + ": " + message;
        Log.i(APP_TAG, logMsg);
        crashlytics.log("I/" + APP_TAG + "/" + logMsg);
    }

    public static void w(String providedTag, String message) {
        String logMsg = providedTag + ": " + message;
        Log.w(APP_TAG, logMsg);
        crashlytics.log("W/" + APP_TAG + "/" + logMsg);
    }

    // Overload for e(tag, message) without throwable
    public static void e(String providedTag, String message) {
        e(providedTag, message, null);
    }

    public static void e(String providedTag, String message, @Nullable Throwable throwable) {
        String logMsg = providedTag + ": " + message;
        Log.e(APP_TAG, logMsg, throwable);

        String crashlyticsMsg = "E/" + APP_TAG + "/" + logMsg;
        if (throwable != null) {
            crashlyticsMsg += " | Exception: " + throwable.toString(); // Using toString for brevity
            crashlytics.log(crashlyticsMsg);
            crashlytics.recordException(throwable);
        } else {
            crashlytics.log(crashlyticsMsg);
            // Log a non-fatal exception if message indicates an error but no throwable is passed
            // This ensures it appears more prominently in Crashlytics if it's a logged error.
            crashlytics.recordException(new Exception("Logged Error: " + logMsg));
        }
    }

    // Overload for trackEvent(eventName) without params
    public static void trackEvent(String eventName) {
        trackEvent(eventName, Collections.emptyMap());
    }

    public static void trackEvent(String eventName, Map<String, String> params) {
        Map<String, String> safeParams = (params == null) ? Collections.emptyMap() : params;

        if (analytics != null) {
            Bundle bundle = new Bundle();
            for (Map.Entry<String, String> entry : safeParams.entrySet()) {
                bundle.putString(entry.getKey(), entry.getValue());
            }
            analytics.logEvent(eventName, bundle);
            Log.d(APP_TAG, "Event tracked: " + eventName + (!safeParams.isEmpty() ? " with params: " + safeParams : ""));
        } else {
            Log.w(APP_TAG, "FirebaseAnalytics not initialized. Cannot track event: " + eventName);
        }
        // Also log event to Crashlytics for context
        crashlytics.log("Event: " + eventName + (!safeParams.isEmpty() ? " Params: " + safeParams : ""));
    }
}
