package com.nipa.healthcareapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.cardview.widget.CardView;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.nipa.healthcareapp.data.models.Provider; // Using the Java version

import java.util.Objects;

public class ProviderAdapter extends ListAdapter<Provider, ProviderAdapter.ProviderViewHolder> {

    public interface OnProviderClickListener {
        void onProviderClick(Provider provider);
    }

    private OnProviderClickListener onProviderClickListener;

    public void setOnProviderClickListener(OnProviderClickListener listener) {
        this.onProviderClickListener = listener;
    }

    public ProviderAdapter() {
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

    // Non-static inner class to access onProviderClickListener from the adapter instance
    public class ProviderViewHolder extends RecyclerView.ViewHolder {
        private final CardView providerCard;
        private final TextView tvProviderName;
        private final TextView tvProviderSpecialty;

        public ProviderViewHolder(@NonNull View itemView) {
            super(itemView);
            providerCard = itemView.findViewById(R.id.providerCard);
            tvProviderName = itemView.findViewById(R.id.tvProviderName);
            tvProviderSpecialty = itemView.findViewById(R.id.tvProviderSpecialty);
        }

        public void bind(final Provider provider) {
            tvProviderName.setText(provider.getName());
            tvProviderSpecialty.setText(provider.getSpecialty());

            providerCard.setOnClickListener(v -> {
                if (onProviderClickListener != null) {
                    onProviderClickListener.onProviderClick(provider);
                }
            });
        }
    }

    private static class ProviderDiffCallback extends DiffUtil.ItemCallback<Provider> {
        @Override
        public boolean areItemsTheSame(@NonNull Provider oldItem, @NonNull Provider newItem) {
            // Assuming ID is non-null and unique
            return oldItem.getId().equals(newItem.getId());
        }

        @Override
        public boolean areContentsTheSame(@NonNull Provider oldItem, @NonNull Provider newItem) {
            // Field-by-field comparison for POJOs, equivalent to data class structural equality
            return oldItem.getId().equals(newItem.getId()) &&
                   Objects.equals(oldItem.getName(), newItem.getName()) &&
                   Objects.equals(oldItem.getEmail(), newItem.getEmail()) &&
                   Objects.equals(oldItem.getSpecialty(), newItem.getSpecialty()) &&
                   Float.compare(oldItem.getRating(), newItem.getRating()) == 0 && // Correct float comparison
                   Objects.equals(oldItem.getProfilePicture(), newItem.getProfilePicture()) &&
                   Objects.equals(oldItem.getAvailability(), newItem.getAvailability());
        }
    }
}
