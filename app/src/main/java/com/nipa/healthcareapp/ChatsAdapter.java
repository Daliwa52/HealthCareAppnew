package com.nipa.healthcareapp;

import android.content.Context;
// import android.content.Intent; // Removed as click listener is now minimal
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.nipa.healthcareapp.data.models.Chat;

// Removed SimpleDateFormat, Date, Locale as lastMessageTime is used directly as String
import java.util.Objects;

public class ChatsAdapter extends ListAdapter<Chat, ChatsAdapter.ChatViewHolder> {

    private final String currentUserId;
    // Context can be kept if future click handling needs it, but direct usage removed for now.
    // private final Context context;

    // Constructor matching Kotlin (no explicit context pass-through for click listener)
    public ChatsAdapter() {
        super(new ChatDiffCallback());
        // this.context = context; // Only if needed for click listener defined by interface
        FirebaseUser currentUser = FirebaseAuth.getInstance().getCurrentUser();
        this.currentUserId = (currentUser != null) ? currentUser.getUid() : "";
    }

    @NonNull
    @Override
    public ChatViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_chat, parent, false);
        return new ChatViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ChatViewHolder holder, int position) {
        Chat chat = getItem(position);
        if (chat != null) {
            holder.bind(chat, currentUserId);
        }
    }

    static class ChatViewHolder extends RecyclerView.ViewHolder {
        private final TextView tvChatName;
        private final TextView tvLastMessage;
        private final TextView tvTimestamp; // Renamed from tvLastMessageTime to match item_chat.xml more likely
        private final TextView tvUnreadCount;

        public ChatViewHolder(@NonNull View itemView) {
            super(itemView);
            tvChatName = itemView.findViewById(R.id.tvChatName);
            tvLastMessage = itemView.findViewById(R.id.tvLastMessage);
            tvTimestamp = itemView.findViewById(R.id.tvLastMessageTime); // Assuming this ID from Kotlin
            tvUnreadCount = itemView.findViewById(R.id.tvUnreadCount);
        }

        public void bind(Chat chat, String currentUserId) {
            String otherParticipantDisplay = "Unknown User"; // Default
            if (chat.getParticipants() != null) {
                for (String participantId : chat.getParticipants()) {
                    if (participantId != null && !participantId.equals(currentUserId)) {
                        otherParticipantDisplay = participantId; // Displaying the ID as per Kotlin
                        break;
                    }
                }
            }
            // If participant list is empty or only contains current user (should not happen in a 1-1 chat context)
            // otherParticipantDisplay might remain "Unknown User" or the first ID if logic is adjusted.
            // For a group chat, this logic would need to be different (e.g. group name).
            // The Kotlin code `chat.participants.firstOrNull { it != currentUserId } ?: ""` handles this.
            // Java equivalent:
            final String finalOtherParticipantId = chat.getParticipants() == null ? "" :
                chat.getParticipants().stream()
                    .filter(id -> id != null && !id.equals(currentUserId))
                    .findFirst()
                    .orElse(""); // If no other participant, or list is null, use empty string.

            tvChatName.setText(finalOtherParticipantId.isEmpty() ? "Chat" : finalOtherParticipantId);


            tvLastMessage.setText(chat.getLastMessage());
            tvTimestamp.setText(chat.getLastMessageTime()); // Used directly as String

            if (chat.getUnreadCount() > 0) {
                tvUnreadCount.setVisibility(View.VISIBLE);
                tvUnreadCount.setText(String.valueOf(chat.getUnreadCount()));
            } else {
                tvUnreadCount.setVisibility(View.GONE);
            }

            itemView.setOnClickListener(v -> {
                // Original Kotlin: "// Handle chat item click - open chat details"
                // Minimal action, or use an interface callback to the Activity/Fragment.
                // For now, just logging as a placeholder.
                Log.d("ChatsAdapter", "Clicked on chat item with ID: " + chat.getId());
                // Example of using an interface (if defined and implemented by Activity/Fragment):
                // if (onChatClickListener != null) {
                //    onChatClickListener.onChatClicked(chat);
                // }
            });
        }
    }

    // Interface for click events (optional, if Activity/Fragment handles clicks)
    /*
    public interface OnChatClickListener {
        void onChatClicked(Chat chat);
    }
    private OnChatClickListener onChatClickListener;
    public void setOnChatClickListener(OnChatClickListener listener) {
        this.onChatClickListener = listener;
    }
    */

    static class ChatDiffCallback extends DiffUtil.ItemCallback<Chat> {
        @Override
        public boolean areItemsTheSame(@NonNull Chat oldItem, @NonNull Chat newItem) {
            return oldItem.getId().equals(newItem.getId());
        }

        @Override
        public boolean areContentsTheSame(@NonNull Chat oldItem, @NonNull Chat newItem) {
            // Using Objects.equals for all fields for robustness, as per original Chat.kt (data class implies field equality)
            // and for safety with POJOs that might not have overridden equals().
            return oldItem.getId().equals(newItem.getId()) && // ID is @NonNull
                   Objects.equals(oldItem.getParticipants(), newItem.getParticipants()) &&
                   Objects.equals(oldItem.getLastMessage(), newItem.getLastMessage()) &&
                   Objects.equals(oldItem.getLastMessageTime(), newItem.getLastMessageTime()) &&
                   oldItem.getUnreadCount() == newItem.getUnreadCount() &&
                   Objects.equals(oldItem.getType(), newItem.getType());
        }
    }
}
