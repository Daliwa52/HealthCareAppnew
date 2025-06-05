package com.nipa.healthcareapp

import com.google.firebase.Timestamp

data class Notification(
    val title: String,
    val message: String,
    val timestamp: Timestamp
)
