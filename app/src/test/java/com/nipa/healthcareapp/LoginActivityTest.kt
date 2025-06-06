package com.nipa.healthcareapp

import android.os.Build
import android.widget.Button
import android.widget.EditText
import androidx.test.core.app.ApplicationProvider
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
class LoginActivityTest {

    private lateinit var activity: LoginActivity
    private lateinit var etEmailLogin: EditText
    private lateinit var etPasswordLogin: EditText
    private lateinit var btnLogin: Button

    @Before
    fun setUp() {
        activity = Robolectric.buildActivity(LoginActivity::class.java).create().resume().get()

        // Using activity.binding.etEmail and activity.binding.etPassword as per LoginActivity structure
        etEmailLogin = activity.binding.etEmail
        etPasswordLogin = activity.binding.etPassword
        btnLogin = activity.binding.btnLogin
    }

    @Test
    fun login_emptyEmail_setsEmailError() {
        etEmailLogin.setText("")
        etPasswordLogin.setText("password123")

        btnLogin.performClick()

        assertNotNull(etEmailLogin.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_invalid_email), etEmailLogin.error)
    }

    @Test
    fun login_invalidEmail_setsEmailError() {
        etEmailLogin.setText("invalidemail")
        etPasswordLogin.setText("password123")

        btnLogin.performClick()

        assertNotNull(etEmailLogin.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_invalid_email), etEmailLogin.error)
    }

    @Test
    fun login_emptyPassword_setsPasswordError() {
        etEmailLogin.setText("test@example.com")
        etPasswordLogin.setText("")

        btnLogin.performClick()

        assertNotNull(etPasswordLogin.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_password_required), etPasswordLogin.error)
    }

    @Test
    fun login_validInputs_noErrorMessagesSet() {
        etEmailLogin.setText("test@example.com")
        etPasswordLogin.setText("password123")

        btnLogin.performClick()

        // Assert that no error messages are set on any field
        // This implies validation passed and Firebase call would be attempted
        assertNull("Email field should have no error", etEmailLogin.error)
        assertNull("Password field should have no error", etPasswordLogin.error)
    }
}
