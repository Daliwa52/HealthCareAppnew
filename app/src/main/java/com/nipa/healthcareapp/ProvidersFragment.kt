package com.nipa.healthcareapp

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.firebase.firestore.FirebaseFirestore
import com.nipa.healthcareapp.data.models.Provider

class ProvidersFragment : Fragment() {
    private lateinit var providerRecyclerView: RecyclerView
    private lateinit var providerAdapter: ProviderAdapter
    private val db = FirebaseFirestore.getInstance()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_providers, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        providerRecyclerView = view.findViewById(R.id.providersRecyclerView)
        providerRecyclerView.layoutManager = LinearLayoutManager(requireContext())
        providerAdapter = ProviderAdapter()
        providerRecyclerView.adapter = providerAdapter

        loadProviders()
    }

    private fun loadProviders() {
        db.collection("providers")
            .get()
            .addOnSuccessListener { result ->
                val providers = mutableListOf<Provider>()
                for (document in result) {
                    val provider = document.toObject(Provider::class.java)
                    providers.add(provider)
                }
                providerAdapter.submitList(providers)
            }
            .addOnFailureListener { exception ->
                // Handle error
            }
    }
}
