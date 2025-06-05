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
import com.nipa.healthcareapp.data.models.Chat

class ChatsFragment : Fragment() {
    private lateinit var chatsRecyclerView: RecyclerView
    private lateinit var chatsAdapter: ChatsAdapter
    private val db = FirebaseFirestore.getInstance()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_chats, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        chatsRecyclerView = view.findViewById(R.id.chatsRecyclerView)
        chatsRecyclerView.layoutManager = LinearLayoutManager(requireContext())
        chatsAdapter = ChatsAdapter()
        chatsRecyclerView.adapter = chatsAdapter

        loadChats()
    }

    private fun loadChats() {
        val userId = FirebaseAuth.getInstance().currentUser?.uid
        if (userId != null) {
            db.collection("chats")
                .whereArrayContains("participants", userId)
                .get()
                .addOnSuccessListener { result ->
                    val chats = mutableListOf<Chat>()
                    for (document in result) {
                        val chat = document.toObject(Chat::class.java)
                        chats.add(chat)
                    }
                    chatsAdapter.submitList(chats)
                }
                .addOnFailureListener { exception ->
                    // Handle error
                }
        }
    }
}
