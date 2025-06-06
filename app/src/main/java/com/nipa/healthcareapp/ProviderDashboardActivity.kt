package com.nipa.healthcareapp

import android.content.Intent // Ensure only one import
import android.os.Bundle
import android.view.MenuItem
import android.widget.TextView
import android.widget.Toast // Added Toast import
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.GravityCompat // Added GravityCompat import
import androidx.navigation.NavController // Added NavController import
import androidx.navigation.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp // Added navigateUp import
import androidx.navigation.ui.setupActionBarWithNavController
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.navigation.NavigationView
import com.google.firebase.auth.FirebaseAuth
import com.nipa.healthcareapp.databinding.ActivityProviderDashboardBinding // Added ViewBinding import


class ProviderDashboardActivity : AppCompatActivity(), NavigationView.OnNavigationItemSelectedListener {
    private lateinit var appBarConfiguration: AppBarConfiguration
    private lateinit var auth: FirebaseAuth
    // private lateinit var navView: NavigationView // Will use binding.navView
    private lateinit var binding: ActivityProviderDashboardBinding // Added ViewBinding
    private lateinit var navController: NavController // Made navController a class member

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProviderDashboardBinding.inflate(layoutInflater) // Initialize binding
        setContentView(binding.root)

        auth = FirebaseAuth.getInstance()

        setSupportActionBar(binding.toolbar) // Use binding

        // navView = findViewById(R.id.navView) // Not needed with binding
        navController = findNavController(R.id.navHostFragment) // Use class member

        // Display user email
        val headerView = binding.navView.getHeaderView(0) // Use binding
        val tvUserEmail = headerView.findViewById<TextView>(R.id.tvUserEmail) // Still need findViewById for header items
        val currentUser = auth.currentUser
        if (currentUser != null) {
            tvUserEmail.text = getString(R.string.text_logged_in_as, currentUser.email)
        } else {
            tvUserEmail.text = getString(R.string.text_not_logged_in)
            // Optionally, redirect to LoginActivity if no user
            // startActivity(Intent(this, LoginActivity::class.java))
            // finish()
        }

        appBarConfiguration = AppBarConfiguration(
            setOf(
                R.id.nav_notifications,
                R.id.nav_chats,
                R.id.nav_client_history,
                R.id.nav_view_appointments, // Added view appointments
                R.id.nav_settings,
                R.id.nav_manage_provider_profile,
                R.id.nav_logout
            ),
            binding.drawerLayout // Use binding
        )

        setupActionBarWithNavController(navController, appBarConfiguration)
        binding.navView.setupWithNavController(navController) // This sets up default navigation, use binding
        binding.navView.setNavigationItemSelectedListener(this) // Set custom listener, use binding
    }

    override fun onSupportNavigateUp(): Boolean {
        // val navController = findNavController(R.id.navHostFragment) // Use class member
        return navController.navigateUp(appBarConfiguration) || super.onSupportNavigateUp() // Pass appBarConfiguration
    }

    // It's good practice to handle onBackPressed for DrawerLayout
    override fun onBackPressed() {
        if (binding.drawerLayout.isDrawerOpen(GravityCompat.START)) {
            binding.drawerLayout.closeDrawer(GravityCompat.START)
        } else {
            super.onBackPressed()
        }
    }

    override fun onNavigationItemSelected(item: MenuItem): Boolean {
        // Handle navigation view item clicks here.
        when (item.itemId) {
            R.id.nav_manage_provider_profile -> {
                val intent = Intent(this, ProfessionalProfileActivity::class.java)
                startActivity(intent)
                binding.drawerLayout.closeDrawer(GravityCompat.START) // Close drawer
                return true // Indicate item was handled
            }
            R.id.nav_view_appointments -> {
                startActivity(Intent(this, ProviderAppointmentsActivity::class.java))
                binding.drawerLayout.closeDrawer(GravityCompat.START)
                return true
            }
            R.id.nav_logout -> {
                auth.signOut()
                val intent = Intent(this, LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
                finish()
                binding.drawerLayout.closeDrawer(GravityCompat.START) // Close drawer
                return true // Indicate item was handled
            }
        }
        // Fallback to default NavController behavior for other items
        val navigated = item.onNavDestinationSelected(navController)
        if (navigated) {
            binding.drawerLayout.closeDrawer(GravityCompat.START) // Close drawer if navigation occurred
        }
        return navigated || super.onOptionsItemSelected(item) // Ensure proper fallback
    }
}
