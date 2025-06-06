package com.nipa.healthcareapp;

import com.google.firebase.Timestamp;

public class NotificationUI {
    private String title;
    private String message;
    private Timestamp timestamp;

    // Default constructor
    public NotificationUI() {
        this.title = "";
        this.message = "";
        this.timestamp = Timestamp.now();
    }

    // Constructor with all fields
    public NotificationUI(String title, String message, Timestamp timestamp) {
        this.title = title;
        this.message = message;
        this.timestamp = timestamp;
    }

    // Getters
    public String getTitle() {
        return title;
    }

    public String getMessage() {
        return message;
    }

    public Timestamp getTimestamp() {
        return timestamp;
    }

    // Setters
    public void setTitle(String title) {
        this.title = title;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setTimestamp(Timestamp timestamp) {
        this.timestamp = timestamp;
    }
}
