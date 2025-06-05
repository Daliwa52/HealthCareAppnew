package com.nipa.healthcareapp.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.nipa.healthcareapp.R
import com.nipa.healthcareapp.databinding.FragmentHomeBinding
import com.nipa.healthcareapp.viewmodel.HomeViewModel

class HomeFragment : Fragment() {
    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: HomeViewModel

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        viewModel = ViewModelProvider(this)[HomeViewModel::class.java]
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Setup view model observers
        viewModel.user.observe(viewLifecycleOwner) { user ->
            // Update UI with user data
            binding.tvWelcome.text = "Welcome, ${user?.name}"
        }
        
        // Setup quick actions
        binding.btnQuickAction1.setOnClickListener { 
            // Handle quick action 1
        }
        binding.btnQuickAction2.setOnClickListener { 
            // Handle quick action 2
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
