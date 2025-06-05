package com.nipa.healthcareapp

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SearchView
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.data.models.Provider
import com.nipa.healthcareapp.databinding.ActivitySearchBinding

class SearchActivity : AppCompatActivity() {
    private lateinit var binding: ActivitySearchBinding
    private lateinit var db: FirebaseFirestore
    private lateinit var searchAdapter: SearchAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySearchBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        db = FirebaseFirestore.getInstance()
        
        // Setup RecyclerView
        binding.recyclerView.apply {
            layoutManager = LinearLayoutManager(this@SearchActivity)
            setHasFixedSize(true)
        }
        
        // Initialize the adapter
        searchAdapter = SearchAdapter()
        binding.recyclerView.adapter = searchAdapter
        
        // Setup SearchView
        binding.searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                query?.let { searchUsers(it) }
                return true
            }

            override fun onQueryTextChange(newText: String?): Boolean {
                newText?.let { searchUsers(it) }
                return true
            }
        })
    }

    private fun searchUsers(query: String) {
        val searchQuery = query.toLowerCase()
        
        db.collection("users")
            .whereEqualTo("role", "provider")
            .get()
            .addOnSuccessListener { result ->
                val providers = result.documents.mapNotNull { document ->
                    val data = document.data
                    data?.let {
                        Provider(
                            id = document.id,
                            name = it["name"] as? String ?: "",
                            email = it["email"] as? String ?: "",
                            specialty = it["specialty"] as? String ?: "",
                            rating = (it["rating"] as? Double ?: 0.0).toFloat()
                        )
                    }
                }
                
                // Filter by search query
                val filteredProviders = providers.filter { 
                    it.name.toLowerCase().contains(searchQuery) || 
                    it.email.toLowerCase().contains(searchQuery) || 
                    it.specialty?.toLowerCase()?.contains(searchQuery) == true 
                }
                
                searchAdapter.submitList(filteredProviders)
            }
            .addOnFailureListener { e ->
                // Handle error
            }
    }
}

// Use Provider class from data.models package
