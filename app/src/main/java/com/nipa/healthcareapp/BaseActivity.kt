package com.nipa.healthcareapp

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.navigation.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlin.coroutines.CoroutineContext

abstract class BaseActivity : AppCompatActivity(), CoroutineScope {
    private lateinit var job: Job
    private lateinit var loadingContainer: View
    private lateinit var errorContainer: View
    private lateinit var contentContainer: View
    private lateinit var progressBar: View
    private lateinit var loadingText: View
    private lateinit var errorTitle: View
    private lateinit var errorMessage: View
    private lateinit var retryButton: View

    override val coroutineContext: CoroutineContext
        get() = Dispatchers.Main + job

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        job = Job()
        
        setContentView(R.layout.activity_base)
        
        // Initialize views
        loadingContainer = findViewById(R.id.loadingContainer)
        errorContainer = findViewById(R.id.errorContainer)
        contentContainer = findViewById(R.id.contentContainer)
        progressBar = findViewById(R.id.progressBar)
        loadingText = findViewById(R.id.loadingText)
        errorTitle = findViewById(R.id.errorTitle)
        errorMessage = findViewById(R.id.errorMessage)
        retryButton = findViewById(R.id.retryButton)

        // Set up retry button
        retryButton.setOnClickListener {
            onRetry()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        job.cancel()
    }

    protected fun showError(message: String) {
        hideLoading()
        errorContainer.visibility = View.VISIBLE
        
        (errorTitle as TextView).text = getString(R.string.error)
        (errorMessage as TextView).text = message
    }

    protected fun showLoading(message: String = getString(R.string.loading)) {
        errorContainer.visibility = View.GONE
        loadingContainer.visibility = View.VISIBLE
        contentContainer.visibility = View.GONE
        
        (loadingText as TextView).text = message
    }

    protected fun hideLoading() {
        loadingContainer.visibility = View.GONE
        contentContainer.visibility = View.VISIBLE
    }

    protected fun showContent() {
        errorContainer.visibility = View.GONE
        loadingContainer.visibility = View.GONE
        contentContainer.visibility = View.VISIBLE
    }

    protected fun showSnackbar(message: String, duration: Int = Snackbar.LENGTH_LONG) {
        Snackbar.make(
            findViewById(android.R.id.content),
            message,
            duration
        ).show()
    }

    protected fun showAlertDialog(
        title: String,
        message: String,
        positiveText: String = getString(R.string.ok),
        negativeText: String? = null,
        onPositive: () -> Unit = {},
        onNegative: (() -> Unit)? = null
    ) {
        MaterialAlertDialogBuilder(this)
            .setTitle(title)
            .setMessage(message)
            .setPositiveButton(positiveText) { _, _ ->
                onPositive()
            }
            .apply {
                if (negativeText != null) {
                    setNegativeButton(negativeText) { _, _ ->
                        onNegative?.invoke()
                    }
                }
            }
            .show()
    }

    protected fun onRetry() {
        // Override in subclasses to handle retry action
    }

    protected fun replaceFragment(fragment: androidx.fragment.app.Fragment, tag: String) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.contentContainer, fragment, tag)
            .commit()
    }

    /**
     * Navigation alternatives for activities without a Navigation Host Fragment
     */
    protected fun navigateTo(activityClass: Class<*>, args: Bundle? = null) {
        val intent = Intent(this, activityClass)
        if (args != null) {
            intent.putExtras(args)
        }
        startActivity(intent)
    }

    protected fun navigateUp() {
        onBackPressedDispatcher.onBackPressed()
    }
}
