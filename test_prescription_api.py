import unittest
import json
import os
import sqlite3
from unittest.mock import patch, MagicMock, ANY
from datetime import date

# Import the Flask app from prescription_api
from prescription_api import app
import prescription_api # To modify prescription_api.DB_NAME

TEST_API_DB_NAME = 'test_prescription_api_level.db'

class TestPrescriptionAPI(unittest.TestCase):
    original_db_name = None

    def setUp(self):
        """Set up test client and application context for each test."""
        self.app_context = app.app_context()
        self.app_context.push()

        app.config['TESTING'] = True
        self.original_db_name = prescription_api.DB_NAME # Save original
        prescription_api.DB_NAME = TEST_API_DB_NAME      # Point app to test DB

        self.client = app.test_client()

    def tearDown(self):
        """Clean up after each test."""
        prescription_api.DB_NAME = self.original_db_name # Restore original
        self.app_context.pop()
        # No actual DB file should be created/deleted by these unit tests due to mocking.

    # --- Test POST /api/prescriptions (create_prescription_api) ---

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_create_prescription')
    def test_create_prescription_success(self, mock_db_create_prescription, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_create_prescription.return_value = 101 # New prescription_id

        payload = {
            "patient_id": 1, "provider_id": 2, "issue_date": "2024-03-15",
            "medications": [{"medication_name": "TestMed", "dosage": "10mg", "frequency": "QD", "quantity": "30"}]
        }
        response = self.client.post('/api/prescriptions', json=payload)
        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['prescription_id'], 101)
        mock_db_create_prescription.assert_called_once_with(
            mock_conn, payload['patient_id'], payload['provider_id'], payload['issue_date'],
            payload['medications'], None, None, None, None, 'active' # Default values for optionals
        )
        mock_conn.close.assert_called_once()


    def test_create_prescription_missing_fields(self):
        payload = {"provider_id": 2, "medications": [{"medication_name": "TestMed", "dosage": "10mg", "frequency": "QD", "quantity": "30"}]} # Missing patient_id
        response = self.client.post('/api/prescriptions', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("patient_id and provider_id are required", data['message'])

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_create_prescription')
    def test_create_prescription_db_integrity_error(self, mock_db_create_prescription, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_create_prescription.side_effect = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
        payload = {
            "patient_id": 999, "provider_id": 998, "issue_date": "2024-03-15", # Non-existent user IDs
            "medications": [{"medication_name": "TestMed", "dosage": "10mg", "frequency": "QD", "quantity": "30"}]
        }
        response = self.client.post('/api/prescriptions', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("Invalid patient_id, provider_id, or appointment_id", data['message'])

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_create_prescription')
    def test_create_prescription_db_value_error(self, mock_db_create_prescription, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_create_prescription.side_effect = ValueError("Missing required medication field: dosage")
        payload = {
            "patient_id": 1, "provider_id": 2, "issue_date": "2024-03-15",
            "medications": [{"medication_name": "TestMed", "frequency": "QD", "quantity": "30"}] # Missing dosage
        }
        response = self.client.post('/api/prescriptions', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("Missing required medication field: dosage", data['message'])

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_create_prescription')
    def test_create_prescription_db_generic_error(self, mock_db_create_prescription, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_create_prescription.side_effect = sqlite3.Error("Generic DB error")
        payload = {
            "patient_id": 1, "provider_id": 2, "issue_date": "2024-03-15",
            "medications": [{"medication_name": "TestMed", "dosage": "10mg", "frequency": "QD", "quantity": "30"}]
        }
        response = self.client.post('/api/prescriptions', json=payload)
        self.assertEqual(response.status_code, 500)

    # --- Test GET /api/prescriptions/<int:prescription_id> (get_prescription_details_api) ---
    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescription_by_id')
    def test_get_details_success_as_patient(self, mock_db_get_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_prescription_data = {'prescription_id': 1, 'patient_id': 10, 'provider_id': 20, "medications": []}
        mock_db_get_by_id.return_value = mock_prescription_data

        response = self.client.get('/api/prescriptions/1?user_id=10') # user_id 10 is patient
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['prescription'], mock_prescription_data)
        mock_db_get_by_id.assert_called_once_with(mock_conn, 1)

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescription_by_id')
    def test_get_details_success_as_provider(self, mock_db_get_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_prescription_data = {'prescription_id': 1, 'patient_id': 10, 'provider_id': 20, "medications": []}
        mock_db_get_by_id.return_value = mock_prescription_data

        response = self.client.get('/api/prescriptions/1?user_id=20') # user_id 20 is provider
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['prescription'], mock_prescription_data)

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescription_by_id')
    def test_get_details_not_found(self, mock_db_get_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_get_by_id.return_value = None
        response = self.client.get('/api/prescriptions/999?user_id=10')
        self.assertEqual(response.status_code, 404)

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescription_by_id')
    def test_get_details_unauthorized(self, mock_db_get_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_prescription_data = {'prescription_id': 1, 'patient_id': 10, 'provider_id': 20}
        mock_db_get_by_id.return_value = mock_prescription_data
        response = self.client.get('/api/prescriptions/1?user_id=30') # User 30 is not part of this prescription
        self.assertEqual(response.status_code, 403)

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescription_by_id')
    def test_get_details_db_error(self, mock_db_get_by_id, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_get_by_id.side_effect = sqlite3.Error("DB error")
        response = self.client.get('/api/prescriptions/1?user_id=10')
        self.assertEqual(response.status_code, 500)

    # --- Test GET /api/patients/<int:patient_id>/prescriptions ---
    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescriptions_for_user')
    def test_get_patient_prescriptions_success(self, mock_db_get_for_user, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_get_for_user.return_value = [{'prescription_id': 1, 'status': 'active'}]

        response = self.client.get('/api/patients/10/prescriptions?user_id=10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(len(data['prescriptions']), 1)
        mock_db_get_for_user.assert_called_once_with(mock_conn, user_id=10, user_role='patient', start_date_filter=None, end_date_filter=None, status_filter=None)

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescriptions_for_user')
    def test_get_patient_prescriptions_unauthorized(self, mock_db_get_for_user, mock_get_conn):
        # No need to mock db_get_for_user as auth check is before
        response = self.client.get('/api/patients/10/prescriptions?user_id=11') # Requesting user 11 for patient 10's data
        self.assertEqual(response.status_code, 403)
        mock_db_get_for_user.assert_not_called() # DB util should not be called if auth fails

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescriptions_for_user')
    def test_get_patient_prescriptions_db_error(self, mock_db_get_for_user, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_get_for_user.side_effect = sqlite3.Error("DB error")
        response = self.client.get('/api/patients/10/prescriptions?user_id=10')
        self.assertEqual(response.status_code, 500)

    # --- Test GET /api/providers/<int:provider_id>/prescriptions ---
    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescriptions_for_user')
    def test_get_provider_prescriptions_success(self, mock_db_get_for_user, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_get_for_user.return_value = [{'prescription_id': 1, 'status': 'active'}]

        response = self.client.get('/api/providers/20/prescriptions?user_id=20')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(len(data['prescriptions']), 1)
        mock_db_get_for_user.assert_called_once_with(mock_conn, user_id=20, user_role='provider', start_date_filter=None, end_date_filter=None, status_filter=None)

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_get_prescriptions_for_user')
    def test_get_provider_prescriptions_unauthorized(self, mock_db_get_for_user, mock_get_conn):
        response = self.client.get('/api/providers/20/prescriptions?user_id=21')
        self.assertEqual(response.status_code, 403)
        mock_db_get_for_user.assert_not_called()

    # --- Test PUT /api/prescriptions/<int:prescription_id>/cancel ---
    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_update_prescription_status')
    def test_cancel_prescription_success(self, mock_db_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_update_status.return_value = True

        payload = {"provider_id": 20, "reason": "Patient no longer needs it."} # provider_id for auth sim
        response = self.client.put('/api/prescriptions/1/cancel', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['new_status'], 'cancelled')
        mock_db_update_status.assert_called_once_with(mock_conn, prescription_id=1, new_status='cancelled', current_provider_id=20, notes="Patient no longer needs it.")

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_update_prescription_status')
    def test_cancel_prescription_not_found_or_unauthorized(self, mock_db_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_update_status.return_value = False # Simulate DB util returning False for auth/not found

        payload = {"provider_id": 20, "reason": "Test"}
        response = self.client.put('/api/prescriptions/999/cancel', json=payload)
        self.assertEqual(response.status_code, 403) # API maps False from util to 403/404 message

    @patch('prescription_api.get_db_connection')
    @patch('prescription_api.db_utils_prescription.db_update_prescription_status')
    def test_cancel_prescription_db_error(self, mock_db_update_status, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_db_update_status.side_effect = sqlite3.Error("DB error on cancel")

        payload = {"provider_id": 20}
        response = self.client.put('/api/prescriptions/1/cancel', json=payload)
        self.assertEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
