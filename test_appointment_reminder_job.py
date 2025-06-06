import unittest
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime, timedelta
import sqlite3

# Functions to be tested are in appointment_reminder_job
from appointment_reminder_job import send_reminders
# We will also patch functions imported by appointment_reminder_job

class TestAppointmentReminderJob(unittest.TestCase):

    # --- Test send_reminders scenarios ---

    @patch('appointment_reminder_job.send_sms_reminder')
    @patch('appointment_reminder_job.send_email_reminder')
    @patch('appointment_reminder_job.db_utils_appointment.mark_reminder_sent')
    @patch('appointment_reminder_job.db_utils_appointment.get_appointments_needing_reminders')
    @patch('appointment_reminder_job.get_db_connection')
    def test_send_reminders_success_multiple_appointments(
            self, mock_get_db_conn, mock_get_appts_needing_reminders,
            mock_mark_sent, mock_send_email, mock_send_sms):
        """
        Test successful sending of reminders for multiple appointments.
        """
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn # For 'with' statement

        # Configure mock_get_appointments_needing_reminders to return a list of mock appointments
        mock_appointments = [
            {
                "appointment_id": 101, "patient_id": 1, "provider_id": 20,
                "appointment_start_time": "2024-01-15 10:00:00",
                "reason_for_visit": "Annual Checkup",
                "patient_username": "John Doe", "provider_username": "Dr. Smith",
                "patient_email": "john.doe@example.com", "patient_phone": "555-0101",
                "last_reminder_sent_at": None
            },
            {
                "appointment_id": 102, "patient_id": 2, "provider_id": 21,
                "appointment_start_time": "2024-01-15 11:00:00",
                "reason_for_visit": "Follow-up",
                "patient_username": "Jane Roe", "provider_username": "Dr. Jones",
                "patient_email": "jane.roe@example.com", "patient_phone": "555-0102",
                "last_reminder_sent_at": "2024-01-10 09:00:00" # Old reminder
            }
        ]
        mock_get_appts_needing_reminders.return_value = mock_appointments
        mock_mark_sent.return_value = True # Simulate successful marking
        mock_send_email.return_value = True
        mock_send_sms.return_value = True

        # Call the main function
        send_reminders(time_window_start_hours_ahead=23, time_window_end_hours_ahead=24, reminder_grace_period_hours=2)

        # Assertions
        mock_get_db_conn.assert_called_once()
        mock_get_appts_needing_reminders.assert_called_once()
        # Check call args for get_appointments_needing_reminders based on datetime.now() is complex,
        # so we'll test that separately or trust the call was made.

        self.assertEqual(mock_send_email.call_count, 2)
        mock_send_email.assert_any_call(mock_appointments[0]["patient_email"], mock_appointments[0])
        mock_send_email.assert_any_call(mock_appointments[1]["patient_email"], mock_appointments[1])

        self.assertEqual(mock_send_sms.call_count, 2)
        mock_send_sms.assert_any_call(mock_appointments[0]["patient_phone"], mock_appointments[0])
        mock_send_sms.assert_any_call(mock_appointments[1]["patient_phone"], mock_appointments[1])

        self.assertEqual(mock_mark_sent.call_count, 2)
        mock_mark_sent.assert_any_call(mock_conn, mock_appointments[0]['appointment_id'])
        mock_mark_sent.assert_any_call(mock_conn, mock_appointments[1]['appointment_id'])

    @patch('appointment_reminder_job.send_sms_reminder')
    @patch('appointment_reminder_job.send_email_reminder')
    @patch('appointment_reminder_job.db_utils_appointment.mark_reminder_sent')
    @patch('appointment_reminder_job.db_utils_appointment.get_appointments_needing_reminders')
    @patch('appointment_reminder_job.get_db_connection')
    def test_send_reminders_no_appointments_found(
            self, mock_get_db_conn, mock_get_appts_needing_reminders,
            mock_mark_sent, mock_send_email, mock_send_sms):
        """
        Test behavior when no appointments are found needing reminders.
        """
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_get_appts_needing_reminders.return_value = [] # No appointments

        send_reminders() # Use default time windows

        mock_get_appts_needing_reminders.assert_called_once()
        mock_send_email.assert_not_called()
        mock_send_sms.assert_not_called()
        mock_mark_sent.assert_not_called()

    @patch('appointment_reminder_job.send_sms_reminder')
    @patch('appointment_reminder_job.send_email_reminder')
    @patch('appointment_reminder_job.db_utils_appointment.mark_reminder_sent')
    @patch('appointment_reminder_job.db_utils_appointment.get_appointments_needing_reminders')
    @patch('appointment_reminder_job.get_db_connection')
    def test_send_reminders_db_error_on_fetch(
            self, mock_get_db_conn, mock_get_appts_needing_reminders,
            mock_mark_sent, mock_send_email, mock_send_sms):
        """
        Test behavior when fetching appointments raises a database error.
        """
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_get_appts_needing_reminders.side_effect = sqlite3.Error("Simulated DB error on fetch")

        send_reminders()

        mock_get_appts_needing_reminders.assert_called_once()
        mock_send_email.assert_not_called()
        mock_send_sms.assert_not_called()
        mock_mark_sent.assert_not_called()
        # The job should print an error message, which could be captured by mocking print if needed.

    @patch('appointment_reminder_job.send_sms_reminder')
    @patch('appointment_reminder_job.send_email_reminder')
    @patch('appointment_reminder_job.db_utils_appointment.mark_reminder_sent')
    @patch('appointment_reminder_job.db_utils_appointment.get_appointments_needing_reminders')
    @patch('appointment_reminder_job.get_db_connection')
    def test_send_reminders_db_error_on_mark_sent(
            self, mock_get_db_conn, mock_get_appts_needing_reminders,
            mock_mark_sent, mock_send_email, mock_send_sms):
        """
        Test behavior when marking a reminder as sent raises a database error.
        The job should attempt to process other appointments if one mark_reminder_sent fails.
        """
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        mock_appointments = [
            {"appointment_id": 101, "patient_email": "test1@example.com", "patient_phone": "111"},
            {"appointment_id": 102, "patient_email": "test2@example.com", "patient_phone": "222"}
        ]
        mock_get_appts_needing_reminders.return_value = mock_appointments

        # Simulate error on first call to mark_reminder_sent, success on second
        mock_mark_sent.side_effect = [sqlite3.Error("Simulated DB error on mark_sent"), True]
        mock_send_email.return_value = True # Assume notifications send successfully
        mock_send_sms.return_value = True

        send_reminders()

        self.assertEqual(mock_send_email.call_count, 2) # Both should be attempted
        self.assertEqual(mock_send_sms.call_count, 2)
        self.assertEqual(mock_mark_sent.call_count, 2) # Both should be attempted
        mock_mark_sent.assert_any_call(mock_conn, 101)
        mock_mark_sent.assert_any_call(mock_conn, 102)
        # Error message for the failed mark_sent would be printed by the job.

    @patch('appointment_reminder_job.send_sms_reminder')
    @patch('appointment_reminder_job.send_email_reminder')
    @patch('appointment_reminder_job.db_utils_appointment.mark_reminder_sent')
    @patch('appointment_reminder_job.db_utils_appointment.get_appointments_needing_reminders')
    @patch('appointment_reminder_job.get_db_connection')
    def test_send_reminders_missing_contact_info(
            self, mock_get_db_conn, mock_get_appts_needing_reminders,
            mock_mark_sent, mock_send_email, mock_send_sms):
        """
        Test that reminders are skipped if contact info is missing, but marking still occurs if one was sent.
        """
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_appointments = [
            {"appointment_id": 101, "patient_email": None, "patient_phone": "111-2222"}, # No email
            {"appointment_id": 102, "patient_email": "test2@example.com", "patient_phone": None}, # No phone
            {"appointment_id": 103, "patient_email": None, "patient_phone": None} # No contact
        ]
        mock_get_appts_needing_reminders.return_value = mock_appointments
        mock_mark_sent.return_value = True
        mock_send_email.return_value = True
        mock_send_sms.return_value = True

        send_reminders()

        # Email should only be called for appt 102
        mock_send_email.assert_called_once_with(mock_appointments[1]["patient_email"], mock_appointments[1])

        # SMS should only be called for appt 101
        mock_send_sms.assert_called_once_with(mock_appointments[0]["patient_phone"], mock_appointments[0])

        # mark_reminder_sent should be called for appt 101 and 102, but not 103
        self.assertEqual(mock_mark_sent.call_count, 2)
        mock_mark_sent.assert_any_call(mock_conn, 101)
        mock_mark_sent.assert_any_call(mock_conn, 102)

    @patch('appointment_reminder_job.db_utils_appointment.get_appointments_needing_reminders')
    @patch('appointment_reminder_job.get_db_connection')
    @patch('appointment_reminder_job.datetime') # Patch datetime module used in send_reminders
    def test_send_reminders_time_window_calculation(
            self, mock_datetime_module, mock_get_db_conn, mock_get_appts):
        """
        Test that the time window for fetching appointments is calculated correctly.
        """
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        # Fix current time for predictable calculations
        fixed_now = datetime(2024, 1, 1, 10, 0, 0) # 10:00 AM
        mock_datetime_module.now.return_value = fixed_now
        # Ensure timedelta can still be used by other parts of the code or the module itself
        mock_datetime_module.timedelta = timedelta


        mock_get_appts.return_value = [] # No appointments needed for this test of args

        start_hours = 23
        end_hours = 24
        grace_hours = 2
        send_reminders(
            time_window_start_hours_ahead=start_hours,
            time_window_end_hours_ahead=end_hours,
            reminder_grace_period_hours=grace_hours
        )

        expected_window_start_dt = fixed_now + timedelta(hours=start_hours)
        expected_window_end_dt = fixed_now + timedelta(hours=end_hours)
        expected_window_start_iso = expected_window_start_dt.strftime('%Y-%m-%d %H:%M:%S')
        expected_window_end_iso = expected_window_end_dt.strftime('%Y-%m-%d %H:%M:%S')

        mock_get_appts.assert_called_once_with(
            mock_conn,
            expected_window_start_iso,
            expected_window_end_iso,
            grace_hours
        )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
