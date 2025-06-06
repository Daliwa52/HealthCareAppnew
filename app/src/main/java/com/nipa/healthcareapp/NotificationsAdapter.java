package com.nipa.healthcareapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.nipa.healthcareapp.data.models.NotificationDB;

import com.google.android.material.card.MaterialCardView;
// com.google.firebase.Timestamp is imported by NotificationDB, but Date and SimpleDateFormat are needed here.
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.Objects;

public class NotificationsAdapter extends ListAdapter<NotificationDB, NotificationsAdapter.NotificationViewHolder> {

    public NotificationsAdapter() {
        super(new NotificationDiffCallback());
    }

    @NonNull
    @Override
    public NotificationViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_notification, parent, false);
        return new NotificationViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull NotificationViewHolder holder, int position) {
        NotificationDB notification = getItem(position);
        if (notification != null) {
            holder.bind(notification);
        }
    }

    static class NotificationViewHolder extends RecyclerView.ViewHolder {
        private final MaterialCardView cardView;
        private final TextView tvTitle;
        private final TextView tvMessage;
        private final TextView tvTime;

        public NotificationViewHolder(@NonNull View itemView) {
            super(itemView);
            cardView = itemView.findViewById(R.id.notificationCard); // Corrected ID from Kotlin source
            tvTitle = itemView.findViewById(R.id.tvNotificationTitle);
            tvMessage = itemView.findViewById(R.id.tvNotificationMessage);
            tvTime = itemView.findViewById(R.id.tvNotificationTime);
        }

        public void bind(NotificationDB notification) {
            tvTitle.setText(notification.getTitle());
            tvMessage.setText(notification.getMessage());

            if (notification.getTimestamp() != null) {
                // Formatting Firebase Timestamp to a more readable format
                Date date = notification.getTimestamp().toDate();
                SimpleDateFormat sdf = new SimpleDateFormat("MMM dd, hh:mm a", Locale.getDefault());
                tvTime.setText(sdf.format(date));
            } else {
                tvTime.setText("");
            }

            // itemView.setOnClickListener(v -> { /* Handle item click if needed */ });
        }
    }

    private static class NotificationDiffCallback extends DiffUtil.ItemCallback<NotificationDB> {
        @Override
        public boolean areItemsTheSame(@NonNull NotificationDB oldItem, @NonNull NotificationDB newItem) {
            return oldItem.getId().equals(newItem.getId());
        }

        @Override
        public boolean areContentsTheSame(@NonNull NotificationDB oldItem, @NonNull NotificationDB newItem) {
            return oldItem.getId().equals(newItem.getId()) &&
                   Objects.equals(oldItem.getTitle(), newItem.getTitle()) &&
                   Objects.equals(oldItem.getMessage(), newItem.getMessage()) &&
                   Objects.equals(oldItem.getTimestamp(), newItem.getTimestamp()) &&
                   Objects.equals(oldItem.getUserId(), newItem.getUserId()) &&
                   oldItem.isRead() == newItem.isRead() &&
                   Objects.equals(oldItem.getType(), newItem.getType()) &&
                   oldItem.isSynced() == newItem.isSynced();
        }
    }
}
