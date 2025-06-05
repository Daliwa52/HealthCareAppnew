package com.nipa.healthcareapp.services

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.nipa.healthcareapp.utils.Logger

/**
 * Handles Firebase Cloud Messaging token refresh events
 * Note: FirebaseInstanceIdService is deprecated, using FirebaseMessagingService instead
 */
class MyFirebaseInstanceIDService : FirebaseMessagingService() {

    private val TAG = "MyFirebaseInstanceIDService"

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Called when the token is refreshed
        Log.d(TAG, "New token: $token")
        // Send token to your server
    }
}
