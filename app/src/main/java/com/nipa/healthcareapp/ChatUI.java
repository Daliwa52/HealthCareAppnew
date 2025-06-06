package com.nipa.healthcareapp;

import com.google.firebase.Timestamp;

public class ChatUI {
    private String id;
    private String name;
    private String lastMessage;
    private Timestamp timestamp;
    private int unreadCount;

    // Default constructor
    public ChatUI() {
        this.id = "";
        this.name = "";
        this.lastMessage = "";
        this.timestamp = Timestamp.now();
        this.unreadCount = 0;
    }

    // Constructor with all fields
    public ChatUI(String id, String name, String lastMessage, Timestamp timestamp, int unreadCount) {
        this.id = id;
        this.name = name;
        this.lastMessage = lastMessage;
        this.timestamp = timestamp;
        this.unreadCount = unreadCount;
    }

    // Getters
    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getLastMessage() {
        return lastMessage;
    }

    public Timestamp getTimestamp() {
        return timestamp;
    }

    public int getUnreadCount() {
        return unreadCount;
    }

    // Setters
    public void setId(String id) {
        this.id = id;
    }

    public void setName(String name) {
        this.name = name;
    }

    public void setLastMessage(String lastMessage) {
        this.lastMessage = lastMessage;
    }

    public void setTimestamp(Timestamp timestamp) {
        this.timestamp = timestamp;
    }

    public void setUnreadCount(int unreadCount) {
        this.unreadCount = unreadCount;
    }
}
