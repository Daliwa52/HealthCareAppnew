package com.nipa.healthcareapp;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentTransaction;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.snackbar.Snackbar;

// R class needs to be imported if not in the same package, or use fully qualified names.
// For this context, assuming R is available from com.nipa.healthcareapp.R
// import com.nipa.healthcareapp.R;

public abstract class BaseActivity extends AppCompatActivity {

    protected View loadingContainer;
    protected View errorContainer;
    protected View contentContainer;
    protected View progressBar; // Added from Kotlin version
    protected TextView loadingText;
    protected TextView errorTitle;
    protected TextView errorMessage;
    protected Button errorRetryButton; // Changed from View to Button for type safety

    // Interface for dialog callbacks
    public interface DialogCallback {
        void execute();
    }

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // BaseActivity provides its own layout
        setContentView(R.layout.activity_base);

        // Initialize views from activity_base.xml
        loadingContainer = findViewById(R.id.loadingContainer);
        errorContainer = findViewById(R.id.errorContainer);
        contentContainer = findViewById(R.id.contentContainer);
        progressBar = findViewById(R.id.progressBar); // Initialize progressBar
        loadingText = findViewById(R.id.loadingText); // This should be a TextView
        errorTitle = findViewById(R.id.errorTitle);   // This should be a TextView
        errorMessage = findViewById(R.id.errorMessage); // This should be a TextView
        errorRetryButton = findViewById(R.id.retryButton); // This should be a Button

        if (errorRetryButton != null) {
            errorRetryButton.setOnClickListener(v -> onRetry());
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Coroutine job cancellation removed as per instructions
    }

    protected void showError(String message) {
        hideLoading(); // As per Kotlin version
        if (errorContainer != null) errorContainer.setVisibility(View.VISIBLE);
        if (contentContainer != null) contentContainer.setVisibility(View.GONE); // Explicitly hide content

        if (errorTitle != null) errorTitle.setText(getString(R.string.error));
        if (errorMessage != null) errorMessage.setText(message);
    }

    protected void showLoading(String message) {
        if (errorContainer != null) errorContainer.setVisibility(View.GONE);
        if (contentContainer != null) contentContainer.setVisibility(View.GONE);
        if (loadingContainer != null) loadingContainer.setVisibility(View.VISIBLE);

        if (loadingText != null) loadingText.setText(message);
    }

    // Overload for default loading message
    protected void showLoading() {
        // Assuming R.string.loading exists, as per Kotlin version
        showLoading(getString(R.string.loading));
    }

    protected void hideLoading() {
        if (loadingContainer != null) loadingContainer.setVisibility(View.GONE);
        // Content visibility is handled by showContent or showError explicitly
    }

    protected void showContent() {
        if (errorContainer != null) errorContainer.setVisibility(View.GONE);
        if (loadingContainer != null) loadingContainer.setVisibility(View.GONE);
        if (contentContainer != null) contentContainer.setVisibility(View.VISIBLE);
    }

    protected void showSnackbar(String message, int duration) {
        Snackbar.make(findViewById(android.R.id.content), message, duration).show();
    }

    // Overload for default duration
    protected void showSnackbar(String message) {
        showSnackbar(message, Snackbar.LENGTH_LONG);
    }

    protected void showAlertDialog(
            @NonNull String title,
            @NonNull String message,
            @NonNull String positiveText,
            @Nullable String negativeText,
            @Nullable DialogCallback onPositive,
            @Nullable DialogCallback onNegative) {

        MaterialAlertDialogBuilder builder = new MaterialAlertDialogBuilder(this);
        builder.setTitle(title);
        builder.setMessage(message);
        builder.setPositiveButton(positiveText, (dialog, which) -> {
            if (onPositive != null) {
                onPositive.execute();
            }
            // Dialog dismisses automatically by default after button click
        });
        if (negativeText != null) {
            builder.setNegativeButton(negativeText, (dialog, which) -> {
                if (onNegative != null) {
                    onNegative.execute();
                }
                // Dialog dismisses automatically
            });
        }
        // Removed setCancelable(false) to match Kotlin version's default behavior
        builder.show();
    }

    // Overload for simple dialog with only positive button and default text
    protected void showAlertDialog(
            @NonNull String title,
            @NonNull String message,
            @Nullable DialogCallback onPositive) {
        showAlertDialog(title, message, getString(R.string.ok), null, onPositive, null);
    }

    // Overload for informational dialog with only OK button
    protected void showAlertDialog(
            @NonNull String title,
            @NonNull String message) {
        showAlertDialog(title, message, getString(android.R.string.ok), null, null, null);
    }

    protected void onRetry() {
        // To be overridden by subclasses to handle retry action
    }

    // Using R.id.contentContainer as per Kotlin, and keeping addToBackStack overload
    protected void replaceFragment(@NonNull Fragment fragment, @NonNull String tag, boolean addToBackStack) {
        FragmentManager fragmentManager = getSupportFragmentManager();
        FragmentTransaction transaction = fragmentManager.beginTransaction();
        transaction.replace(R.id.contentContainer, fragment, tag);
        if (addToBackStack) {
            transaction.addToBackStack(tag);
        }
        transaction.commit();
    }

    protected void replaceFragment(@NonNull Fragment fragment, @NonNull String tag) {
        replaceFragment(fragment, tag, false); // Default to not adding to back stack
    }

    protected void navigateTo(@NonNull Class<?> activityClass, @Nullable Bundle args) {
        Intent intent = new Intent(this, activityClass);
        if (args != null) {
            intent.putExtras(args);
        }
        startActivity(intent);
    }

    protected void navigateTo(@NonNull Class<?> activityClass) {
        navigateTo(activityClass, null);
    }

    // Using onBackPressedDispatcher as per Kotlin version
    protected void navigateUp() {
        getOnBackPressedDispatcher().onBackPressed();
    }
}
