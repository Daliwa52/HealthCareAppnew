package com.nipa.healthcareapp

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

abstract class BaseFragment : Fragment() {
    private var _rootView: View? = null
    protected val rootView get() = _rootView!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _rootView = inflater.inflate(getLayoutId(), container, false)
        return _rootView!!
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _rootView = null
    }

    protected abstract fun getLayoutId(): Int

    protected fun showError(message: String) {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("Error")
            .setMessage(message)
            .setPositiveButton("OK") { dialog, _ -> dialog.dismiss() }
            .show()
    }

    private lateinit var loadingView: View
    private lateinit var errorView: View
    private lateinit var contentView: View

    protected fun setupViews() {
        loadingView = rootView.findViewById(R.id.loadingView)
        errorView = rootView.findViewById(R.id.errorView)
        contentView = rootView.findViewById(R.id.contentView)
    }

    protected fun showLoading(isLoading: Boolean) {
        loadingView.visibility = if (isLoading) View.VISIBLE else View.GONE
        contentView.visibility = if (isLoading) View.GONE else View.VISIBLE
        errorView.visibility = View.GONE
    }

    protected fun showError(error: Throwable) {
        showLoading(false)
        errorView.visibility = View.VISIBLE
        
        val errorText = error.message ?: "An error occurred"
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("Error")
            .setMessage(errorText)
            .setPositiveButton("Retry") { _, _ ->
                retryAction?.invoke()
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
            }
            .show()
    }

    protected var retryAction: (() -> Unit)? = null

    protected suspend fun <T> safeApiCall(call: suspend () -> T): Result<T> {
        return try {
            Result.success(call())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    protected suspend fun <T> executeWithLoading(call: suspend () -> T): Result<T> {
        return try {
            showLoading(true)
            Result.success(call())
        } catch (e: Exception) {
            showError(e)
            Result.failure(e)
        } finally {
            showLoading(false)
        }
    }
}
