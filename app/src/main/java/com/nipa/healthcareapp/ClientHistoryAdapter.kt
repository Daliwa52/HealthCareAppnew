package com.nipa.healthcareapp

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.data.models.ClientHistoryItem
import com.google.android.material.card.MaterialCardView

class ClientHistoryAdapter : ListAdapter<ClientHistoryItem, ClientHistoryAdapter.HistoryViewHolder>(HistoryDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): HistoryViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_client_history, parent, false)
        return HistoryViewHolder(view)
    }

    override fun onBindViewHolder(holder: HistoryViewHolder, position: Int) {
        val historyItem = getItem(position)
        holder.bind(historyItem)
    }

    class HistoryViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val cardView: MaterialCardView = itemView.findViewById(R.id.historyCard)
        private val patientNameTextView: TextView = itemView.findViewById(R.id.tvPatientName)
        private val consultationTypeTextView: TextView = itemView.findViewById(R.id.tvConsultationType)
        private val consultationDateTextView: TextView = itemView.findViewById(R.id.tvConsultationDate)
        private val notesTextView: TextView = itemView.findViewById(R.id.tvNotes)

        fun bind(historyItem: ClientHistoryItem) {
            patientNameTextView.text = historyItem.patientName
            consultationTypeTextView.text = historyItem.consultationType.toString()
            consultationDateTextView.text = historyItem.consultationDate.toString()
            notesTextView.text = historyItem.notes
        }
    }

    private class HistoryDiffCallback : DiffUtil.ItemCallback<ClientHistoryItem>() {
        override fun areItemsTheSame(oldItem: ClientHistoryItem, newItem: ClientHistoryItem): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: ClientHistoryItem, newItem: ClientHistoryItem): Boolean {
            return oldItem == newItem
        }
    }
}
