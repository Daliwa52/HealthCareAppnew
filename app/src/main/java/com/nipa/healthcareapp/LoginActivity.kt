package com.nipa.healthcareapp

import android.content.Intent // Only one import needed
import android.os.Bundle
import android.util.Patterns
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthInvalidCredentialsException
import com.google.firebase.auth.FirebaseAuthInvalidUserException
import com.google.firebase.firestore.FirebaseFirestore // Added Firestore import
// Removed direct import to ProviderDashboardActivity, will use dynamic intent
import com.nipa.healthcareapp.databinding.ActivityLoginBinding

class LoginActivity : AppCompatActivity() {
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore // Added Firestore instance

    private lateinit var binding: ActivityLoginBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)
        auth = FirebaseAuth.getInstance()
        db = FirebaseFirestore.getInstance() // Initialize Firestore

        binding.btnLogin.setOnClickListener {
            val email = binding.etEmail.text.toString().trim()
            val password = binding.etPassword.text.toString()

            // Reset errors
            binding.etEmail.error = null
            binding.etPassword.error = null

            if (email.isEmpty()) {
                binding.etEmail.error = getString(R.string.error_invalid_email) // Assuming empty is also invalid
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

            auth.signInWithEmailAndPassword(email, password)
                .addOnCompleteListener(this) { task ->
                    if (task.isSuccessful) {
                        val user = auth.currentUser
                        if (user != null) {
                            val userId = user.uid
                            db.collection("users").document(userId).get()
                                .addOnSuccessListener { document ->
                                    if (document != null && document.exists()) {
                                        val role = document.getString("role")
                                        val dashboardIntent = when (role) {
                                            "patient" -> Intent(this, PatientDashboardActivity::class.java)
                                            "provider" -> Intent(this, ProviderDashboardActivity::class.java)
                                            else -> {
                                                Toast.makeText(this, getString(R.string.error_role_not_found), Toast.LENGTH_LONG).show()
                                                auth.signOut() // Sign out if role is invalid
                                                null
                                            }
                                        }
                                        if (dashboardIntent != null) {
                                            dashboardIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                            startActivity(dashboardIntent)
                                            finish()
                                        }
                                    } else {
                                        Toast.makeText(this, getString(R.string.error_fetch_user_details) + " (User data not found)", Toast.LENGTH_LONG).show()
                                        auth.signOut()
                                    }
                                }
                                .addOnFailureListener { e ->
                                    Toast.makeText(this, getString(R.string.error_fetch_user_details) + ": ${e.message}", Toast.LENGTH_LONG).show()
                                    auth.signOut()
                                }
                        } else {
                             // Should not happen if task is successful, but as a safeguard
                            Toast.makeText(this, "Authentication successful but user is null.", Toast.LENGTH_LONG).show()
                            auth.signOut()
                        }
                    } else {
                        try {
                            throw task.exception!!
                        } catch (e: FirebaseAuthInvalidUserException) {
                            Toast.makeText(this, getString(R.string.error_user_not_found), Toast.LENGTH_LONG).show()
                        } catch (e: FirebaseAuthInvalidCredentialsException) {
                            Toast.makeText(this, getString(R.string.error_invalid_password), Toast.LENGTH_LONG).show()
                        } catch (e: Exception) {
                            Toast.makeText(this, "Authentication failed: ${e.message}", Toast.LENGTH_LONG).show()
                        }
                    }
                }
        }

        binding.tvRegister.setOnClickListener {
            val intent = Intent(this, RegisterActivity::class.java)
            intent.putExtra("role", intent.getStringExtra("role")) // Pass role if needed
            startActivity(intent)
        }

        binding.tvForgotPassword.setOnClickListener {
            // Toast.makeText(this, getString(R.string.text_forgot_password_toast), Toast.LENGTH_LONG).show()
            val intent = Intent(this, ForgotPasswordActivity::class.java)
            startActivity(intent)
        }
    }
}
