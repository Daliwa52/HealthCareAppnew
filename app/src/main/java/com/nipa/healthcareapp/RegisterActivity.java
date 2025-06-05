package com.nipa.healthcareapp;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.OnFailureListener;
import com.google.android.gms.tasks.OnSuccessListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.AuthResult;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.firestore.FirebaseFirestore;
import com.nipa.healthcareapp.databinding.ActivityRegisterBinding;
import java.util.HashMap;
import java.util.Map;

public class RegisterActivity extends AppCompatActivity {
    private FirebaseAuth auth;
    private FirebaseFirestore db;
    private ActivityRegisterBinding binding;
    private String userRole;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityRegisterBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        auth = FirebaseAuth.getInstance();
        db = FirebaseFirestore.getInstance();

        userRole = getIntent().getStringExtra("role");
        // It's good to have a default or handle null userRole if necessary
        if (userRole == null) {
            // Default to "patient" or show an error, depending on desired app flow
            userRole = "patient"; // Example default
            // Toast.makeText(this, "User role not specified, defaulting to patient.", Toast.LENGTH_SHORT).show();
        }


        binding.btnRegister.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String email = binding.etEmail.getText().toString().trim();
                String password = binding.etPassword.getText().toString().trim();
                String name = binding.etName.getText().toString().trim();

                if (TextUtils.isEmpty(email) || TextUtils.isEmpty(password) || TextUtils.isEmpty(name)) {
                    Toast.makeText(RegisterActivity.this, "Please fill all fields", Toast.LENGTH_SHORT).show();
                    return;
                }

                auth.createUserWithEmailAndPassword(email, password)
                    .addOnCompleteListener(RegisterActivity.this, new OnCompleteListener<AuthResult>() {
                        @Override
                        public void onComplete(@NonNull Task<AuthResult> task) {
                            if (task.isSuccessful()) {
                                FirebaseUser firebaseUser = auth.getCurrentUser();
                                if (firebaseUser != null && firebaseUser.getUid() != null && !firebaseUser.getUid().isEmpty()) {
                                    String userId = firebaseUser.getUid();
                                    Map<String, Object> userData = new HashMap<>();
                                    userData.put("name", name);
                                    userData.put("role", userRole);
                                    userData.put("email", email);
                                    // Potentially add fcmToken here if obtained during registration

                                    db.collection("users")
                                        .document(userId)
                                        .set(userData)
                                        .addOnSuccessListener(new OnSuccessListener<Void>() {
                                            @Override
                                            public void onSuccess(Void aVoid) {
                                                Toast.makeText(RegisterActivity.this, "Registration successful.", Toast.LENGTH_SHORT).show();
                                                Intent intent;
                                                if ("provider".equals(userRole)) {
                                                    intent = new Intent(RegisterActivity.this, ProviderDashboardActivity.class);
                                                } else if ("patient".equals(userRole)) {
                                                    intent = new Intent(RegisterActivity.this, PatientDashboardActivity.class);
                                                } else {
                                                    // Default or error
                                                    intent = new Intent(RegisterActivity.this, LoginActivity.class);
                                                    intent.putExtra("role", userRole); // Pass role back to login
                                                }
                                                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                                                startActivity(intent);
                                                finish();
                                            }
                                        })
                                        .addOnFailureListener(new OnFailureListener() {
                                            @Override
                                            public void onFailure(@NonNull Exception e) {
                                                Toast.makeText(RegisterActivity.this, "Registration failed (DB): " + e.getMessage(), Toast.LENGTH_LONG).show();
                                            }
                                        });
                                } else {
                                    Toast.makeText(RegisterActivity.this, "Registration failed: User ID not found.", Toast.LENGTH_LONG).show();
                                }
                            } else {
                                Toast.makeText(RegisterActivity.this, "Registration failed: " + task.getException().getMessage(), Toast.LENGTH_LONG).show();
                            }
                        }
                    });
            }
        });

        binding.tvLogin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(RegisterActivity.this, LoginActivity.class);
                intent.putExtra("role", userRole); // Pass the current role back to LoginActivity
                startActivity(intent);
                // finish(); // Optional: finish RegisterActivity when going to Login
            }
        });
    }
}
