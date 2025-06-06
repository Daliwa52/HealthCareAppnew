package com.nipa.healthcareapp

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.databinding.ActivityViewProfessionalProfileForPatientBinding

class ViewProfessionalProfileForPatientActivity : AppCompatActivity() {

    private lateinit var binding: ActivityViewProfessionalProfileForPatientBinding
    private lateinit var db: FirebaseFirestore
    private var professionalUid: String? = null
    private var professionalName: String? = null // To pass to RequestAppointmentActivity

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityViewProfessionalProfileForPatientBinding.inflate(layoutInflater)
        setContentView(binding.root)

        title = getString(R.string.title_activity_view_professional_profile_for_patient)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        db = FirebaseFirestore.getInstance()
        professionalUid = intent.getStringExtra("PROFESSIONAL_UID")

        if (professionalUid == null) {
            Toast.makeText(this, "Error: Professional ID not provided.", Toast.LENGTH_LONG).show()
            finish()
            return
        }

        loadProfessionalProfile(professionalUid!!)

        binding.btnGoToRequestAppointment.setOnClickListener {
            if (professionalUid != null && professionalName != null) {
                val intent = Intent(this, RequestAppointmentActivity::class.java)
                intent.putExtra("PROFESSIONAL_UID", professionalUid)
                intent.putExtra("PROFESSIONAL_NAME", professionalName)
                startActivity(intent)
            } else {
                Toast.makeText(this, getString(R.string.error_professional_details_missing), Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun loadProfessionalProfile(profId: String) {
        db.collection("users").document(profId).get()
            .addOnSuccessListener { document ->
                if (document.exists() && document.getString("role") == "provider") {
                    professionalName = document.getString("name") // Store for later use

                    binding.tvProfNamePatientView.text = professionalName ?: "N/A"
                    binding.tvProfEmailPatientView.text = document.getString("email") ?: "N/A"

                    @Suppress("UNCHECKED_CAST")
                    val profileData = document.get("profileData") as? Map<String, Any>
                    binding.tvProfQualificationsPatientView.text = profileData?.get("qualifications") as? String ?: "Not specified"
                    binding.tvProfSpecialtiesPatientView.text = profileData?.get("specialties") as? String ?: "Not specified"
                    binding.tvProfAvailabilityPatientView.text = profileData?.get("availabilityNotes") as? String ?: "Not specified"
                } else {
                    Toast.makeText(this, getString(R.string.error_professional_not_found), Toast.LENGTH_LONG).show()
                    finish()
                }
            }
            .addOnFailureListener { e ->
                Toast.makeText(this, getString(R.string.error_loading_professional_profile) + ": " + e.message, Toast.LENGTH_LONG).show()
                finish()
            }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
