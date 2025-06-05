package com.nipa.healthcareapp.data.models;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;
// import androidx.room.TypeConverters; // Potentially needed for Timestamp

import com.google.firebase.Timestamp;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

@Entity(tableName = "notification")
public class Notification {

    @PrimaryKey
    @NonNull
    private String id;

    private String title;
    private String message;
    private Timestamp timestamp; // Ensure TypeConverter for Timestamp is set up for Room
    private String userId;
    private boolean read;
    private NotificationType type; // Ensure TypeConverter for NotificationType is set up for Room (or it's stored as String)
    private boolean synced;

    // Default constructor
    public Notification() {
        this.id = UUID.randomUUID().toString();
        this.timestamp = Timestamp.now();
        this.read = false;
        this.type = NotificationType.GENERAL;
        this.synced = true;
        // title, message, userId will be null/default
    }

    // Constructor with all fields
    public Notification(@NonNull String id, String title, String message, Timestamp timestamp,
                        String userId, boolean read, NotificationType type, boolean synced) {
        this.id = id;
        this.title = title;
        this.message = message;
        this.timestamp = timestamp != null ? timestamp : Timestamp.now(); // Default if null
        this.userId = userId;
        this.read = read;
        this.type = type != null ? type : NotificationType.GENERAL; // Default if null
        this.synced = synced;
    }

    // Getters
    @NonNull
    public String getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getMessage() {
        return message;
    }

    public Timestamp getTimestamp() {
        return timestamp;
    }

    public String getUserId() {
        return userId;
    }

    public boolean isRead() {
        return read;
    }

    public NotificationType getType() {
        return type;
    }

    public boolean isSynced() {
        return synced;
    }

    // Setters
    public void setId(@NonNull String id) {
        this.id = id;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setTimestamp(Timestamp timestamp) {
        this.timestamp = timestamp;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public void setRead(boolean read) {
        this.read = read;
    }

    public void setType(NotificationType type) {
        this.type = type;
    }

    public void setSynced(boolean synced) {
        this.synced = synced;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Notification that = (Notification) o;
        return read == that.read &&
               synced == that.synced &&
               id.equals(that.id) && // @NonNull
               Objects.equals(title, that.title) &&
               Objects.equals(message, that.message) &&
               Objects.equals(timestamp, that.timestamp) &&
               Objects.equals(userId, that.userId) &&
               type == that.type;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, title, message, timestamp, userId, read, type, synced);
    }

    @Override
    public String toString() {
        return "Notification{" +
               "id='" + id + '\'' +
               ", title='" + title + '\'' +
               ", message='" + message + '\'' +
               ", timestamp=" + timestamp +
               ", userId='" + userId + '\'' +
               ", read=" + read +
               ", type=" + type +
               ", synced=" + synced +
               '}';
    }

    public static List<String> validate(Notification notification) {
        List<String> errors = new ArrayList<>();
        // ... validation logic ...
        // Example:
        // if (notification.getTitle() == null || notification.getTitle().trim().isEmpty()) {
        //     errors.add("Notification title cannot be empty.");
        // }
        // if (notification.getMessage() == null || notification.getMessage().trim().isEmpty()) {
        //     errors.add("Notification message cannot be empty.");
        // }
        // if (notification.getUserId() == null || notification.getUserId().trim().isEmpty()) {
        //     errors.add("User ID cannot be empty for notification.");
        // }
        return errors;
    }
}
