package com.nipa.healthcareapp

import android.app.AlertDialog // Added AlertDialog import
import android.os.Bundle
import android.util.Log // Added Log import
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import java.text.SimpleDateFormat // Added SimpleDateFormat import
import java.util.Locale // Added Locale import
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.Query
import com.nipa.healthcareapp.adapters.AppointmentAdapter
import com.nipa.healthcareapp.databinding.ActivityProviderAppointmentsBinding
import com.nipa.healthcareapp.models.Appointment

class ProviderAppointmentsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProviderAppointmentsBinding
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private lateinit var appointmentAdapter: AppointmentAdapter
    private val appointmentsList = mutableListOf<Appointment>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProviderAppointmentsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        title = getString(R.string.title_activity_provider_appointments)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance()

        setupRecyclerView()
        loadAppointments()
    }

    private fun setupRecyclerView() {
        appointmentAdapter = AppointmentAdapter(appointmentsList) { appointment ->
            showAppointmentActionDialog(appointment)
        }
        binding.rvProviderAppointments.apply {
            layoutManager = LinearLayoutManager(this@ProviderAppointmentsActivity)
            adapter = appointmentAdapter
        }
    }

    private fun loadAppointments() {
        binding.pbLoadingAppointmentsProvider.visibility = View.VISIBLE
        binding.tvNoAppointmentsProvider.visibility = View.GONE
        binding.rvProviderAppointments.visibility = View.GONE

        val providerUid = auth.currentUser?.uid
        if (providerUid == null) {
            Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            binding.pbLoadingAppointmentsProvider.visibility = View.GONE
            finish()
            return
        }

        db.collection("appointments")
            .whereEqualTo("professionalId", providerUid)
            // "pending_confirmation" and "confirmed" seem most relevant for active management.
            // Could also include "completed" or "cancelled" if a history view is intended.
            // .whereIn("status", listOf("pending_confirmation", "confirmed")) // Removed for history view
            .orderBy("appointmentTimestamp", Query.Direction.DESCENDING) // Show most recent first
            .get()
            .addOnSuccessListener { documents ->
                binding.pbLoadingAppointmentsProvider.visibility = View.GONE
                appointmentsList.clear()
                if (documents.isEmpty) {
                    binding.tvNoAppointmentsProvider.visibility = View.VISIBLE
                    binding.rvProviderAppointments.visibility = View.GONE
                } else {
                    val fetchedAppointments = documents.toObjects(Appointment::class.java)
                    appointmentsList.addAll(fetchedAppointments)
                    binding.rvProviderAppointments.visibility = View.VISIBLE
                    binding.tvNoAppointmentsProvider.visibility = View.GONE
                }
                appointmentAdapter.updateAppointments(appointmentsList) // Use a copy if direct modification is an issue
            }
            .addOnFailureListener { e ->
                binding.pbLoadingAppointmentsProvider.visibility = View.GONE
                binding.tvNoAppointmentsProvider.visibility = View.VISIBLE // Show no appointments on error too
                binding.rvProviderAppointments.visibility = View.GONE
                Toast.makeText(this, "Error loading appointments: ${e.message}", Toast.LENGTH_LONG).show()
            }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }

    private fun showAppointmentActionDialog(appointment: Appointment) {
        val sdfDate = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
        val sdfTime = SimpleDateFormat("hh:mm a", Locale.getDefault())
        val dateStr = appointment.appointmentTimestamp?.toDate()?.let { sdfDate.format(it) } ?: "N/A"
        val timeStr = appointment.appointmentTimestamp?.toDate()?.let { sdfTime.format(it) } ?: "N/A"

        val message = getString(R.string.dialog_message_appointment_details,
            appointment.patientName ?: "N/A",
            dateStr,
            timeStr,
            appointment.reasonForVisit ?: "N/A",
            appointment.status ?: "N/A"
        )

        val builder = AlertDialog.Builder(this)
        builder.setTitle(getString(R.string.dialog_title_appointment_action))
        builder.setMessage(message)

        // Confirm Button - Visible only if status is "pending_confirmation"
        if (appointment.status == "pending_confirmation") {
            builder.setPositiveButton(getString(R.string.btn_confirm_appointment)) { dialog, _ ->
                updateAppointmentStatus(appointment.id, "confirmed")
                dialog.dismiss()
            }
        }

        // Cancel Button - Visible if status is "pending_confirmation" or "confirmed"
        if (appointment.status == "pending_confirmation" || appointment.status == "confirmed") {
            builder.setNegativeButton(getString(R.string.btn_cancel_appointment_provider)) { dialog, _ ->
                updateAppointmentStatus(appointment.id, "cancelled_by_provider")
                dialog.dismiss()
            }
        }

        // Dismiss Button - Always visible as a neutral option
        builder.setNeutralButton(getString(R.string.btn_dismiss)) { dialog, _ ->
            dialog.dismiss()
        }

        builder.create().show()
    }

    private fun updateAppointmentStatus(appointmentId: String?, newStatus: String) {
        if (appointmentId == null) {
            Log.e("ProviderAppointments", "Appointment ID is null, cannot update status.")
            Toast.makeText(this, getString(R.string.error_updating_appointment_status), Toast.LENGTH_SHORT).show()
            return
        }

        db.collection("appointments").document(appointmentId)
            .update("status", newStatus)
            .addOnSuccessListener {
                val successMessage = if (newStatus == "confirmed") getString(R.string.appointment_confirmed_success)
                                     else getString(R.string.appointment_cancelled_success) // Assumes any other status change to here is cancellation by provider
                Toast.makeText(this, successMessage, Toast.LENGTH_SHORT).show()
                loadAppointments() // Refresh the list
            }
            .addOnFailureListener { e ->
                Log.e("ProviderAppointments", "Error updating appointment status for $appointmentId to $newStatus", e)
                Toast.makeText(this, getString(R.string.error_updating_appointment_status) + ": " + e.message, Toast.LENGTH_LONG).show()
            }
    }
}
