package com.nipa.healthcareapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.nipa.healthcareapp.data.models.ClientHistoryItemDB;
// Assuming ConsultationTypeDB is an enum within ClientHistoryItemDB or accessible
// import com.nipa.healthcareapp.data.models.ConsultationTypeDB;

import com.google.android.material.card.MaterialCardView;

import java.time.format.DateTimeFormatter; // For formatting LocalDate
import java.util.Objects;

public class ClientHistoryAdapter extends ListAdapter<ClientHistoryItemDB, ClientHistoryAdapter.HistoryViewHolder> {

    public ClientHistoryAdapter() {
        super(new HistoryDiffCallback());
    }

    @NonNull
    @Override
    public HistoryViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_client_history, parent, false);
        return new HistoryViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull HistoryViewHolder holder, int position) {
        ClientHistoryItemDB historyItem = getItem(position);
        if (historyItem != null) {
            holder.bind(historyItem);
        }
    }

    static class HistoryViewHolder extends RecyclerView.ViewHolder {
        private final MaterialCardView cardView; // Corrected ID will be used
        private final TextView tvPatientName;
        private final TextView tvConsultationType;
        private final TextView tvConsultationDate;
        private final TextView tvNotes;

        public HistoryViewHolder(@NonNull View itemView) {
            super(itemView);
            cardView = itemView.findViewById(R.id.historyCard); // Corrected ID from Kotlin source
            tvPatientName = itemView.findViewById(R.id.tvPatientName);
            tvConsultationType = itemView.findViewById(R.id.tvConsultationType);
            tvConsultationDate = itemView.findViewById(R.id.tvConsultationDate);
            tvNotes = itemView.findViewById(R.id.tvNotes);
        }

        public void bind(ClientHistoryItemDB historyItem) {
            tvPatientName.setText(historyItem.getPatientName());

            if (historyItem.getConsultationType() != null) {
                tvConsultationType.setText(historyItem.getConsultationType().toString());
            } else {
                tvConsultationType.setText("N/A");
            }

            if (historyItem.getConsultationDate() != null) {
                // Formatting LocalDate for better readability than default toString()
                DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMM dd, yyyy");
                tvConsultationDate.setText(historyItem.getConsultationDate().format(formatter));
            } else {
                tvConsultationDate.setText("N/A");
            }

            // Show notes if available, hide otherwise
            if (historyItem.getNotes() != null && !historyItem.getNotes().isEmpty()) {
                tvNotes.setText(historyItem.getNotes());
                tvNotes.setVisibility(View.VISIBLE);
            } else {
                tvNotes.setVisibility(View.GONE);
            }

            // itemView.setOnClickListener(v -> { /* Handle item click if needed */ });
        }
    }

    private static class HistoryDiffCallback extends DiffUtil.ItemCallback<ClientHistoryItemDB> {
        @Override
        public boolean areItemsTheSame(@NonNull ClientHistoryItemDB oldItem, @NonNull ClientHistoryItemDB newItem) {
            return oldItem.getId().equals(newItem.getId());
        }

        @Override
        public boolean areContentsTheSame(@NonNull ClientHistoryItemDB oldItem, @NonNull ClientHistoryItemDB newItem) {
            return oldItem.getId().equals(newItem.getId()) &&
                   Objects.equals(oldItem.getProviderId(), newItem.getProviderId()) &&
                   Objects.equals(oldItem.getPatientId(), newItem.getPatientId()) &&
                   Objects.equals(oldItem.getPatientName(), newItem.getPatientName()) &&
                   Objects.equals(oldItem.getConsultationDate(), newItem.getConsultationDate()) &&
                   Objects.equals(oldItem.getConsultationType(), newItem.getConsultationType()) &&
                   Objects.equals(oldItem.getNotes(), newItem.getNotes()) &&
                   Objects.equals(oldItem.getAttachments(), newItem.getAttachments()) &&
                   oldItem.isSynced() == newItem.isSynced();
        }
    }
}
