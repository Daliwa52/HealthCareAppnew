package com.nipa.healthcareapp.data.models;

import java.util.ArrayList;
import java.util.List;

public class Chat {
    private String id;
    private List<String> participants;
    private String lastMessage;
    private String lastMessageTime;
    private int unreadCount;
    private String type; // "patient" or "provider"

    // Default constructor
    public Chat() {
        this.id = "";
        this.participants = new ArrayList<>();
        this.lastMessage = "";
        this.lastMessageTime = "";
        this.unreadCount = 0;
        this.type = "";
    }

    // Constructor with all fields
    public Chat(String id, List<String> participants, String lastMessage, String lastMessageTime, int unreadCount, String type) {
        this.id = id;
        this.participants = participants;
        this.lastMessage = lastMessage;
        this.lastMessageTime = lastMessageTime;
        this.unreadCount = unreadCount;
        this.type = type;
    }

    // Getters
    public String getId() {
        return id;
    }

    public List<String> getParticipants() {
        return participants;
    }

    public String getLastMessage() {
        return lastMessage;
    }

    public String getLastMessageTime() {
        return lastMessageTime;
    }

    public int getUnreadCount() {
        return unreadCount;
    }

    public String getType() {
        return type;
    }

    // Setters
    public void setId(String id) {
        this.id = id;
    }

    public void setParticipants(List<String> participants) {
        this.participants = participants;
    }

    public void setLastMessage(String lastMessage) {
        this.lastMessage = lastMessage;
    }

    public void setLastMessageTime(String lastMessageTime) {
        this.lastMessageTime = lastMessageTime;
    }

    public void setUnreadCount(int unreadCount) {
        this.unreadCount = unreadCount;
    }

    public void setType(String type) {
        this.type = type;
    }
}
