import unittest
import json
import os
import sqlite3
from unittest.mock import patch, MagicMock, ANY

# Import the Flask app from appointment_api
# We also need to be able to modify its DB_NAME for testing context
from appointment_api import app
import appointment_api # To modify appointment_api.DB_NAME

TEST_API_DB_NAME = 'test_appointment_api_level.db'

class TestAppointmentAPI(unittest.TestCase):

    def setUp(self):
        """Set up test client and application context for each test."""
        self.app_context = app.app_context()
        self.app_context.push()

        app.config['TESTING'] = True
        # Override the DB_NAME in the appointment_api module for the duration of the test
        self.original_db_name = appointment_api.DB_NAME
        appointment_api.DB_NAME = TEST_API_DB_NAME

        self.client = app.test_client()

    def tearDown(self):
        """Clean up after each test."""
        # Restore the original DB_NAME
        appointment_api.DB_NAME = self.original_db_name
        self.app_context.pop()
        # Note: We are not creating/deleting the TEST_API_DB_NAME file here
        # because all DB interactions should be mocked. If a real file was created,
        # it would indicate a gap in mocking.

    # --- Provider Availability Endpoint Tests ---

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.add_provider_availability')
    def test_add_availability_success(self, mock_add_avail, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn # Mock the context manager's __enter__
        mock_add_avail.return_value = 101 # New availability_id

        payload = {"start_datetime": "2024-01-01 09:00:00", "end_datetime": "2024-01-01 12:00:00"}
        response = self.client.post('/api/providers/1/availability', json=payload)

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertEqual(data['availability_id'], 101)
        mock_add_avail.assert_called_once_with(mock_conn.__enter__(), 1, "2024-01-01 09:00:00", "2024-01-01 12:00:00", None)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.add_provider_availability')
    def test_add_availability_provider_not_found(self, mock_add_avail, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_add_avail.side_effect = sqlite3.IntegrityError("FOREIGN KEY constraint failed")

        payload = {"start_datetime": "2024-01-01 09:00:00", "end_datetime": "2024-01-01 12:00:00"}
        response = self.client.post('/api/providers/999/availability', json=payload)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("Provider with ID 999 not found", data['message'])

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.add_provider_availability')
    def test_add_availability_invalid_time_range(self, mock_add_avail, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_add_avail.side_effect = sqlite3.IntegrityError("CHECK constraint failed: chk_start_end_availability")

        payload = {"start_datetime": "2024-01-01 12:00:00", "end_datetime": "2024-01-01 09:00:00"}
        response = self.client.post('/api/providers/1/availability', json=payload)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("End datetime must be after start datetime", data['message'])

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.get_provider_availability')
    def test_get_availability_success(self, mock_get_avail, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_avail.return_value = [{"availability_id": 1, "start_datetime": "2024-01-01 09:00:00"}]

        response = self.client.get('/api/providers/1/availability?start_filter=2024-01-01 00:00:00&end_filter=2024-01-02 00:00:00')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(len(data['availability']), 1)
        mock_get_avail.assert_called_once_with(mock_conn.__enter__(), 1, "2024-01-01 00:00:00", "2024-01-02 00:00:00")

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.delete_provider_availability')
    def test_delete_availability_success(self, mock_delete_avail, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_delete_avail.return_value = True # Simulate successful deletion

        response = self.client.delete('/api/providers/availability/10', json={"provider_id": 1})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['message'], "Availability slot deleted successfully.")
        mock_delete_avail.assert_called_once_with(mock_conn.__enter__(), 10, 1)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.delete_provider_availability')
    def test_delete_availability_not_found_or_unauthorized(self, mock_delete_avail, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_delete_avail.return_value = False # Simulate not found or not authorized

        response = self.client.delete('/api/providers/availability/10', json={"provider_id": 1})
        self.assertEqual(response.status_code, 404) # API returns 404 in this case
        data = json.loads(response.data.decode())
        self.assertIn("Availability slot not found or you are not authorized", data['message'])

    # --- Appointment Request & Retrieval Tests ---
    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.request_appointment') # aliased as db_request_appointment in API
    def test_request_appointment_success(self, mock_request_appt, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_request_appt.return_value = 201 # New appointment_id
        payload = {
            "patient_id": 1, "provider_id": 2,
            "appointment_start_time": "2024-01-02 10:00:00",
            "appointment_end_time": "2024-01-02 10:30:00",
            "reason_for_visit": "Checkup"
        }
        response = self.client.post('/api/appointments/request', json=payload)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertEqual(data['appointment_id'], 201)
        mock_request_appt.assert_called_once() # Args check can be more specific

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.request_appointment')
    def test_request_appointment_user_not_found(self, mock_request_appt, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_request_appt.side_effect = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
        payload = {
            "patient_id": 999, "provider_id": 2, # 999 is non-existent
            "appointment_start_time": "2024-01-02 10:00:00",
            "appointment_end_time": "2024-01-02 10:30:00"
        }
        response = self.client.post('/api/appointments/request', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("Invalid patient_id or provider_id", data['message'])

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.get_appointments_for_user')
    def test_get_provider_appointments_success(self, mock_get_appts, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_appts.return_value = [{"appointment_id": 1, "patient_username": "test patient"}]
        response = self.client.get('/api/providers/1/appointments?status=confirmed')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(len(data['appointments']), 1)
        mock_get_appts.assert_called_once_with(mock_conn.__enter__(), user_id=1, user_role='provider', status_filter='confirmed', start_date_filter=None, end_date_filter=None)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.get_appointments_for_user')
    def test_get_patient_appointments_success(self, mock_get_appts, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_appts.return_value = [{"appointment_id": 1, "provider_username": "test doc"}]
        response = self.client.get('/api/patients/1/appointments')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(len(data['appointments']), 1)
        mock_get_appts.assert_called_once_with(mock_conn.__enter__(), user_id=1, user_role='patient', status_filter=None, start_date_filter=None, end_date_filter=None)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.get_appointment_by_id')
    def test_get_appointment_details_success(self, mock_get_appt_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        # User making the request is patient_id 10
        mock_get_appt_by_id.return_value = {"appointment_id": 5, "patient_id": 10, "provider_id": 20, "patient_username": "p_test", "provider_username": "d_test"}
        response = self.client.get('/api/appointments/5?user_id=10') # user_id 10 is the patient
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['appointment']['appointment_id'], 5)
        mock_get_appt_by_id.assert_called_once_with(mock_conn.__enter__(), 5)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.get_appointment_by_id')
    def test_get_appointment_details_not_found(self, mock_get_appt_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_appt_by_id.return_value = None
        response = self.client.get('/api/appointments/999?user_id=10')
        self.assertEqual(response.status_code, 404)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.get_appointment_by_id')
    def test_get_appointment_details_unauthorized(self, mock_get_appt_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        # User making request is 30, not part of appt
        mock_get_appt_by_id.return_value = {"appointment_id": 5, "patient_id": 10, "provider_id": 20}
        response = self.client.get('/api/appointments/5?user_id=30')
        self.assertEqual(response.status_code, 403)

    # --- Appointment Status Update Tests ---
    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.update_appointment_status')
    @patch('appointment_api.db_utils_appointment.get_appointment_by_id')
    def test_confirm_appointment_success(self, mock_get_appt, mock_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_update_status.return_value = True
        confirmed_appointment_data = {"appointment_id": 7, "status": "confirmed", "video_room_name": "Room123"}
        mock_get_appt.return_value = confirmed_appointment_data

        response = self.client.put('/api/appointments/7/confirm', json={"provider_id": 1})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['appointment'], confirmed_appointment_data)
        mock_update_status.assert_called_once_with(mock_conn.__enter__(), appointment_id=7, new_status='confirmed', current_user_id=1, user_role='provider')
        mock_get_appt.assert_called_once_with(mock_conn.__enter__(), 7)

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.update_appointment_status')
    def test_confirm_appointment_fail_or_unauthorized(self, mock_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_update_status.return_value = False # Simulate auth fail or appt not found by update util

        response = self.client.put('/api/appointments/8/confirm', json={"provider_id": 1})
        self.assertEqual(response.status_code, 403) # API returns 403/404 combined message

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.update_appointment_status')
    def test_cancel_appointment_success(self, mock_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_update_status.return_value = True

        payload = {"user_id": 10, "cancelled_by_role": "patient", "reason": "No longer needed"}
        response = self.client.put('/api/appointments/9/cancel', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['new_appointment_status'], 'cancelled_by_patient')
        mock_update_status.assert_called_once_with(mock_conn.__enter__(), appointment_id=9, new_status='cancelled_by_patient', current_user_id=10, user_role='patient', notes="No longer needed")

    @patch('appointment_api.get_db_connection')
    @patch('appointment_api.db_utils_appointment.update_appointment_status')
    def test_cancel_appointment_fail_or_unauthorized(self, mock_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_update_status.return_value = False

        payload = {"user_id": 10, "cancelled_by_role": "provider", "reason": "Mistake"}
        response = self.client.put('/api/appointments/10/cancel', json=payload)
        self.assertEqual(response.status_code, 403) # API returns 403/404 combined message


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
