package com.nipa.healthcareapp;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.AuthResult;
import com.google.firebase.auth.FirebaseAuth;
import com.nipa.healthcareapp.databinding.ActivityLoginBinding;

public class LoginActivity extends AppCompatActivity {
    private FirebaseAuth auth;
    private ActivityLoginBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        auth = FirebaseAuth.getInstance();

        binding.btnLogin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String email = binding.etEmail.getText().toString().trim();
                String password = binding.etPassword.getText().toString().trim();

                if (email.isEmpty() || password.isEmpty()) {
                    Toast.makeText(LoginActivity.this, "Please fill all fields", Toast.LENGTH_SHORT).show();
                    return;
                }

                auth.signInWithEmailAndPassword(email, password)
                    .addOnCompleteListener(LoginActivity.this, new OnCompleteListener<AuthResult>() {
                        @Override
                        public void onComplete(@NonNull Task<AuthResult> task) {
                            if (task.isSuccessful()) {
                                // Determine role from intent extra (passed from WelcomeActivity)
                                String role = getIntent().getStringExtra("role");

                                // Navigate to the appropriate dashboard based on role
                                // For now, using ProviderDashboardActivity as per original Kotlin code
                                // This might need refinement if PatientDashboardActivity should be chosen based on 'role'
                                if ("provider".equals(role)) {
                                    Intent intent = new Intent(LoginActivity.this, ProviderDashboardActivity.class);
                                    // intent.putExtra("role", role); // Optionally pass role to dashboard
                                    startActivity(intent);
                                } else if ("patient".equals(role)) {
                                    // Assuming PatientDashboardActivity exists and is the target for patients
                                    Intent intent = new Intent(LoginActivity.this, PatientDashboardActivity.class);
                                    // intent.putExtra("role", role); // Optionally pass role to dashboard
                                    startActivity(intent);
                                } else {
                                    // Fallback or default dashboard if role is not specified or unrecognized
                                    // Defaulting to ProviderDashboardActivity as in the original KT
                                    // Or show an error / go to a generic dashboard
                                    Intent intent = new Intent(LoginActivity.this, ProviderDashboardActivity.class);
                                    startActivity(intent);
                                }
                                finish();
                            } else {
                                Toast.makeText(LoginActivity.this, "Authentication failed.", Toast.LENGTH_SHORT).show();
                            }
                        }
                    });
            }
        });

        binding.tvRegister.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(LoginActivity.this, RegisterActivity.class);
                // Pass the role to RegisterActivity, which was originally passed to LoginActivity
                String currentRole = getIntent().getStringExtra("role");
                if (currentRole != null) {
                    intent.putExtra("role", currentRole);
                }
                startActivity(intent);
            }
        });
    }
}
