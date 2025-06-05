package com.nipa.healthcareapp

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.databinding.ItemProviderBinding
import com.nipa.healthcareapp.data.models.Provider

class SearchAdapter : ListAdapter<Provider, SearchAdapter.ProviderViewHolder>(ProviderDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProviderViewHolder {
        val binding = ItemProviderBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ProviderViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ProviderViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ProviderViewHolder(
        private val binding: ItemProviderBinding
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(provider: Provider) {
            binding.apply {
                tvProviderName.text = provider.name
                tvProviderSpecialty.text = provider.specialty
                
                root.setOnClickListener {
                    // Handle provider click
                }
            }
        }
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
