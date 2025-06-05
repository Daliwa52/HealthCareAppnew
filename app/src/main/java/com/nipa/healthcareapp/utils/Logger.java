package com.nipa.healthcareapp.utils;

import android.os.Bundle;
import android.util.Log;
import com.google.firebase.analytics.FirebaseAnalytics;
import com.google.firebase.crashlytics.FirebaseCrashlytics;
import java.util.Map;

public final class Logger {

    private static final String APP_TAG = "HealthCareApp"; // Default App Tag
    private static final FirebaseCrashlytics crashlytics = FirebaseCrashlytics.getInstance();
    private static FirebaseAnalytics analytics;

    // Private constructor to prevent instantiation
    private Logger() {}

    public static void initAnalytics(FirebaseAnalytics analyticsInstance) {
        Logger.analytics = analyticsInstance;
    }

    public static void d(String tag, String message) {
        Log.d(APP_TAG, tag + ": " + message);
    }

    public static void i(String tag, String message) {
        Log.i(APP_TAG, tag + ": " + message);
    }

    public static void w(String tag, String message) {
        Log.w(APP_TAG, tag + ": " + message);
        crashlytics.log(APP_TAG + " - " + tag + ": " + message); // Log to Crashlytics with full context
    }

    public static void w(String tag, String message, Throwable throwable) {
        Log.w(APP_TAG, tag + ": " + message, throwable);
        crashlytics.log(APP_TAG + " - " + tag + ": " + message); // Log to Crashlytics
        if (throwable != null) { // Ensure throwable is passed to Crashlytics if present
            crashlytics.recordException(throwable);
        }
    }

    public static void e(String tag, String message) {
        Log.e(APP_TAG, tag + ": " + message);
        crashlytics.log(APP_TAG + " - " + tag + ": " + message); // Log to Crashlytics
    }

    public static void e(String tag, String message, Throwable throwable) {
        Log.e(APP_TAG, tag + ": " + message, throwable);
        crashlytics.log(APP_TAG + " - " + tag + ": " + message); // Log to Crashlytics
        if (throwable != null) {
            crashlytics.recordException(throwable);
        } else {
            // Optionally log a generic exception if message indicates an error but no throwable is passed
            // crashlytics.recordException(new RuntimeException(APP_TAG + " - " + tag + ": " + message));
        }
    }

    public static void trackEvent(String eventName, Map<String, String> params) {
        if (analytics != null) {
            Bundle bundle = new Bundle();
            if (params != null) {
                for (Map.Entry<String, String> entry : params.entrySet()) {
                    bundle.putString(entry.getKey(), entry.getValue());
                }
            }
            analytics.logEvent(eventName, bundle);
            Log.d(APP_TAG, "Analytics event tracked: " + eventName);
        } else {
            Log.w(APP_TAG, "FirebaseAnalytics not initialized. Cannot track event: " + eventName);
        }
    }
}
