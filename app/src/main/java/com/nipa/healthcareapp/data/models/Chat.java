package com.nipa.healthcareapp.data.models;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class Chat {
    private String id;
    private List<String> participants;
    private String lastMessage;
    private String lastMessageTime;
    private int unreadCount;
    private String type;

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

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Chat chat = (Chat) o;
        return unreadCount == chat.unreadCount &&
               Objects.equals(id, chat.id) &&
               Objects.equals(participants, chat.participants) &&
               Objects.equals(lastMessage, chat.lastMessage) &&
               Objects.equals(lastMessageTime, chat.lastMessageTime) &&
               Objects.equals(type, chat.type);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, participants, lastMessage, lastMessageTime, unreadCount, type);
    }

    @Override
    public String toString() {
        return "Chat{" +
               "id='" + id + '\'' +
               ", participants=" + participants +
               ", lastMessage='" + lastMessage + '\'' +
               ", lastMessageTime='" + lastMessageTime + '\'' +
               ", unreadCount=" + unreadCount +
               ", type='" + type + '\'' +
               '}';
    }
}
