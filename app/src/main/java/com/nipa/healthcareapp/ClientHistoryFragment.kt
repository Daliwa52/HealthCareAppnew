package com.nipa.healthcareapp

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.data.models.ClientHistoryItem

class ClientHistoryFragment : Fragment() {
    private lateinit var historyRecyclerView: RecyclerView
    private lateinit var historyAdapter: ClientHistoryAdapter
    private val db = FirebaseFirestore.getInstance()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_client_history, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        historyRecyclerView = view.findViewById(R.id.clientHistoryRecyclerView)
        historyRecyclerView.layoutManager = LinearLayoutManager(requireContext())
        historyAdapter = ClientHistoryAdapter()
        historyRecyclerView.adapter = historyAdapter

        loadClientHistory()
    }

    private fun loadClientHistory() {
        val userId = FirebaseAuth.getInstance().currentUser?.uid
        if (userId != null) {
            db.collection("client_history")
                .whereEqualTo("providerId", userId)
                .get()
                .addOnSuccessListener { result ->
                    val history = mutableListOf<ClientHistoryItem>()
                    for (document in result) {
                        val item = document.toObject(ClientHistoryItem::class.java)
                        history.add(item)
                    }
                    historyAdapter.submitList(history)
                }
                .addOnFailureListener { exception ->
                    // Handle error
                }
        }
    }
}
