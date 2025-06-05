package com.nipa.healthcareapp

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.FirebaseFirestoreException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import com.nipa.healthcareapp.data.models.Notification

class NotificationsFragment : Fragment() {
    private lateinit var notificationsRecyclerView: RecyclerView
    private lateinit var notificationsAdapter: NotificationsAdapter
    private val db = FirebaseFirestore.getInstance()
    private val auth = FirebaseAuth.getInstance()
    private val coroutineScope = CoroutineScope(Dispatchers.Main)

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_notifications, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        notificationsRecyclerView = view.findViewById(R.id.notificationsRecyclerView)
        notificationsRecyclerView.layoutManager = LinearLayoutManager(requireContext())
        notificationsAdapter = NotificationsAdapter()
        notificationsRecyclerView.adapter = notificationsAdapter

        if (auth.currentUser == null) {
            Toast.makeText(requireContext(), "Please sign in to view notifications", Toast.LENGTH_LONG).show()
            return
        }

        loadNotifications()
    }

    private fun loadNotifications() {
        coroutineScope.launch {
            try {
                val userId = auth.currentUser?.uid ?: return@launch
                val result = db.collection("notifications")
                    .whereEqualTo("userId", userId)
                    .get()
                    .await()

                val notifications = mutableListOf<Notification>()
                for (document in result) {
                    val notification = document.toObject(Notification::class.java)
                    notifications.add(notification)
                }
                notificationsAdapter.submitList(notifications)
            } catch (e: FirebaseFirestoreException) {
                when (e.code) {
                    FirebaseFirestoreException.Code.UNAVAILABLE -> {
                        Toast.makeText(requireContext(), "No internet connection", Toast.LENGTH_LONG).show()
                    }
                    else -> {
                        Toast.makeText(requireContext(), "Failed to load notifications: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "An unexpected error occurred: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }
}
