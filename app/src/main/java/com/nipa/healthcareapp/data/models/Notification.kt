package com.nipa.healthcareapp.data.models

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.google.firebase.Timestamp
import java.time.Instant
import java.util.UUID

@Entity(tableName = "notification")
@kotlinx.serialization.Serializable
data class Notification(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    val title: String,
    val message: String,
    @kotlinx.serialization.Contextual
    val timestamp: Timestamp = Timestamp.now(),
    val userId: String,
    val read: Boolean = false,
    val type: NotificationType = NotificationType.GENERAL,
    var synced: Boolean = true
) {
    companion object {
        fun validate(notification: Notification): List<String> {
            val errors = mutableListOf<String>()
            
            if (notification.title.isBlank()) errors.add("Title is required")
            if (notification.message.isBlank()) errors.add("Message is required")
            if (notification.userId.isBlank()) errors.add("User ID is required")
            if (notification.type == NotificationType.UNKNOWN) errors.add("Invalid notification type")
            
            return errors
        }
    }
}

enum class NotificationType {
    GENERAL,
    APPOINTMENT,
    REMINDER,
    SYSTEM,
    UNKNOWN
}
