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
import com.nipa.healthcareapp.adapters.PatientAppointmentAdapter
import com.nipa.healthcareapp.databinding.ActivityPatientAppointmentsBinding
import com.nipa.healthcareapp.models.Appointment

class PatientAppointmentsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityPatientAppointmentsBinding
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private lateinit var patientAppointmentAdapter: PatientAppointmentAdapter
    private val appointmentsList = mutableListOf<Appointment>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPatientAppointmentsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        title = getString(R.string.title_activity_patient_appointments)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance()

        setupRecyclerView()
        loadAppointments()
    }

    private fun setupRecyclerView() {
        patientAppointmentAdapter = PatientAppointmentAdapter(appointmentsList) { appointment ->
            showPatientAppointmentActionDialog(appointment)
        }
        binding.rvPatientAppointments.apply {
            layoutManager = LinearLayoutManager(this@PatientAppointmentsActivity)
            adapter = patientAppointmentAdapter
        }
    }

    private fun loadAppointments() {
        binding.pbLoadingAppointmentsPatient.visibility = View.VISIBLE
        binding.tvNoAppointmentsPatient.visibility = View.GONE
        binding.rvPatientAppointments.visibility = View.GONE

        val patientUid = auth.currentUser?.uid
        if (patientUid == null) {
            Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            binding.pbLoadingAppointmentsPatient.visibility = View.GONE
            finish()
            return
        }

        db.collection("appointments")
            .whereEqualTo("patientId", patientUid)
            .orderBy("appointmentTimestamp", Query.Direction.DESCENDING) // Show newest first, or ASCENDING for upcoming
            .get()
            .addOnSuccessListener { documents ->
                binding.pbLoadingAppointmentsPatient.visibility = View.GONE
                appointmentsList.clear()
                if (documents.isEmpty) {
                    binding.tvNoAppointmentsPatient.visibility = View.VISIBLE
                    binding.rvPatientAppointments.visibility = View.GONE
                } else {
                    val fetchedAppointments = documents.toObjects(Appointment::class.java)
                    appointmentsList.addAll(fetchedAppointments)
                    binding.rvPatientAppointments.visibility = View.VISIBLE
                    binding.tvNoAppointmentsPatient.visibility = View.GONE
                }
                patientAppointmentAdapter.updateAppointments(appointmentsList)
            }
            .addOnFailureListener { e ->
                binding.pbLoadingAppointmentsPatient.visibility = View.GONE
                binding.tvNoAppointmentsPatient.visibility = View.VISIBLE
                binding.rvPatientAppointments.visibility = View.GONE
                Toast.makeText(this, "Error loading appointments: ${e.message}", Toast.LENGTH_LONG).show()
            }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }

    private fun showPatientAppointmentActionDialog(appointment: Appointment) {
        val sdfDate = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
        val sdfTime = SimpleDateFormat("hh:mm a", Locale.getDefault())
        val dateStr = appointment.appointmentTimestamp?.toDate()?.let { sdfDate.format(it) } ?: "N/A"
        val timeStr = appointment.appointmentTimestamp?.toDate()?.let { sdfTime.format(it) } ?: "N/A"

        val message = getString(R.string.dialog_message_patient_appointment_details,
            appointment.professionalName ?: "N/A",
            dateStr,
            timeStr,
            appointment.reasonForVisit ?: "N/A",
            appointment.status ?: "N/A"
        )

        val builder = AlertDialog.Builder(this)
        builder.setTitle(getString(R.string.dialog_title_patient_appointment_action))
        builder.setMessage(message)

        // Cancel Appointment Button - Visible if status is "pending_confirmation" or "confirmed"
        if (appointment.status == "pending_confirmation" || appointment.status == "confirmed") {
            builder.setNegativeButton(getString(R.string.btn_cancel_appointment_patient)) { dialog, _ ->
                updateAppointmentStatusByPatient(appointment.id, "cancelled_by_patient")
                dialog.dismiss()
            }
        }

        // Dismiss Button - Positive button as the main non-destructive action or if no other action is available.
        builder.setPositiveButton(getString(R.string.btn_dismiss)) { dialog, _ ->
            dialog.dismiss()
        }

        builder.create().show()
    }

    private fun updateAppointmentStatusByPatient(appointmentId: String?, newStatus: String) {
        if (appointmentId == null) {
            Log.e("PatientAppointments", "Appointment ID is null, cannot update status.")
            Toast.makeText(this, getString(R.string.error_updating_appointment_status), Toast.LENGTH_SHORT).show()
            return
        }

        db.collection("appointments").document(appointmentId)
            .update("status", newStatus)
            .addOnSuccessListener {
                // For patient cancellation, the message is always appointment_cancelled_success
                Toast.makeText(this, getString(R.string.appointment_cancelled_success), Toast.LENGTH_SHORT).show()
                loadAppointments() // Refresh the list
            }
            .addOnFailureListener { e ->
                Log.e("PatientAppointments", "Error updating appointment status for $appointmentId to $newStatus by patient", e)
                Toast.makeText(this, getString(R.string.error_updating_appointment_status) + ": " + e.message, Toast.LENGTH_LONG).show()
            }
    }
}
