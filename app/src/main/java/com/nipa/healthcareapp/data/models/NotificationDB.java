package com.nipa.healthcareapp.data.models;

import androidx.room.Entity;
import androidx.room.PrimaryKey;
// import androidx.room.TypeConverters; // Potentially for Timestamp and NotificationTypeDB
import androidx.annotation.NonNull;

import com.google.firebase.Timestamp; // For Timestamp field
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import android.text.TextUtils; // For validation

// Enum for Notification Type
enum NotificationTypeDB {
    GENERAL,
    APPOINTMENT,
    REMINDER,
    SYSTEM,
    UNKNOWN
}

@Entity(tableName = "notification")
// Example: @TypeConverters({TimestampConverter.class, NotificationTypeConverter.class})
public class NotificationDB {

    @PrimaryKey
    @NonNull
    private String id;

    @NonNull
    private String title;

    @NonNull
    private String message;

    @NonNull // Assuming timestamp should always be present
    // Room might need a TypeConverter for com.google.firebase.Timestamp
    private Timestamp timestamp;

    @NonNull
    private String userId;

    private boolean read;

    @NonNull // Assuming type should always be present
    // Room might need a TypeConverter for NotificationTypeDB enum
    private NotificationTypeDB type;

    private boolean synced;

    // Default constructor for Room
    public NotificationDB() {
        this.id = UUID.randomUUID().toString();
        this.timestamp = Timestamp.now();
        this.read = false;
        this.type = NotificationTypeDB.GENERAL;
        this.synced = true;
        // title, message, userId must be set via setters or parameterized constructor
    }

    // Parameterized constructor for creating instances with specific values
    public NotificationDB(@NonNull String title, @NonNull String message, @NonNull Timestamp timestamp,
                          @NonNull String userId, boolean read, @NonNull NotificationTypeDB type, boolean synced) {
        this.id = UUID.randomUUID().toString(); // Generate new ID
        this.title = title;
        this.message = message;
        this.timestamp = timestamp;
        this.userId = userId;
        this.read = read;
        this.type = type;
        this.synced = synced;
    }

    // Constructor including ID (e.g., when creating from existing data)
    public NotificationDB(@NonNull String id, @NonNull String title, @NonNull String message, @NonNull Timestamp timestamp,
                          @NonNull String userId, boolean read, @NonNull NotificationTypeDB type, boolean synced) {
        this.id = id;
        this.title = title;
        this.message = message;
        this.timestamp = timestamp;
        this.userId = userId;
        this.read = read;
        this.type = type;
        this.synced = synced;
    }

    // Getters
    @NonNull
    public String getId() { return id; }
    @NonNull
    public String getTitle() { return title; }
    @NonNull
    public String getMessage() { return message; }
    @NonNull
    public Timestamp getTimestamp() { return timestamp; }
    @NonNull
    public String getUserId() { return userId; }
    public boolean isRead() { return read; }
    @NonNull
    public NotificationTypeDB getType() { return type; }
    public boolean isSynced() { return synced; }

    // Setters
    public void setId(@NonNull String id) { this.id = id; }
    public void setTitle(@NonNull String title) { this.title = title; }
    public void setMessage(@NonNull String message) { this.message = message; }
    public void setTimestamp(@NonNull Timestamp timestamp) { this.timestamp = timestamp; }
    public void setUserId(@NonNull String userId) { this.userId = userId; }
    public void setRead(boolean read) { this.read = read; }
    public void setType(@NonNull NotificationTypeDB type) { this.type = type; }
    public void setSynced(boolean synced) { this.synced = synced; }

    // Static validation method (placeholder for actual logic)
    public static List<String> validate(NotificationDB notification) {
        List<String> errors = new ArrayList<>();
        if (notification == null) {
            errors.add("NotificationDB cannot be null.");
            return errors;
        }
        if (TextUtils.isEmpty(notification.getTitle())) {
            errors.add("Title cannot be empty.");
        }
        if (TextUtils.isEmpty(notification.getMessage())) {
            errors.add("Message cannot be empty.");
        }
        if (notification.getTimestamp() == null) {
            errors.add("Timestamp cannot be null.");
        }
        if (TextUtils.isEmpty(notification.getUserId())) {
            errors.add("User ID cannot be empty.");
        }
        if (notification.getType() == null) {
            errors.add("Notification type cannot be null.");
        }
        // Add more specific validation logic if needed
        return errors;
    }
}
