package com.nipa.healthcareapp

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.RadioButton
import androidx.appcompat.app.AppCompatActivity
import com.nipa.healthcareapp.LoginActivity
import com.nipa.healthcareapp.RegisterActivity

class WelcomeActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_welcome)

        val radioCareProvider = findViewById<RadioButton>(R.id.radioCareProvider)
        val radioPatient = findViewById<RadioButton>(R.id.radioPatient)
        val btnLogin = findViewById<Button>(R.id.btnLogin)
        val btnRegister = findViewById<Button>(R.id.btnRegister)

        btnLogin.setOnClickListener {
            val role = if (radioCareProvider.isChecked) "provider" else "patient"
            val intent = Intent(this, LoginActivity::class.java)
            intent.putExtra("role", role)
            startActivity(intent)
        }

        btnRegister.setOnClickListener {
            val role = if (radioCareProvider.isChecked) "provider" else "patient"
            val intent = Intent(this, RegisterActivity::class.java)
            intent.putExtra("role", role)
            startActivity(intent)
        }
    }
}
