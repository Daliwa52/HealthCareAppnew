package com.nipa.healthcareapp

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.Timestamp // Import Firebase Timestamp
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FieldValue
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.databinding.ActivityRequestAppointmentBinding
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

class RequestAppointmentActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRequestAppointmentBinding
    private var professionalUid: String? = null
    private var professionalName: String? = null
    private val appointmentCalendar: Calendar = Calendar.getInstance()
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private var currentPatientId: String? = null
    private var currentPatientName: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRequestAppointmentBinding.inflate(layoutInflater)
        setContentView(binding.root)

        professionalUid = intent.getStringExtra("PROFESSIONAL_UID")
        professionalName = intent.getStringExtra("PROFESSIONAL_NAME")

        if (professionalUid == null || professionalName == null) {
            Toast.makeText(this, getString(R.string.error_professional_details_missing), Toast.LENGTH_LONG).show()
            finish()
            return
        }

        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance()
        currentPatientId = auth.currentUser?.uid

        if (currentPatientId == null) {
            Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            finish()
            return
        }
        fetchPatientName(currentPatientId!!)

        title = getString(R.string.title_activity_request_appointment)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        binding.tvRequestingWithProfName.text = getString(R.string.label_requesting_appointment_with, professionalName)

        updateDateDisplay()
        updateTimeDisplay()

        binding.tvSelectedDateValue.setOnClickListener {
            showDatePicker()
        }

        binding.tvSelectedTimeValue.setOnClickListener {
            showTimePicker()
        }

        binding.btnSubmitRequest.setOnClickListener {
            if (currentPatientId == null || currentPatientName == null) {
                Toast.makeText(this, getString(R.string.error_patient_details_missing_for_request), Toast.LENGTH_LONG).show()
                return@setOnClickListener
            }
            // This check is somewhat redundant due to onCreate logic, but good for safety
            if (professionalUid == null || professionalName == null) {
                Toast.makeText(this, getString(R.string.error_professional_details_missing), Toast.LENGTH_LONG).show()
                return@setOnClickListener
            }
            val reason = binding.etReasonForVisit.text.toString().trim()
            if (reason.isEmpty()) {
                binding.etReasonForVisit.error = getString(R.string.error_reason_required)
                return@setOnClickListener
            }

            val appointmentTimestampCal = Timestamp(appointmentCalendar.time)

            val appointmentData = hashMapOf(
                "patientId" to currentPatientId,
                "patientName" to currentPatientName,
                "professionalId" to professionalUid,
                "professionalName" to professionalName,
                "appointmentTimestamp" to appointmentTimestampCal,
                "reasonForVisit" to reason,
                "status" to "pending_confirmation", // Initial status
                "createdAt" to FieldValue.serverTimestamp()
            )

            db.collection("appointments").add(appointmentData)
                .addOnSuccessListener {
                    Toast.makeText(this, getString(R.string.appointment_request_sent_success), Toast.LENGTH_LONG).show()
                    finish() // Go back after successful request
                }
                .addOnFailureListener { e ->
                    Toast.makeText(this, getString(R.string.appointment_request_failed) + ": " + e.message, Toast.LENGTH_LONG).show()
                    Log.e("RequestAppointment", "Error adding appointment", e)
                }
        }
    }

    private fun fetchPatientName(patientId: String) {
        // Optional: Show a small loading indicator or Toast
        // Toast.makeText(this, getString(R.string.fetching_patient_details), Toast.LENGTH_SHORT).show()
        db.collection("users").document(patientId).get()
            .addOnSuccessListener { document ->
                if (document.exists()) {
                    currentPatientName = document.getString("name")
                    if (currentPatientName == null) { // Fallback if name field is missing
                       currentPatientName = auth.currentUser?.displayName ?: "Patient"
                    }
                } else { // Document doesn't exist
                    currentPatientName = auth.currentUser?.displayName ?: "Patient"
                     Log.w("RequestAppointment", "Patient document not found, using display name as fallback.")
                }
            }
            .addOnFailureListener { e ->
                currentPatientName = auth.currentUser?.displayName ?: "Patient" // Fallback
                Log.e("RequestAppointment", "Error fetching patient name", e)
                // Toast.makeText(this, "Could not fetch your name, using default.", Toast.LENGTH_SHORT).show()
            }
    }

    private fun showDatePicker() {
        val year = appointmentCalendar.get(Calendar.YEAR)
        val month = appointmentCalendar.get(Calendar.MONTH)
        val day = appointmentCalendar.get(Calendar.DAY_OF_MONTH)

        val datePickerDialog = DatePickerDialog(this, { _, selectedYear, selectedMonth, selectedDayOfMonth ->
            appointmentCalendar.set(Calendar.YEAR, selectedYear)
            appointmentCalendar.set(Calendar.MONTH, selectedMonth)
            appointmentCalendar.set(Calendar.DAY_OF_MONTH, selectedDayOfMonth)
            updateDateDisplay()
        }, year, month, day)

        // Optional: Set min date to today
        datePickerDialog.datePicker.minDate = System.currentTimeMillis() - 1000
        datePickerDialog.show()
    }

    private fun showTimePicker() {
        val hour = appointmentCalendar.get(Calendar.HOUR_OF_DAY)
        val minute = appointmentCalendar.get(Calendar.MINUTE)

        val timePickerDialog = TimePickerDialog(this, { _, selectedHour, selectedMinute ->
            appointmentCalendar.set(Calendar.HOUR_OF_DAY, selectedHour)
            appointmentCalendar.set(Calendar.MINUTE, selectedMinute)
            updateTimeDisplay()
        }, hour, minute, false) // false for 12-hour format with AM/PM
        timePickerDialog.show()
    }

    private fun updateDateDisplay() {
        val dateFormat = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
        binding.tvSelectedDateValue.text = dateFormat.format(appointmentCalendar.time)
    }

    private fun updateTimeDisplay() {
        val timeFormat = SimpleDateFormat("hh:mm a", Locale.getDefault())
        binding.tvSelectedTimeValue.text = timeFormat.format(appointmentCalendar.time)
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
