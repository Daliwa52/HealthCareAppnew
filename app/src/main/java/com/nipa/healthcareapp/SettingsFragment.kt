package com.nipa.healthcareapp

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore

class SettingsFragment : Fragment() {
    private val auth = FirebaseAuth.getInstance()
    private val db = FirebaseFirestore.getInstance()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_settings, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val profileCard = view.findViewById<androidx.cardview.widget.CardView>(R.id.profileCard)
        val editProfileButton = view.findViewById<com.google.android.material.button.MaterialButton>(R.id.editProfileButton)
        val logoutButton = view.findViewById<com.google.android.material.button.MaterialButton>(R.id.logoutButton)

        profileCard.setOnClickListener { handleProfileClick() }
        editProfileButton.setOnClickListener { handleProfileClick() }
        logoutButton.setOnClickListener { handleLogoutClick() }
        
        // Set up settings list with RecyclerView
        setupSettingsList(view)
    }

    private fun setupSettingsList(view: View) {
        val settingsList = view.findViewById<RecyclerView>(R.id.settingsList)
        settingsList.layoutManager = LinearLayoutManager(requireContext())
        
        // Create list of settings items
        val settingsItems = listOf(
            SettingsItem("Notifications", "Manage your notification preferences", R.drawable.ic_notifications),
            SettingsItem("Privacy", "Manage your privacy settings", R.drawable.ic_privacy),
            SettingsItem("About", "Learn more about the app", R.drawable.ic_info)
        )
        
        // Create adapter for settings items
        // Note: SettingsAdapter needs to be implemented
        // settingsList.adapter = SettingsAdapter(settingsItems) { item ->
        //     when(item.title) {
        //         "Notifications" -> handleNotificationsClick()
        //         "Privacy" -> handlePrivacyClick()
        //         "About" -> handleAboutClick()
        //     }
        // }
    }

    private fun handleProfileClick() {
        // TODO: Implement profile editing functionality
    }
    
    private fun handleLogoutClick() {
        // Log out user
        auth.signOut()
        // Navigate to login activity
        val intent = Intent(requireContext(), LoginActivity::class.java)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        startActivity(intent)
    }
    
    // Data class for settings items
    data class SettingsItem(
        val title: String,
        val description: String,
        val iconResId: Int
    )
}
