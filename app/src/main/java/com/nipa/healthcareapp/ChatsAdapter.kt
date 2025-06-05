package com.nipa.healthcareapp

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.google.firebase.auth.FirebaseAuth
import com.nipa.healthcareapp.data.models.Chat
import java.text.SimpleDateFormat
import java.util.*

class ChatsAdapter : ListAdapter<Chat, ChatsAdapter.ChatViewHolder>(ChatDiffCallback()) {
    private val auth = FirebaseAuth.getInstance()
    private val currentUserId = auth.currentUser?.uid ?: ""
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ChatViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_chat, parent, false)
        return ChatViewHolder(view)
    }

    override fun onBindViewHolder(holder: ChatViewHolder, position: Int) {
        val chat = getItem(position)
        holder.bind(chat, currentUserId)
    }

    class ChatViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvChatName: TextView = itemView.findViewById(R.id.tvChatName)
        private val tvLastMessage: TextView = itemView.findViewById(R.id.tvLastMessage)
        private val tvLastMessageTime: TextView = itemView.findViewById(R.id.tvLastMessageTime)
        private val tvUnreadCount: TextView = itemView.findViewById(R.id.tvUnreadCount)
        
        fun bind(chat: Chat, currentUserId: String) {
            // Set participant name (other than current user)
            val otherParticipant = chat.participants.firstOrNull { it != currentUserId } ?: ""
            tvChatName.text = otherParticipant
            
            // Set last message
            tvLastMessage.text = chat.lastMessage
            
            // Set time
            tvLastMessageTime.text = chat.lastMessageTime
            
            // Set unread count
            if (chat.unreadCount > 0) {
                tvUnreadCount.visibility = View.VISIBLE
                tvUnreadCount.text = chat.unreadCount.toString()
            } else {
                tvUnreadCount.visibility = View.GONE
            }
            
            // Set click listener
            itemView.setOnClickListener {
                // Handle chat item click - open chat details
            }
        }
    }
}

class ChatDiffCallback : DiffUtil.ItemCallback<Chat>() {
    override fun areItemsTheSame(oldItem: Chat, newItem: Chat): Boolean {
        return oldItem.id == newItem.id
    }

    override fun areContentsTheSame(oldItem: Chat, newItem: Chat): Boolean {
        return oldItem == newItem
    }
}
