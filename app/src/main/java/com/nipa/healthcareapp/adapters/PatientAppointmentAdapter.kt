package com.nipa.healthcareapp.adapters

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.R // Import R
import com.nipa.healthcareapp.databinding.ListItemAppointmentBinding
import com.nipa.healthcareapp.models.Appointment
import java.text.SimpleDateFormat
import java.util.*

class PatientAppointmentAdapter(
    private var appointments: List<Appointment>,
    private val onItemClicked: (Appointment) -> Unit
) : RecyclerView.Adapter<PatientAppointmentAdapter.ViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ListItemAppointmentBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val appointment = appointments[position]
        holder.bind(appointment)
        holder.itemView.setOnClickListener { onItemClicked(appointment) }
    }

    override fun getItemCount(): Int = appointments.size

    fun updateAppointments(newAppointments: List<Appointment>) {
        appointments = newAppointments
        notifyDataSetChanged() // Consider DiffUtil later
    }

    class ViewHolder(private val binding: ListItemAppointmentBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(appointment: Appointment) {
            // Use context from itemView to get strings
            val context = binding.root.context
            // For patients, tvListItemPatientName should show the professional's name
            binding.tvListItemPatientName.text = context.getString(R.string.label_professional_name_prefix) + " ${appointment.professionalName ?: "N/A"}"
            binding.tvListItemReason.text = context.getString(R.string.label_reason_prefix) + " ${appointment.reasonForVisit ?: "N/A"}"
            binding.tvListItemStatus.text = context.getString(R.string.label_status_prefix) + " ${appointment.status ?: "N/A"}"

            val sdf = SimpleDateFormat("MMM dd, yyyy 'at' hh:mm a", Locale.getDefault())
            binding.tvListItemDateTime.text = context.getString(R.string.label_appointment_datetime_prefix) + " ${appointment.appointmentTimestamp?.toDate()?.let { sdf.format(it) } ?: "N/A"}"
        }
    }
}
