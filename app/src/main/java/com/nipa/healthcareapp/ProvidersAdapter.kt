package com.nipa.healthcareapp

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.data.models.Provider
import com.google.android.material.card.MaterialCardView

class ProvidersAdapter : ListAdapter<Provider, ProvidersAdapter.ProviderViewHolder>(ProviderDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProviderViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_provider, parent, false)
        return ProviderViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProviderViewHolder, position: Int) {
        val provider = getItem(position)
        holder.bind(provider)
    }

    class ProviderViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val cardView: MaterialCardView = itemView.findViewById(R.id.providerCard)
        private val nameTextView: TextView = itemView.findViewById(R.id.tvProviderName)
        private val specialtyTextView: TextView = itemView.findViewById(R.id.tvProviderSpecialty)
        private val ratingTextView: TextView = itemView.findViewById(R.id.tvRating)

        fun bind(provider: Provider) {
            nameTextView.text = provider.name
            specialtyTextView.text = provider.specialty
            ratingTextView.text = "${provider.rating}/5"
        }
    }

    private class ProviderDiffCallback : DiffUtil.ItemCallback<Provider>() {
        override fun areItemsTheSame(oldItem: Provider, newItem: Provider): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: Provider, newItem: Provider): Boolean {
            return oldItem == newItem
        }
    }
}
