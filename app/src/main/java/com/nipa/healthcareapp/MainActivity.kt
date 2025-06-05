package com.nipa.healthcareapp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.firebase.FirebaseApp
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.messaging.FirebaseMessaging
import com.nipa.healthcareapp.utils.ErrorHandler
import com.nipa.healthcareapp.utils.Logger

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.cancel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

class MainActivity : AppCompatActivity() {
    private lateinit var auth: FirebaseAuth
    private lateinit var db: FirebaseFirestore
    private val coroutineScope = CoroutineScope(Dispatchers.Main + Job())
    private val errorHandler = ErrorHandler(this)
    private val REQUIRED_PERMISSIONS = arrayOf(
        Manifest.permission.INTERNET,
        Manifest.permission.READ_EXTERNAL_STORAGE,
        Manifest.permission.WRITE_EXTERNAL_STORAGE,
        Manifest.permission.CAMERA
    )
    private lateinit var progressBar: ProgressBar
    private lateinit var errorContainer: View
    private lateinit var errorText: TextView
    private lateinit var retryButton: Button
    private lateinit var contentContainer: View

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        if (!checkPermissions()) {
            requestPermissions()
            return
        }

        try {
            initializeViews()
        } catch (e: Exception) {
            Logger.e("MainActivity", "Failed to initialize views", e)
            errorHandler.handleError(e)
        }
        
        // Initialize Firebase
        try {
            FirebaseApp.initializeApp(this)
            auth = FirebaseAuth.getInstance()
            db = FirebaseFirestore.getInstance()

            // Initialize Firebase Cloud Messaging
            coroutineScope.launch {
                try {
                    showLoading(true)
                    val token = FirebaseMessaging.getInstance().token.await()
                    auth.currentUser?.let { user ->
                        db.collection("users").document(user.uid)
                            .update("fcmToken", token)
                            .await()
                    }
                    handleAuthentication()
                } catch (e: Exception) {
                    showError("Failed to initialize messaging: ${e.message}")
                } finally {
                    showLoading(false)
                }
            }
        } catch (e: Exception) {
            showError("Failed to initialize app: ${e.message}")
        }
    }

    private fun initializeViews() {
        progressBar = findViewById(R.id.progressBar)
        errorContainer = findViewById(R.id.errorContainer)
        errorText = findViewById(R.id.errorText)
        retryButton = findViewById(R.id.retryButton)
        contentContainer = findViewById(R.id.contentContainer)

        retryButton.setOnClickListener {
            recreate()
        }
    }

    private fun showLoading(show: Boolean) {
        progressBar.visibility = if (show) View.VISIBLE else View.GONE
        errorContainer.visibility = View.GONE
        contentContainer.visibility = if (show) View.GONE else View.VISIBLE
    }

    private fun showError(message: String?) {
        progressBar.visibility = View.GONE
        errorContainer.visibility = View.VISIBLE
        contentContainer.visibility = View.GONE
        errorText.text = message ?: "An unknown error occurred"
    }

    private fun checkPermissions(): Boolean {
        return REQUIRED_PERMISSIONS.all { 
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun requestPermissions() {
        ActivityCompat.requestPermissions(
            this,
            REQUIRED_PERMISSIONS,
            1001
        )
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1001) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                recreate()
            } else {
                showError("Required permissions not granted")
            }
        }
    }

    private fun handleAuthentication() {
        if (auth.currentUser == null) {
            startActivity(Intent(this, WelcomeActivity::class.java))
            finish()
            return
        }

        val userRole = intent.getStringExtra("role")
        if (userRole == null) {
            showErrorDialog("Role not specified")
            finish()
            return
        }

        when (userRole) {
            "provider" -> startActivity(Intent(this, ProviderDashboardActivity::class.java))
            "patient" -> startActivity(Intent(this, PatientDashboardActivity::class.java))
            else -> {
                showErrorDialog("Invalid role specified")
                finish()
            }
        }
    }

    private fun showErrorDialog(message: String) {
        MaterialAlertDialogBuilder(this)
            .setTitle("Error")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ -> finish() }
            .show()
    }

    override fun onDestroy() {
        super.onDestroy()
        coroutineScope.cancel()
    }
}
