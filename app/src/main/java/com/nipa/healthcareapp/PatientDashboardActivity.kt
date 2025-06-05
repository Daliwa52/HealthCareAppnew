package com.nipa.healthcareapp

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.setupActionBarWithNavController
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.navigation.NavigationView


class PatientDashboardActivity : AppCompatActivity() {
    private lateinit var appBarConfiguration: AppBarConfiguration

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_patient_dashboard)

        val toolbar: androidx.appcompat.widget.Toolbar = findViewById(R.id.toolbar)
        setSupportActionBar(toolbar)

        val navView: NavigationView = findViewById(R.id.navView)
        val navController = findNavController(R.id.navHostFragment)

        appBarConfiguration = AppBarConfiguration(
            setOf(
                R.id.nav_providers,
                R.id.nav_notifications,
                R.id.nav_chats,
                R.id.nav_upload,
                R.id.nav_settings
            ),
            findViewById<androidx.drawerlayout.widget.DrawerLayout>(R.id.drawerLayout)
        )

        setupActionBarWithNavController(navController, appBarConfiguration)
        navView.setupWithNavController(navController)

        val fabUpload: com.google.android.material.floatingactionbutton.FloatingActionButton = findViewById(R.id.fabUpload)
        fabUpload.setOnClickListener {
            navController.navigate(R.id.nav_upload)
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        val navController = findNavController(R.id.navHostFragment)
        return navController.navigateUp() || super.onSupportNavigateUp()
    }
}
