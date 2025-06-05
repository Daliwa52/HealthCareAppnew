package com.nipa.healthcareapp

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.data.models.Provider

class ProviderAdapter : ListAdapter<Provider, ProviderAdapter.ProviderViewHolder>(ProviderDiffCallback()) {

    private var onProviderClickListener: ((Provider) -> Unit)? = null

    fun setOnProviderClickListener(listener: (Provider) -> Unit) {
        onProviderClickListener = listener
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProviderViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_provider, parent, false)
        return ProviderViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProviderViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ProviderViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val providerCard: CardView = itemView.findViewById(R.id.providerCard)
        private val tvProviderName: TextView = itemView.findViewById(R.id.tvProviderName)
        private val tvProviderSpecialty: TextView = itemView.findViewById(R.id.tvProviderSpecialty)

        fun bind(provider: Provider) {
            tvProviderName.text = provider.name
            tvProviderSpecialty.text = provider.specialty

            providerCard.setOnClickListener {
                onProviderClickListener?.invoke(provider)
            }
        }
    }

    class ProviderDiffCallback : DiffUtil.ItemCallback<Provider>() {
        override fun areItemsTheSame(oldItem: Provider, newItem: Provider): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: Provider, newItem: Provider): Boolean {
            return oldItem == newItem
        }
    }
}
