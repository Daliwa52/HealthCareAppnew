package com.nipa.healthcareapp.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import kotlinx.coroutines.launch

class HomeViewModel : ViewModel() {
    private val _user = MutableLiveData<User>()
    val user: LiveData<User> = _user

    private val auth = FirebaseAuth.getInstance()
    private val db = FirebaseFirestore.getInstance()

    init {
        loadUserData()
    }

    private fun loadUserData() {
        viewModelScope.launch {
            auth.currentUser?.let { user ->
                db.collection("users")
                    .document(user.uid)
                    .get()
                    .addOnSuccessListener { document ->
                        if (document.exists()) {
                            val userData = document.data
                            _user.value = User(
                                id = document.id,
                                name = userData?.get("name") as? String ?: "",
                                email = userData?.get("email") as? String ?: "",
                                role = userData?.get("role") as? String ?: "",
                                lastSeen = userData?.get("lastSeen") as? Long ?: 0
                            )
                        }
                    }
            }
        }
    }

    data class User(
        val id: String,
        val name: String,
        val email: String,
        val role: String,
        val lastSeen: Long
    )
}
