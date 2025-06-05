package com.nipa.healthcareapp.firebase

import android.app.Application
import com.google.firebase.FirebaseApp
import com.google.firebase.crashlytics.FirebaseCrashlytics
import com.google.firebase.ktx.Firebase
import com.google.firebase.perf.FirebasePerformance
import com.google.firebase.perf.metrics.Trace

class FirebaseInitializer : Application() {
    override fun onCreate() {
        super.onCreate()
        
        // Initialize Firebase
        FirebaseApp.initializeApp(this)
        
        // Initialize Crashlytics
        FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(true)
        
        // Initialize Performance Monitoring
        val perf = FirebasePerformance.getInstance()
        
        // Create a trace for app startup - using the getInstance().newTrace() method
        val trace = perf.newTrace("app_startup")
        trace.start()
        
        // Add any additional Firebase initialization here
    }
}
