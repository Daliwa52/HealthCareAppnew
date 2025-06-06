import unittest
import json
import os
import sqlite3
from datetime import datetime, date, timedelta # Added timedelta
import time # For minor delays if needed

# Import the Flask app and db utils
from prescription_api import app # To get the test client
import prescription_api # To modify prescription_api.DB_NAME
from db_utils_prescription import get_db_connection, initialize_prescription_schema, get_prescription_by_id as db_get_prescription_by_id

TEST_DB_NAME = 'test_prescription_integration.db'

class TestIntegrationPrescription(unittest.TestCase):
    original_db_name = None
    provider1_id = None
    provider2_id = None # For unauthorized tests
    patient1_id = None
    patient2_id = None # For unauthorized tests
    appointment1_id = None

    @classmethod
    def setUpClass(cls):
        cls.original_db_name = prescription_api.DB_NAME
        prescription_api.DB_NAME = TEST_DB_NAME

        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)

        conn = None
        try:
            conn = get_db_connection(TEST_DB_NAME)
            initialize_prescription_schema(conn) # This also creates users and appointments tables
            cursor = conn.cursor()

            # Create test users
            users_data = [
                ('integ_prov1', 'p1_rx@example.com', '111000111'),
                ('integ_prov2', 'p2_rx@example.com', '222000222'), # Another provider
                ('integ_pat1', 'pa1_rx@example.com', '333000333'),
                ('integ_pat2', 'pa2_rx@example.com', '444000444'), # Another patient
            ]
            user_ids = {}
            for uname, uemail, uphone in users_data:
                cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?, ?, ?)", (uname, uemail, uphone))
                if cursor.lastrowid == 0: # User already existed
                    cursor.execute("SELECT user_id FROM users WHERE username = ?", (uname,))
                    user_ids[uname] = cursor.fetchone()['user_id']
                else:
                    user_ids[uname] = cursor.lastrowid

            cls.provider1_id = user_ids['integ_prov1']
            cls.provider2_id = user_ids['integ_prov2']
            cls.patient1_id = user_ids['integ_pat1']
            cls.patient2_id = user_ids['integ_pat2']

            # Create a test appointment for FK
            cursor.execute("INSERT INTO appointments (patient_id, provider_id, appointment_start_time) VALUES (?, ?, ?)",
                           (cls.patient1_id, cls.provider1_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            cls.appointment1_id = cursor.lastrowid
            conn.commit()
            print(f"setUpClass: Test users and appointment created. P1={cls.provider1_id}, P2={cls.provider2_id}, PA1={cls.patient1_id}, PA2={cls.patient2_id}, Appt1={cls.appointment1_id}")

        except Exception as e:
            print(f"Error in setUpClass for prescriptions: {e}")
            if conn: conn.rollback()
            raise
        finally:
            if conn: conn.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        if cls.original_db_name:
            prescription_api.DB_NAME = cls.original_db_name
        print(f"tearDownClass: Cleaned up {TEST_DB_NAME} and restored DB_NAME.")

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db_conn = get_db_connection(TEST_DB_NAME)

        # Clean tables before each test for better isolation
        cursor = self.db_conn.cursor()
        cursor.execute("DELETE FROM prescription_medications;")
        cursor.execute("DELETE FROM prescriptions;")
        self.db_conn.commit()

    def tearDown(self):
        self.db_conn.close()

    def _post_json(self, endpoint, payload):
        return self.client.post(endpoint, json=payload)

    def _put_json(self, endpoint, payload):
        return self.client.put(endpoint, json=payload)

    def test_create_and_get_prescription_flow(self):
        print("\nRunning: test_create_and_get_prescription_flow")
        medications_payload = [
            {"medication_name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "quantity": "30 tablets"},
            {"medication_name": "Simvastatin", "dosage": "20mg", "frequency": "Once daily at bedtime", "quantity": "30 tablets", "is_prn": False}
        ]
        create_payload = {
            "patient_id": self.patient1_id,
            "provider_id": self.provider1_id, # Simulating auth context
            "issue_date": date.today().isoformat(),
            "medications": medications_payload,
            "appointment_id": self.appointment1_id,
            "notes_for_patient": "Take as directed."
        }

        # Provider1 creates a prescription for Patient1
        response_create = self._post_json('/api/prescriptions', create_payload)
        self.assertEqual(response_create.status_code, 201, f"Failed to create prescription: {response_create.data.decode()}")
        create_data = json.loads(response_create.data.decode())
        self.assertIn("prescription_id", create_data)
        prescription_id = create_data['prescription_id']

        # Direct DB Check (optional but good)
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM prescriptions WHERE prescription_id = ?", (prescription_id,))
        self.assertEqual(cursor.fetchone()[0], 1, "Prescription not found in DB after creation.")
        cursor.execute("SELECT COUNT(*) FROM prescription_medications WHERE prescription_id = ?", (prescription_id,))
        self.assertEqual(cursor.fetchone()[0], 2, "Incorrect number of medications in DB.")

        # Patient1 gets this prescription by ID
        response_get_pat = self.client.get(f'/api/prescriptions/{prescription_id}?user_id={self.patient1_id}')
        self.assertEqual(response_get_pat.status_code, 200)
        get_data_pat = json.loads(response_get_pat.data.decode())
        self.assertEqual(get_data_pat['prescription']['prescription_id'], prescription_id)
        self.assertEqual(len(get_data_pat['prescription']['medications']), 2)
        self.assertEqual(get_data_pat['prescription']['medications'][0]['medication_name'], "Lisinopril")

        # Provider1 gets this prescription by ID
        response_get_prov = self.client.get(f'/api/prescriptions/{prescription_id}?user_id={self.provider1_id}')
        self.assertEqual(response_get_prov.status_code, 200)
        get_data_prov = json.loads(response_get_prov.data.decode())
        self.assertEqual(get_data_prov['prescription']['prescription_id'], prescription_id)

        # Patient1 lists their prescriptions
        response_list_pat = self.client.get(f'/api/patients/{self.patient1_id}/prescriptions?user_id={self.patient1_id}')
        self.assertEqual(response_list_pat.status_code, 200)
        list_data_pat = json.loads(response_list_pat.data.decode())
        self.assertEqual(len(list_data_pat['prescriptions']), 1)
        self.assertEqual(list_data_pat['prescriptions'][0]['prescription_id'], prescription_id)

        # Provider1 lists their prescriptions
        response_list_prov = self.client.get(f'/api/providers/{self.provider1_id}/prescriptions?user_id={self.provider1_id}')
        self.assertEqual(response_list_prov.status_code, 200)
        list_data_prov = json.loads(response_list_prov.data.decode())
        self.assertEqual(len(list_data_prov['prescriptions']), 1)
        self.assertEqual(list_data_prov['prescriptions'][0]['prescription_id'], prescription_id)

    def test_cancel_prescription_flow(self):
        print("\nRunning: test_cancel_prescription_flow")
        # Provider1 creates a prescription for Patient1
        meds = [{"medication_name": "Amoxicillin", "dosage": "250mg", "frequency": "TID", "quantity": "21"}]
        rx_id = prescription_api.db_utils_prescription.db_create_prescription(
            self.db_conn, self.patient1_id, self.provider1_id, date.today().isoformat(), meds, self.appointment1_id
        )
        self.assertIsNotNone(rx_id)

        # Provider1 cancels it
        cancel_payload = {"provider_id": self.provider1_id, "reason": "Patient condition changed"}
        response_cancel = self._put_json(f'/api/prescriptions/{rx_id}/cancel', cancel_payload)
        self.assertEqual(response_cancel.status_code, 200, f"Cancel failed: {response_cancel.data.decode()}")
        cancel_data = json.loads(response_cancel.data.decode())
        self.assertEqual(cancel_data['new_status'], 'cancelled')

        # Get prescription by ID & Direct DB Check
        details_after_cancel = db_get_prescription_by_id(self.db_conn, rx_id)
        self.assertIsNotNone(details_after_cancel)
        self.assertEqual(details_after_cancel['status'], 'cancelled')
        self.assertIn("Patient condition changed", details_after_cancel['notes_for_pharmacist'])

    def test_create_prescription_invalid_data(self):
        print("\nRunning: test_create_prescription_invalid_data")
        # Attempt with non-existent patient_id
        invalid_payload_user = {
            "patient_id": 9999, "provider_id": self.provider1_id, "issue_date": date.today().isoformat(),
            "medications": [{"medication_name": "TestMed", "dosage": "10mg", "frequency": "QD", "quantity": "30"}]
        }
        response_invalid_user = self._post_json('/api/prescriptions', invalid_payload_user)
        self.assertEqual(response_invalid_user.status_code, 400) # FK constraint failure
        self.assertIn("Invalid patient_id, provider_id, or appointment_id", json.loads(response_invalid_user.data.decode())['message'])

        # Attempt with invalid medication data (missing medication_name)
        invalid_payload_med = {
            "patient_id": self.patient1_id, "provider_id": self.provider1_id, "issue_date": date.today().isoformat(),
            "medications": [{"dosage": "10mg", "frequency": "QD", "quantity": "30"}] # Missing medication_name
        }
        response_invalid_med = self._post_json('/api/prescriptions', invalid_payload_med)
        self.assertEqual(response_invalid_med.status_code, 400) # ValueError from db_util
        self.assertIn("missing required field", json.loads(response_invalid_med.data.decode())['message'])


    def test_get_prescription_unauthorized(self):
        print("\nRunning: test_get_prescription_unauthorized")
        # Provider1 creates prescription for Patient1
        meds = [{"medication_name": "TestDrug", "dosage": "10mg", "frequency": "QD", "quantity": "1"}]
        rx_id = prescription_api.db_utils_prescription.db_create_prescription(
            self.db_conn, self.patient1_id, self.provider1_id, date.today().isoformat(), meds
        )
        self.assertIsNotNone(rx_id)

        # Patient2 (not involved) tries to GET this prescription by ID
        response_unauth = self.client.get(f'/api/prescriptions/{rx_id}?user_id={self.patient2_id}')
        self.assertEqual(response_unauth.status_code, 403)

    def test_cancel_prescription_unauthorized(self):
        print("\nRunning: test_cancel_prescription_unauthorized")
        # Provider1 creates prescription for Patient1
        meds = [{"medication_name": "AnotherDrug", "dosage": "5mg", "frequency": "BID", "quantity": "10"}]
        rx_id = prescription_api.db_utils_prescription.db_create_prescription(
            self.db_conn, self.patient1_id, self.provider1_id, date.today().isoformat(), meds
        )
        self.assertIsNotNone(rx_id)

        # Provider2 tries to cancel it
        cancel_payload_p2 = {"provider_id": self.provider2_id, "reason": "Trying to cancel other's rx"}
        response_unauth_cancel_p2 = self._put_json(f'/api/prescriptions/{rx_id}/cancel', cancel_payload_p2)
        self.assertEqual(response_unauth_cancel_p2.status_code, 403) # API maps False from util to 403/404 message

        # Patient1 tries to cancel it (current cancel endpoint is provider-only based on payload)
        # The API expects provider_id in payload for cancel, so this would be a bad request or fail auth in db_util.
        # db_update_prescription_status would prevent this because provider_id from payload won't match.
        cancel_payload_pat1 = {"provider_id": self.patient1_id, "reason": "Patient trying to cancel as provider"}
        response_unauth_cancel_pat1 = self._put_json(f'/api/prescriptions/{rx_id}/cancel', cancel_payload_pat1)
        self.assertEqual(response_unauth_cancel_pat1.status_code, 403)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
