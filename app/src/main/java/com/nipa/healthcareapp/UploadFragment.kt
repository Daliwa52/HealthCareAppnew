package com.nipa.healthcareapp

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.nipa.healthcareapp.BaseFragment
import com.nipa.healthcareapp.databinding.FragmentUploadBinding
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.storage.FirebaseStorage
import com.google.firebase.storage.StorageReference
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import java.util.*

class UploadFragment : BaseFragment() {
    private var _binding: FragmentUploadBinding? = null
    private val binding get() = _binding!!
    private lateinit var auth: FirebaseAuth
    private lateinit var storage: FirebaseStorage
    private lateinit var storageRef: StorageReference
    private var currentFileUri: Uri? = null

    private val pickImage = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val data = result.data
            data?.data?.let { uri ->
                currentFileUri = uri
                uploadFile(uri, "photos")
            }
        }
    }

    private val pickVideo = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val data = result.data
            data?.data?.let { uri ->
                currentFileUri = uri
                uploadFile(uri, "videos")
            }
        }
    }

    private val pickDocument = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val data = result.data
            data?.data?.let { uri ->
                currentFileUri = uri
                uploadFile(uri, "documents")
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentUploadBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        auth = FirebaseAuth.getInstance()
        storage = FirebaseStorage.getInstance()
        storageRef = storage.reference

        binding.apply {
            btnUploadPhoto.setOnClickListener {
                val intent = Intent(Intent.ACTION_PICK)
                intent.type = "image/*"
                pickImage.launch(intent)
            }

            btnUploadVideo.setOnClickListener {
                val intent = Intent(Intent.ACTION_PICK)
                intent.type = "video/*"
                pickVideo.launch(intent)
            }

            btnUploadDocument.setOnClickListener {
                val intent = Intent(Intent.ACTION_PICK)
                intent.type = "*/*"
                intent.putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("application/pdf", "application/msword"))
                pickDocument.launch(intent)
            }
        }
    }

    private fun uploadFile(fileUri: Uri, folder: String) {
        val userId = auth.currentUser?.uid ?: return
        val fileName = "${UUID.randomUUID()}"
        val fileRef = storageRef.child("$folder/$userId/$fileName")

        // Declare uploadTask here to be accessible in catch
        var uploadTask: com.google.firebase.storage.UploadTask? = null

        lifecycleScope.launch {
            try {
                // Show loading indicator
                showLoading(true)
                
                // Initialize and start upload
                uploadTask = fileRef.putFile(fileUri)
                uploadTask?.await() // Use safe call
                val downloadUrl = fileRef.downloadUrl.await()
                
                // Save metadata to Firestore
                val metadata = hashMapOf(
                    "userId" to userId,
                    "fileName" to fileName,
                    "fileType" to folder,
                    "uploadTime" to System.currentTimeMillis(),
                    "downloadUrl" to downloadUrl.toString()
                )
                
                val db = com.google.firebase.firestore.FirebaseFirestore.getInstance()
                db.collection("uploads")
                    .add(metadata)
                    .await()
                
                // Hide loading indicator and show success message
                showLoading(false)
                showSuccess("File uploaded successfully")
            } catch (e: Exception) {
                // Attempt to cancel the upload task if it was initiated
                uploadTask?.cancel()
                
                // Hide loading indicator and show error message
                showLoading(false)
                showError("Upload failed: ${e.message}")
            }
        }
    }

    private fun showSuccess(message: String) {
        // Using the showError method from BaseFragment to display success messages
        // Ideally, this would be a separate method in BaseFragment
        showError(message)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    override fun getLayoutId(): Int {
        return R.layout.fragment_upload
    }
}
