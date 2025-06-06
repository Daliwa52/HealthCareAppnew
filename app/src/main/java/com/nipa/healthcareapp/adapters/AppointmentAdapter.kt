package com.nipa.healthcareapp.adapters

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.nipa.healthcareapp.R // Required for string resources
import com.nipa.healthcareapp.databinding.ListItemAppointmentBinding
import com.nipa.healthcareapp.models.Appointment
import java.text.SimpleDateFormat
import java.util.*

class AppointmentAdapter(
    private var appointments: List<Appointment>,
    private val onItemClicked: (Appointment) -> Unit
) : RecyclerView.Adapter<AppointmentAdapter.AppointmentViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AppointmentViewHolder {
        val binding = ListItemAppointmentBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return AppointmentViewHolder(binding)
    }

    override fun onBindViewHolder(holder: AppointmentViewHolder, position: Int) {
        val appointment = appointments[position]
        holder.bind(appointment)
        holder.itemView.setOnClickListener { onItemClicked(appointment) }
    }

    override fun getItemCount(): Int = appointments.size

    fun updateAppointments(newAppointments: List<Appointment>) {
        appointments = newAppointments
        notifyDataSetChanged() // Consider DiffUtil for better performance later
    }

    class AppointmentViewHolder(private val binding: ListItemAppointmentBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(appointment: Appointment) {
            val context = binding.root.context
            binding.tvListItemPatientName.text = context.getString(R.string.label_patient_name_prefix) + " ${appointment.patientName ?: "N/A"}"
            binding.tvListItemReason.text = context.getString(R.string.label_reason_prefix) + " ${appointment.reasonForVisit ?: "N/A"}"
            binding.tvListItemStatus.text = context.getString(R.string.label_status_prefix) + " ${appointment.status ?: "N/A"}"

            val sdf = SimpleDateFormat("MMM dd, yyyy 'at' hh:mm a", Locale.getDefault())
            binding.tvListItemDateTime.text = context.getString(R.string.label_appointment_datetime_prefix) + " ${appointment.appointmentTimestamp?.toDate()?.let { sdf.format(it) } ?: "N/A"}"
        }
    }
}
