package com.nipa.healthcareapp

import android.content.Intent // Added Intent import
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
// No need to import FirebaseUser explicitly if only uid is used from auth.currentUser
import com.nipa.healthcareapp.databinding.ActivityPatientProfileBinding

class PatientProfileActivity : AppCompatActivity() {

    private lateinit var binding: ActivityPatientProfileBinding
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private var currentUserId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPatientProfileBinding.inflate(layoutInflater)
        setContentView(binding.root)

        title = getString(R.string.title_activity_patient_profile)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance()
        currentUserId = auth.currentUser?.uid

        if (currentUserId == null) {
            Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            // Consider finishing the activity and redirecting to Login
            // For example, could start LoginActivity with flags to clear task
            // val intent = Intent(this, LoginActivity::class.java)
            // intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            // startActivity(intent)
            finish()
            return
        }

        loadProfileData()

        binding.btnSavePatientProfile.setOnClickListener {
            currentUserId?.let { userId ->
                val medicalHistory = binding.etMedicalHistory.text.toString().trim()
                val allergies = binding.etAllergies.text.toString().trim()
                val currentMedications = binding.etCurrentMedications.text.toString().trim()

                val patientProfileMap = hashMapOf(
                    "medicalHistory" to medicalHistory,
                    "allergies" to allergies,
                    "currentMedications" to currentMedications
                )

                db.collection("users").document(userId)
                    .update("profileData", patientProfileMap) // Using update to add/modify the profileData map
                    .addOnSuccessListener {
                        Toast.makeText(this, getString(R.string.profile_saved_success), Toast.LENGTH_SHORT).show()
                        // finish() // Optional: close activity after save
                    }
                    .addOnFailureListener { e ->
                        Toast.makeText(this, getString(R.string.error_save_profile) + ": " + e.message, Toast.LENGTH_LONG).show()
                    }
            } ?: run {
                // This case should ideally not be reached if currentUserId check in onCreate leads to finish()
                Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            }
        }

        binding.tvPatientApptHistoryPlaceholder.setOnClickListener {
            startActivity(Intent(this, PatientAppointmentsActivity::class.java))
        }
    }

    private fun loadProfileData() {
        currentUserId?.let { userId ->
            db.collection("users").document(userId).get()
                .addOnSuccessListener { document ->
                    if (document != null && document.exists()) {
                        binding.tvProfileNameValue.text = document.getString("name") ?: getString(R.string.placeholder_name)
                        binding.tvProfileEmailValue.text = document.getString("email") ?: getString(R.string.placeholder_email)

                        // Firestore stores nested objects as Maps
                        @Suppress("UNCHECKED_CAST")
                        val profileData = document.get("profileData") as? Map<String, Any>
                        binding.etMedicalHistory.setText(profileData?.get("medicalHistory") as? String ?: "")
                        binding.etAllergies.setText(profileData?.get("allergies") as? String ?: "")
                        binding.etCurrentMedications.setText(profileData?.get("currentMedications") as? String ?: "")
                    } else {
                        Toast.makeText(this, getString(R.string.error_load_profile) + " (Document does not exist)", Toast.LENGTH_SHORT).show()
                         // Pre-fill name and email from auth if document doesn't exist yet or has no name/email
                        auth.currentUser?.let {
                            binding.tvProfileNameValue.text = it.displayName ?: getString(R.string.placeholder_name)
                            binding.tvProfileEmailValue.text = it.email ?: getString(R.string.placeholder_email)
                        }
                    }
                }
                .addOnFailureListener { e ->
                    Toast.makeText(this, getString(R.string.error_load_profile) + ": " + e.message, Toast.LENGTH_LONG).show()
                     // Pre-fill name and email from auth on failure too, as a fallback
                    auth.currentUser?.let {
                        binding.tvProfileNameValue.text = it.displayName ?: getString(R.string.placeholder_name)
                        binding.tvProfileEmailValue.text = it.email ?: getString(R.string.placeholder_email)
                    }
                }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
