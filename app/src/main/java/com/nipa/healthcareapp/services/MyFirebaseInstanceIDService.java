package com.nipa.healthcareapp.services;

import android.util.Log;
import androidx.annotation.NonNull; // For @NonNull on token parameter
import com.google.firebase.messaging.FirebaseMessagingService;

public class MyFirebaseInstanceIDService extends FirebaseMessagingService {

    private static final String TAG = "MyFirebaseInstanceIDService"; // Made static final

    @Override
    public void onNewToken(@NonNull String token) { // Added @NonNull
        super.onNewToken(token);
        Log.d(TAG, "New token: " + token);
        // Send token to your server
    }
}
