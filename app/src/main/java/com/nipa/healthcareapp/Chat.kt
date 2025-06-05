package com.nipa.healthcareapp

data class Chat(
    val id: String = "",
    val name: String = "",
    val lastMessage: String = "",
    val timestamp: com.google.firebase.Timestamp = com.google.firebase.Timestamp.now(),
    val unreadCount: Int = 0
)
