package com.nipa.healthcareapp.dashboard

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.findNavController
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.nipa.healthcareapp.*
import com.nipa.healthcareapp.databinding.ActivityDashboardBinding

class DashboardActivity : AppCompatActivity() {
    private lateinit var binding: ActivityDashboardBinding
    private lateinit var navView: BottomNavigationView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDashboardBinding.inflate(layoutInflater)
        setContentView(binding.root)

        navView = binding.navView
        
        // Setup with Navigation Controller
        val navController = findNavController(R.id.nav_host_fragment_activity_dashboard)
        navView.setupWithNavController(navController)
    }

    override fun onStart() {
        super.onStart()
        // Check user authentication
        if (!isUserAuthenticated()) {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
        }
    }

    private fun isUserAuthenticated(): Boolean {
        // Implement authentication check
        return true
    }
}
