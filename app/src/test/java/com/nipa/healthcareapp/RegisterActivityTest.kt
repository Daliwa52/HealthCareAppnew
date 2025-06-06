package com.nipa.healthcareapp

import android.os.Build
import android.widget.Button
import android.widget.EditText
import androidx.test.core.app.ApplicationProvider
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import io.mockk.mockk
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [Build.VERSION_CODES.P]) // SDK 28
class RegisterActivityTest {

    private lateinit var activity: RegisterActivity
    private lateinit var etName: EditText
    private lateinit var etEmail: EditText
    private lateinit var etPassword: EditText
    private lateinit var etConfirmPassword: EditText
    private lateinit var btnRegister: Button

    // Mock Firebase instances (though not strictly used for validation logic testing here)
    private lateinit var mockAuth: FirebaseAuth
    private lateinit var mockDb: FirebaseFirestore

    @Before
    fun setUp() {
        // Mock Firebase (not directly used by validation but good practice if activity initializes them)
        mockAuth = mockk(relaxed = true)
        mockDb = mockk(relaxed = true)

        // It's tricky to directly inject mocks into Activity fields not designed for it without reflection or DI.
        // For these tests, we are focusing on UI validation which happens before Firebase interaction.
        // If RegisterActivity initializes its own auth/db, those will be the actual Firebase instances (or null if not configured in test).
        // This is generally fine as long as our button click doesn't lead to a crash due to unmocked Firebase.
        // Robolectric often handles basic Firebase initializations to non-null (but non-functional) objects.

        activity = Robolectric.buildActivity(RegisterActivity::class.java).create().resume().get()

        // Access views. Assuming public binding properties. If not, use findViewById.
        // Example: activity.binding.etName, if binding is public.
        // For this setup, I will assume direct access or findViewById if binding isn't easily available in test.
        // Based on previous files, RegisterActivity uses 'binding.etName', etc.
        // Robolectric should allow access to these if the binding class is generated and accessible.
        etName = activity.binding.etName
        etEmail = activity.binding.etEmail
        etPassword = activity.binding.etPassword
        etConfirmPassword = activity.binding.etConfirmPassword
        btnRegister = activity.binding.btnRegister
    }

    @Test
    fun register_emptyName_setsNameError() {
        etName.setText("")
        etEmail.setText("test@example.com")
        etPassword.setText("password123")
        etConfirmPassword.setText("password123")

        btnRegister.performClick()

        assertNotNull(etName.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_name_required), etName.error)
    }

    @Test
    fun register_emptyEmail_setsEmailError() {
        etName.setText("Test User")
        etEmail.setText("")
        etPassword.setText("password123")
        etConfirmPassword.setText("password123")

        btnRegister.performClick()

        assertNotNull(etEmail.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_invalid_email), etEmail.error)
    }

    @Test
    fun register_invalidEmail_setsEmailError() {
        etName.setText("Test User")
        etEmail.setText("invalidemail")
        etPassword.setText("password123")
        etConfirmPassword.setText("password123")

        btnRegister.performClick()

        assertNotNull(etEmail.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_invalid_email), etEmail.error)
    }

    @Test
    fun register_emptyPassword_setsPasswordError() {
        etName.setText("Test User")
        etEmail.setText("test@example.com")
        etPassword.setText("")
        etConfirmPassword.setText("")

        btnRegister.performClick()

        assertNotNull(etPassword.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_password_required), etPassword.error)
    }

    @Test
    fun register_shortPassword_setsPasswordError() {
        etName.setText("Test User")
        etEmail.setText("test@example.com")
        etPassword.setText("12345") // Less than 6 chars
        etConfirmPassword.setText("12345")

        btnRegister.performClick()

        assertNotNull(etPassword.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_password_length), etPassword.error)
    }

    @Test
    fun register_mismatchedPasswords_setsConfirmPasswordError() {
        etName.setText("Test User")
        etEmail.setText("test@example.com")
        etPassword.setText("password123")
        etConfirmPassword.setText("password456") // Mismatch

        btnRegister.performClick()

        assertNotNull(etConfirmPassword.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_passwords_no_match), etConfirmPassword.error)
    }

    @Test
    fun register_emptyConfirmPassword_setsConfirmPasswordError() {
        etName.setText("Test User")
        etEmail.setText("test@example.com")
        etPassword.setText("password123")
        etConfirmPassword.setText("") // Empty confirm password

        btnRegister.performClick()

        assertNotNull(etConfirmPassword.error)
        // The error message for empty confirm password was R.string.error_passwords_no_match in RegisterActivity
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_passwords_no_match), etConfirmPassword.error)
    }

    @Test
    fun register_validInputs_noErrorMessagesSet() {
        etName.setText("Test User")
        etEmail.setText("test@example.com")
        etPassword.setText("password123")
        etConfirmPassword.setText("password123")

        btnRegister.performClick()

        // Assert that no error messages are set on any field
        // This implies validation passed and Firebase call would be attempted
        assertNull("Name field should have no error", etName.error)
        assertNull("Email field should have no error", etEmail.error)
        assertNull("Password field should have no error", etPassword.error)
        assertNull("Confirm Password field should have no error", etConfirmPassword.error)
    }
}
