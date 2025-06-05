package com.nipa.healthcareapp;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.firebase.FirebaseApp;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.messaging.FirebaseMessaging;
import com.nipa.healthcareapp.utils.ErrorHandler;
import com.nipa.healthcareapp.utils.Logger;

import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private FirebaseAuth auth;
    private FirebaseFirestore db;
    private ErrorHandler errorHandler;
    private ExecutorService executorService;
    private Handler mainThreadHandler;

    private static final String[] REQUIRED_PERMISSIONS = {
            Manifest.permission.INTERNET,
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.CAMERA
    };
    private static final int PERMISSIONS_REQUEST_CODE = 1001;

    private ProgressBar progressBar;
    private View errorContainer;
    private TextView errorText;
    private Button retryButton;
    private View contentContainer;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        errorHandler = new ErrorHandler(this);
        executorService = Executors.newSingleThreadExecutor();
        mainThreadHandler = new Handler(Looper.getMainLooper());

        if (!checkPermissions()) {
            requestPermissions();
            return;
        }

        try {
            initializeViews();
        } catch (Exception e) {
            Logger.e("MainActivity", "Failed to initialize views", e);
            errorHandler.handleError(e);
            return; // Stop further execution if views can't be initialized
        }

        // Initialize Firebase
        try {
            FirebaseApp.initializeApp(this);
            auth = FirebaseAuth.getInstance();
            db = FirebaseFirestore.getInstance();

            // Initialize Firebase Cloud Messaging
            showLoading(true);
            executorService.execute(() -> {
                try {
                    String token = FirebaseMessaging.getInstance().getToken().getResult(); // Simplified, consider proper task handling
                    if (auth.getCurrentUser() != null && token != null) {
                        db.collection("users").document(auth.getCurrentUser().getUid())
                                .update("fcmToken", token)
                                .addOnCompleteListener(task -> {
                                    if (!task.isSuccessful()) {
                                        Logger.w("MainActivity", "FCM token update failed", task.getException());
                                    }
                                });
                    }
                    mainThreadHandler.post(this::handleAuthentication);
                } catch (Exception e) {
                    mainThreadHandler.post(() -> showError("Failed to initialize messaging: " + e.getMessage()));
                } finally {
                    mainThreadHandler.post(() -> showLoading(false));
                }
            });
        } catch (Exception e) {
            showError("Failed to initialize app: " + e.getMessage());
            showLoading(false); // Ensure loading is hidden on error
        }
    }

    private void initializeViews() {
        progressBar = findViewById(R.id.progressBar);
        errorContainer = findViewById(R.id.errorContainer);
        errorText = findViewById(R.id.errorText);
        retryButton = findViewById(R.id.retryButton);
        contentContainer = findViewById(R.id.contentContainer);

        retryButton.setOnClickListener(v -> recreate());
    }

    private void showLoading(boolean show) {
        progressBar.setVisibility(show ? View.VISIBLE : View.GONE);
        errorContainer.setVisibility(View.GONE);
        contentContainer.setVisibility(show ? View.GONE : View.VISIBLE);
    }

    private void showError(String message) {
        progressBar.setVisibility(View.GONE);
        errorContainer.setVisibility(View.VISIBLE);
        contentContainer.setVisibility(View.GONE);
        errorText.setText(message != null ? message : "An unknown error occurred");
    }

    private boolean checkPermissions() {
        for (String permission : REQUIRED_PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    private void requestPermissions() {
        ActivityCompat.requestPermissions(
                this,
                REQUIRED_PERMISSIONS,
                PERMISSIONS_REQUEST_CODE
        );
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSIONS_REQUEST_CODE) {
            boolean allGranted = true;
            for (int grantResult : grantResults) {
                if (grantResult != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }

            if (allGranted) {
                recreate();
            } else {
                showError("Required permissions not granted");
            }
        }
    }

    private void handleAuthentication() {
        if (auth.getCurrentUser() == null) {
            startActivity(new Intent(this, WelcomeActivity.class));
            finish();
            return;
        }

        String userRole = getIntent().getStringExtra("role");
        if (userRole == null) {
            showErrorDialog("Role not specified");
            // Consider not finishing immediately, or providing a way to retry role input if applicable
            // finish(); // Original Kotlin code finishes here
            return;
        }

        Intent intent;
        switch (userRole) {
            case "provider":
                intent = new Intent(this, ProviderDashboardActivity.class);
                break;
            case "patient":
                intent = new Intent(this, PatientDashboardActivity.class);
                break;
            default:
                showErrorDialog("Invalid role specified: " + userRole);
                // finish(); // Original Kotlin code finishes here
                return;
        }
        startActivity(intent);
        finish(); // Finish MainActivity after launching dashboard
    }

    private void showErrorDialog(String message) {
        new MaterialAlertDialogBuilder(this)
                .setTitle("Error")
                .setMessage(message)
                .setPositiveButton("OK", (dialog, which) -> finish())
                .setOnCancelListener(dialog -> finish()) // Ensure finish if dialog is cancelled
                .show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
        }
    }
}
