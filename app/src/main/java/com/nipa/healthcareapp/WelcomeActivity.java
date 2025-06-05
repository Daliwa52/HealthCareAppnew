package com.nipa.healthcareapp;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.RadioButton;
import androidx.appcompat.app.AppCompatActivity;

// It's good practice to ensure LoginActivity and RegisterActivity are imported if they are in the same package.
// However, explicit imports for classes in the same package are not strictly necessary.
// import com.nipa.healthcareapp.LoginActivity;
// import com.nipa.healthcareapp.RegisterActivity;

public class WelcomeActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_welcome);

        final RadioButton radioCareProvider = findViewById(R.id.radioCareProvider);
        final RadioButton radioPatient = findViewById(R.id.radioPatient); // Assuming R.id.radioPatient exists
        Button btnLogin = findViewById(R.id.btnLogin);
        Button btnRegister = findViewById(R.id.btnRegister);

        btnLogin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String role = radioCareProvider.isChecked() ? "provider" : "patient";
                Intent intent = new Intent(WelcomeActivity.this, LoginActivity.class);
                intent.putExtra("role", role);
                startActivity(intent);
            }
        });

        btnRegister.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String role = radioCareProvider.isChecked() ? "provider" : "patient";
                Intent intent = new Intent(WelcomeActivity.this, RegisterActivity.class);
                intent.putExtra("role", role);
                startActivity(intent);
            }
        });
    }
}
