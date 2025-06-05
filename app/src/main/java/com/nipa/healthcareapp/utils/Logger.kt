package com.nipa.healthcareapp.utils

import android.util.Log
import com.google.firebase.crashlytics.FirebaseCrashlytics
import com.google.firebase.analytics.FirebaseAnalytics
import kotlin.properties.ReadOnlyProperty
import kotlin.reflect.KProperty

class Logger {
    companion object {
        private const val TAG = "HealthCareApp"
        private val crashlytics = FirebaseCrashlytics.getInstance()
        private var analytics: FirebaseAnalytics? = null
        
        fun initAnalytics(analytics: FirebaseAnalytics) {
            this.analytics = analytics
        }

        fun d(tag: String, message: String) {
            Log.d(TAG, "$tag: $message")
        }

        fun i(tag: String, message: String) {
            Log.i(TAG, "$tag: $message")
        }

        fun w(tag: String, message: String) {
            Log.w(TAG, "$tag: $message")
            crashlytics.log("$tag: $message")
        }

        fun e(tag: String, message: String, throwable: Throwable? = null) {
            Log.e(TAG, "$tag: $message", throwable)
            crashlytics.log("$tag: $message")
            throwable?.let { crashlytics.recordException(it) }
        }

        fun trackEvent(eventName: String, params: Map<String, String> = emptyMap()) {
            analytics?.let {
                val bundle = android.os.Bundle()
                params.forEach { (key, value) -> bundle.putString(key, value) }
                it.logEvent(eventName, bundle)
            }
        }
    }
}

// Extension property for logging
val Any.logger: Logger
    get() = Logger()

// Delegated property for logging
fun <T : Any> T.log(tag: String = this::class.java.simpleName): ReadOnlyProperty<T, Logger> {
    return object : ReadOnlyProperty<T, Logger> {
        override fun getValue(thisRef: T, property: KProperty<*>): Logger {
            return Logger()
        }
    }
}
