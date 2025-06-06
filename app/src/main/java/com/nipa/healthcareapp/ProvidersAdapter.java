package com.nipa.healthcareapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import com.google.android.material.card.MaterialCardView;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.nipa.healthcareapp.data.models.Provider; // Using the Java version

// Removed Locale import as simple concatenation will be used for rating
import java.util.Objects;

public class ProvidersAdapter extends ListAdapter<Provider, ProvidersAdapter.ProviderViewHolder> {

    public ProvidersAdapter() {
        super(new ProviderDiffCallback());
    }

    @NonNull
    @Override
    public ProviderViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_provider, parent, false);
        return new ProviderViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ProviderViewHolder holder, int position) {
        Provider provider = getItem(position);
        if (provider != null) {
            holder.bind(provider);
        }
    }

    public static class ProviderViewHolder extends RecyclerView.ViewHolder {
        private final MaterialCardView providerCardView;
        private final TextView tvProviderName;
        private final TextView tvProviderSpecialty;
        private final TextView tvProviderRating;

        public ProviderViewHolder(@NonNull View itemView) {
            super(itemView);
            providerCardView = itemView.findViewById(R.id.providerCard);
            tvProviderName = itemView.findViewById(R.id.tvProviderName);
            tvProviderSpecialty = itemView.findViewById(R.id.tvProviderSpecialty);
            tvProviderRating = itemView.findViewById(R.id.tvRating); // Corrected ID from Kotlin source
        }

        public void bind(final Provider provider) {
            tvProviderName.setText(provider.getName());
            tvProviderSpecialty.setText(provider.getSpecialty());

            // Match Kotlin's rating text format: "${provider.rating}/5"
            if (tvProviderRating != null) {
                tvProviderRating.setText(provider.getRating() + "/5");
            }

            // No click listener in Kotlin version's bind method
            // itemView.setOnClickListener(v -> { /* ... */ });
        }
    }

    private static class ProviderDiffCallback extends DiffUtil.ItemCallback<Provider> {
        @Override
        public boolean areItemsTheSame(@NonNull Provider oldItem, @NonNull Provider newItem) {
            return oldItem.getId().equals(newItem.getId());
        }

        @Override
        public boolean areContentsTheSame(@NonNull Provider oldItem, @NonNull Provider newItem) {
            return oldItem.getId().equals(newItem.getId()) &&
                   Objects.equals(oldItem.getName(), newItem.getName()) &&
                   Objects.equals(oldItem.getEmail(), newItem.getEmail()) &&
                   Objects.equals(oldItem.getSpecialty(), newItem.getSpecialty()) &&
                   Float.compare(oldItem.getRating(), newItem.getRating()) == 0 &&
                   Objects.equals(oldItem.getProfilePicture(), newItem.getProfilePicture()) &&
                   Objects.equals(oldItem.getAvailability(), newItem.getAvailability());
        }
    }
}
