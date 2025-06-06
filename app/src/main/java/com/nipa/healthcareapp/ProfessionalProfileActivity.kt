package com.nipa.healthcareapp

import android.content.Intent // Added Intent import
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.databinding.ActivityProfessionalProfileBinding

class ProfessionalProfileActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProfessionalProfileBinding
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private var currentUserId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProfessionalProfileBinding.inflate(layoutInflater)
        setContentView(binding.root)

        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance()
        currentUserId = auth.currentUser?.uid

        if (currentUserId == null) {
            Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            finish()
            return // Important to return early if not logged in
        }

        title = getString(R.string.title_activity_professional_profile)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        loadProfileData()

        binding.btnSaveProfessionalProfile.setOnClickListener {
            currentUserId?.let { userId ->
                val qualifications = binding.etQualifications.text.toString().trim()
                val specialties = binding.etSpecialties.text.toString().trim()
                val availabilityNotes = binding.etAvailabilityNotes.text.toString().trim()

                val professionalProfileMap = hashMapOf(
                    "qualifications" to qualifications,
                    "specialties" to specialties,
                    "availabilityNotes" to availabilityNotes
                )

                db.collection("users").document(userId)
                    .update("profileData", professionalProfileMap) // This will update or create the profileData field
                    .addOnSuccessListener {
                        Toast.makeText(this, getString(R.string.profile_saved_success), Toast.LENGTH_SHORT).show()
                        // finish() // Optional
                    }
                    .addOnFailureListener { e ->
                        Toast.makeText(this, getString(R.string.error_save_profile) + ": " + e.message, Toast.LENGTH_LONG).show()
                    }
            } ?: run {
                Toast.makeText(this, getString(R.string.error_not_logged_in), Toast.LENGTH_LONG).show()
            }
        }

        binding.tvProfessionalApptHistoryPlaceholder.setOnClickListener {
            startActivity(Intent(this, ProviderAppointmentsActivity::class.java))
        }
    }

    private fun loadProfileData() {
        currentUserId?.let { userId ->
            db.collection("users").document(userId).get()
                .addOnSuccessListener { document ->
                    if (document.exists()) {
                        binding.tvProfNameValue.text = document.getString("name") ?: auth.currentUser?.displayName ?: ""
                        binding.tvProfEmailValue.text = document.getString("email") ?: auth.currentUser?.email ?: ""

                        @Suppress("UNCHECKED_CAST")
                        val profileData = document.get("profileData") as? Map<String, Any>
                        binding.etQualifications.setText(profileData?.get("qualifications") as? String ?: "")
                        binding.etSpecialties.setText(profileData?.get("specialties") as? String ?: "")
                        binding.etAvailabilityNotes.setText(profileData?.get("availabilityNotes") as? String ?: "")
                    } else {
                        // Still set name/email from auth if possible, even if profile doc is new/empty
                        binding.tvProfNameValue.text = auth.currentUser?.displayName ?: ""
                        binding.tvProfEmailValue.text = auth.currentUser?.email ?: ""
                        Toast.makeText(this, getString(R.string.error_load_profile) + " Profile data might be new.", Toast.LENGTH_SHORT).show()
                    }
                }
                .addOnFailureListener { e ->
                    // Fallback to auth for name/email on failure too
                    binding.tvProfNameValue.text = auth.currentUser?.displayName ?: ""
                    binding.tvProfEmailValue.text = auth.currentUser?.email ?: ""
                    Toast.makeText(this, getString(R.string.error_load_profile) + ": " + e.message, Toast.LENGTH_LONG).show()
                }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
