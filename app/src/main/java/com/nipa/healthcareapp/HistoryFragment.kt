package com.nipa.healthcareapp

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import com.google.firebase.auth.FirebaseAuth

/**
 * Fragment that serves as a container for different types of history views
 * (Client history for providers, Visit history for patients)
 */
class HistoryFragment : Fragment() {
    private val auth = FirebaseAuth.getInstance()
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_history, container, false)
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Check if user is a provider or patient
        val currentUser = auth.currentUser
        if (currentUser != null) {
            // Determine user type and load appropriate fragment
            determineUserTypeAndLoadHistory(currentUser.uid)
        }
    }
    
    private fun determineUserTypeAndLoadHistory(userId: String) {
        // In a real implementation, this would query a users collection
        // to determine if the user is a provider or patient
        // For now, we'll just load the ClientHistoryFragment
        
        val transaction = childFragmentManager.beginTransaction()
        transaction.replace(R.id.history_container, ClientHistoryFragment())
        transaction.commit()
    }
}
