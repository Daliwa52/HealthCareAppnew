package com.nipa.healthcareapp

import android.content.Intent
import android.os.Bundle
import android.util.Patterns
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthUserCollisionException
import com.google.firebase.auth.FirebaseAuthWeakPasswordException
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.ProviderDashboardActivity
import com.nipa.healthcareapp.databinding.ActivityRegisterBinding

class RegisterActivity : AppCompatActivity() {
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private lateinit var binding: ActivityRegisterBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance()

        val userRole = intent.getStringExtra("role")
        
        binding.btnRegister.setOnClickListener {
            val name = binding.etName.text.toString().trim()
            val email = binding.etEmail.text.toString().trim()
            val password = binding.etPassword.text.toString()
            val confirmPassword = binding.etConfirmPassword.text.toString()

            // Reset errors
            binding.etName.error = null
            binding.etEmail.error = null
            binding.etPassword.error = null
            binding.etConfirmPassword.error = null

            if (name.isEmpty()) {
                binding.etName.error = getString(R.string.error_name_required)
                return@setOnClickListener
            }

            if (email.isEmpty()) {
                binding.etEmail.error = getString(R.string.error_invalid_email) // Assuming empty is also invalid email
                return@setOnClickListener
            }

            if (!Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
                binding.etEmail.error = getString(R.string.error_invalid_email)
                return@setOnClickListener
            }

            if (password.isEmpty()) {
                binding.etPassword.error = getString(R.string.error_password_required)
                return@setOnClickListener
            }

            if (password.length < 6) {
                binding.etPassword.error = getString(R.string.error_password_length)
                return@setOnClickListener
            }

            if (confirmPassword.isEmpty()) {
                binding.etConfirmPassword.error = getString(R.string.error_passwords_no_match) // Or a specific "confirm password required"
                return@setOnClickListener
            }

            if (password != confirmPassword) {
                binding.etConfirmPassword.error = getString(R.string.error_passwords_no_match)
                return@setOnClickListener
            }

            auth.createUserWithEmailAndPassword(email, password)
                .addOnCompleteListener(this) { task ->
                    if (task.isSuccessful) {
                        val user = auth.currentUser
                        val userData = hashMapOf(
                            "name" to name,
                            "role" to userRole,
                            "email" to email
                        )

                        db.collection("users")
                            .document(user?.uid ?: "")
                            .set(userData)
                            .addOnSuccessListener {
                                // Role-based navigation
                                val dashboardIntent = when (userRole) {
                                    "patient" -> Intent(this, PatientDashboardActivity::class.java)
                                    "provider" -> Intent(this, ProviderDashboardActivity::class.java)
                                    else -> {
                                        Toast.makeText(this, getString(R.string.error_unexpected_role) + " Role: $userRole", Toast.LENGTH_LONG).show()
                                        // Optionally navigate to Login or a default screen, or just don't finish.
                                        // For now, if role is unknown, it will effectively stay on a completed registration screen or user has to manually go to login.
                                        null
                                    }
                                }

                                if (dashboardIntent != null) {
                                    dashboardIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    startActivity(dashboardIntent)
                                    finish()
                                } else {
                                    // If dashboardIntent is null (e.g. unexpected role),
                                    // you might want to explicitly navigate to LoginActivity.
                                    // For now, it will just show the toast and the user would be on a "finished" RegisterActivity.
                                    // Consider:
                                    // val loginIntent = Intent(this, LoginActivity::class.java)
                                    // loginIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    // startActivity(loginIntent)
                                    // finish()
                                }
                            }
                            .addOnFailureListener { e ->
                                Toast.makeText(this, "Registration failed: ${e.message}", Toast.LENGTH_LONG).show()
                            }
                    } else {
                        try {
                            throw task.exception!!
                        } catch (e: FirebaseAuthUserCollisionException) {
                            Toast.makeText(this, getString(R.string.error_email_exists), Toast.LENGTH_LONG).show()
                        } catch (e: FirebaseAuthWeakPasswordException) {
                            Toast.makeText(this, getString(R.string.error_weak_password), Toast.LENGTH_LONG).show()
                        } catch (e: Exception) {
                            Toast.makeText(this, "Registration failed: ${e.message}", Toast.LENGTH_LONG).show()
                        }
                    }
                }
        }

        binding.tvLogin.setOnClickListener {
            val intent = Intent(this, LoginActivity::class.java)
            intent.putExtra("role", userRole)
            startActivity(intent)
        }
    }
}
