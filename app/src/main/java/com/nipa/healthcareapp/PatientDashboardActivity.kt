package com.nipa.healthcareapp

import android.content.Intent // Added Intent import
import android.os.Bundle
import android.view.MenuItem
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.GravityCompat
import androidx.navigation.NavController
import androidx.navigation.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp
import androidx.navigation.ui.setupActionBarWithNavController
import androidx.navigation.ui.setupWithNavController
import androidx.navigation.ui.NavigationUI.*;
import com.google.android.material.navigation.NavigationView
import com.nipa.healthcareapp.databinding.ActivityPatientDashboardBinding

class PatientDashboardActivity : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {

    private lateinit var binding: ActivityPatientDashboardBinding
    private lateinit var appBarConfiguration: AppBarConfiguration
    private lateinit var navController: NavController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPatientDashboardBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)

        navController = findNavController(R.id.navHostFragment)

        appBarConfiguration = AppBarConfiguration(
            setOf(
                R.id.nav_providers,
                R.id.nav_notifications,
                R.id.nav_chats,
                R.id.nav_upload,
                R.id.nav_my_appointments, // Added new menu item
                R.id.nav_book_appointment,
                R.id.nav_settings,
                R.id.btnManagePatientProfile,
                R.id.nav_logout
            ),
            binding.drawerLayout
        )

        setupActionBarWithNavController(navController, appBarConfiguration)
        binding.navView.setupWithNavController(navController)
        binding.navView.setNavigationItemSelectedListener(this)

        binding.fabUpload.setOnClickListener { // Changed to use binding
            navController.navigate(R.id.nav_upload)
        }
        // The welcome message (tvPatientWelcome) is in nav_header_main.xml,
        // which is included by binding.navView. Its text is set via XML.
    }

    override fun onSupportNavigateUp(): Boolean {
        return navController.navigateUp(appBarConfiguration) || super.onSupportNavigateUp()
    }

    override fun onBackPressed() {
        if (binding.drawerLayout.isDrawerOpen(GravityCompat.START)) {
            binding.drawerLayout.closeDrawer(GravityCompat.START)
        } else {
            super.onBackPressed()
        }
    }

    override fun onNavigationItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            R.id.btnManagePatientProfile -> {
                val intent = Intent(this, PatientProfileActivity::class.java)
                startActivity(intent)
                binding.drawerLayout.closeDrawer(GravityCompat.START) // Close the drawer
                return true // Item click handled
            }
            R.id.nav_book_appointment -> {
                startActivity(Intent(this, SelectProfessionalActivity::class.java))
                binding.drawerLayout.closeDrawer(GravityCompat.START)
                return true
            }
            R.id.nav_my_appointments -> {
                startActivity(Intent(this, PatientAppointmentsActivity::class.java))
                binding.drawerLayout.closeDrawer(GravityCompat.START)
                return true
            }
            // Potentially handle other items like nav_logout here if needed
            // For now, let NavController handle other items by default
        }
        // Default handling for other menu items by NavController
        // This ensures that if an item is in the nav graph, NavController will handle it.
        val navigated = item.onNavDestinationSelected(navController)
        if (navigated) {
            binding.drawerLayout.closeDrawer(GravityCompat.START)
        }
        return navigated || super.onOptionsItemSelected(item) // Fallback for items not in nav graph
    }
}
