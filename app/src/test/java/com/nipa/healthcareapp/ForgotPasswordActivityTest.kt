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
class ForgotPasswordActivityTest {

    private lateinit var activity: ForgotPasswordActivity
    private lateinit var etEmailForgotPassword: EditText
    private lateinit var btnResetPassword: Button

    @Before
    fun setUp() {
        activity = Robolectric.buildActivity(ForgotPasswordActivity::class.java).create().resume().get()

        // Using activity.binding.etEmailForgotPassword as per ForgotPasswordActivity structure
        etEmailForgotPassword = activity.binding.etEmailForgotPassword
        btnResetPassword = activity.binding.btnResetPassword
    }

    @Test
    fun forgotPassword_emptyEmail_setsEmailError() {
        etEmailForgotPassword.setText("")

        btnResetPassword.performClick()

        assertNotNull(etEmailForgotPassword.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_invalid_email_for_reset), etEmailForgotPassword.error)
    }

    @Test
    fun forgotPassword_invalidEmail_setsEmailError() {
        etEmailForgotPassword.setText("invalidemail")

        btnResetPassword.performClick()

        assertNotNull(etEmailForgotPassword.error)
        assertEquals(ApplicationProvider.getApplicationContext<android.content.Context>().getString(R.string.error_invalid_email_for_reset), etEmailForgotPassword.error)
    }

    @Test
    fun forgotPassword_validEmail_noErrorMessageSet() {
        etEmailForgotPassword.setText("test@example.com")

        btnResetPassword.performClick()

        // Assert that no error message is set on the email field
        // This implies validation passed and Firebase call would be attempted
        assertNull("Email field should have no error", etEmailForgotPassword.error)
    }
}
