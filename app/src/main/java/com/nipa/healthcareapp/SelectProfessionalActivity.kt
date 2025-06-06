package com.nipa.healthcareapp

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.nipa.healthcareapp.databinding.ActivitySelectProfessionalBinding

class SelectProfessionalActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySelectProfessionalBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySelectProfessionalBinding.inflate(layoutInflater)
        setContentView(binding.root)

        title = getString(R.string.title_select_professional)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)

        binding.btnFetchProfessional.setOnClickListener {
            val professionalId = binding.etProfessionalUidInput.text.toString().trim()
            if (professionalId.isNotEmpty()) {
                val intent = Intent(this, ViewProfessionalProfileForPatientActivity::class.java)
                intent.putExtra("PROFESSIONAL_UID", professionalId)
                startActivity(intent)
            } else {
                Toast.makeText(this, "Please enter a Professional ID", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        onBackPressedDispatcher.onBackPressed()
        return true
    }
}
