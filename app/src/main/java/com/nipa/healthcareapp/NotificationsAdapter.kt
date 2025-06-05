package com.nipa.healthcareapp

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.data.models.Notification
import com.google.android.material.card.MaterialCardView

class NotificationsAdapter : ListAdapter<Notification, NotificationsAdapter.NotificationViewHolder>(NotificationDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): NotificationViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_notification, parent, false)
        return NotificationViewHolder(view)
    }

    override fun onBindViewHolder(holder: NotificationViewHolder, position: Int) {
        val notification = getItem(position)
        holder.bind(notification)
    }

    class NotificationViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val cardView: MaterialCardView = itemView.findViewById(R.id.notificationCard)
        private val titleTextView: TextView = itemView.findViewById(R.id.tvNotificationTitle)
        private val messageTextView: TextView = itemView.findViewById(R.id.tvNotificationMessage)
        private val timeTextView: TextView = itemView.findViewById(R.id.tvNotificationTime)

        fun bind(notification: Notification) {
            titleTextView.text = notification.title
            messageTextView.text = notification.message
            timeTextView.text = notification.timestamp.toDate().toString()
        }
    }

    private class NotificationDiffCallback : DiffUtil.ItemCallback<Notification>() {
        override fun areItemsTheSame(oldItem: Notification, newItem: Notification): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: Notification, newItem: Notification): Boolean {
            return oldItem == newItem
        }
    }
}
