package com.nipa.healthcareapp.data.models

data class Chat(
    val id: String = "",
    val participants: List<String> = emptyList(),
    val lastMessage: String = "",
    val lastMessageTime: String = "",
    val unreadCount: Int = 0,
    val type: String = "" // "patient" or "provider"
)
