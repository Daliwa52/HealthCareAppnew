import unittest
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone # Added timezone for UTC consistency if needed
import time # For minor delays

# Import the Flask app and db utils
from appointment_api import app # To get the test client
import appointment_api # To modify appointment_api.DB_NAME
from db_utils_appointment import (
    get_db_connection,
    initialize_appointment_schema,
    get_appointments_needing_reminders, # For reminder logic test
    mark_reminder_sent,               # For reminder logic test
    get_appointment_by_id,            # For reminder logic test & general verification
    # We'll use API calls for most actions, but direct DB utils for setup/verification sometimes
    add_provider_availability as db_add_provider_availability,
    request_appointment as db_request_appointment,
    update_appointment_status as db_update_appointment_status
)

TEST_DB_NAME = 'test_appointment_integration.db'

class TestIntegrationAppointment(unittest.TestCase):
    original_db_name = None
    provider1_id = None
    provider2_id = None
    patient1_id = None
    patient2_id = None

    @classmethod
    def setUpClass(cls):
        cls.original_db_name = appointment_api.DB_NAME
        appointment_api.DB_NAME = TEST_DB_NAME

        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)

        conn = None
        try:
            conn = get_db_connection(TEST_DB_NAME)
            initialize_appointment_schema(conn)
            cursor = conn.cursor()
            users_to_create = [
                ('integ_provider1', 'p1@example.com', '111000111'),
                ('integ_provider2', 'p2@example.com', '222000222'),
                ('integ_patient1', 'pa1@example.com', '333000333'),
                ('integ_patient2', 'pa2@example.com', '444000444'),
            ]
            user_ids = {}
            for uname, uemail, uphone in users_to_create:
                try:
                    cursor.execute("INSERT INTO users (username, email, phone) VALUES (?, ?, ?)", (uname, uemail, uphone))
                    user_ids[uname] = cursor.lastrowid
                except sqlite3.IntegrityError: # If re-running without full cleanup
                    cursor.execute("SELECT user_id FROM users WHERE username = ?", (uname,))
                    user_ids[uname] = cursor.fetchone()['user_id']

            cls.provider1_id = user_ids['integ_provider1']
            cls.provider2_id = user_ids['integ_provider2']
            cls.patient1_id = user_ids['integ_patient1']
            cls.patient2_id = user_ids['integ_patient2']
            conn.commit()
            print(f"setUpClass: Test users created. P1={cls.provider1_id}, P2={cls.provider2_id}, PA1={cls.patient1_id}, PA2={cls.patient2_id}")
        except Exception as e:
            print(f"Error in setUpClass: {e}")
            if conn: conn.rollback()
            raise
        finally:
            if conn: conn.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
        if cls.original_db_name:
            appointment_api.DB_NAME = cls.original_db_name
        print(f"tearDownClass: Cleaned up {TEST_DB_NAME} and restored DB_NAME.")

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db_conn = get_db_connection(TEST_DB_NAME) # For direct DB checks/setup within tests

    def tearDown(self):
        # Clean relevant tables after each test to ensure independence
        cursor = self.db_conn.cursor()
        cursor.execute("DELETE FROM appointments;")
        cursor.execute("DELETE FROM provider_availability;")
        self.db_conn.commit()
        self.db_conn.close()

    # Helper to reduce boilerplate for POST
    def _post_json(self, endpoint, payload):
        return self.client.post(endpoint, json=payload)

    # Helper to reduce boilerplate for PUT
    def _put_json(self, endpoint, payload):
        return self.client.put(endpoint, json=payload)

    # Helper to reduce boilerplate for DELETE
    def _delete_json(self, endpoint, payload):
        return self.client.delete(endpoint, json=payload)


    def test_full_appointment_booking_and_confirmation_flow(self):
        print("\nRunning: test_full_appointment_booking_and_confirmation_flow")
        # 1. Provider1 adds availability
        avail_payload = {
            "start_datetime": "2024-08-01 09:00:00",
            "end_datetime": "2024-08-01 12:00:00"
        }
        response_add_avail = self._post_json(f'/api/providers/{self.provider1_id}/availability', avail_payload)
        self.assertEqual(response_add_avail.status_code, 201)
        avail_data = json.loads(response_add_avail.data.decode())
        self.assertIn("availability_id", avail_data)

        # 2. Patient1 requests an appointment
        appt_payload = {
            "patient_id": self.patient1_id,
            "provider_id": self.provider1_id,
            "appointment_start_time": "2024-08-01 10:00:00",
            "appointment_end_time": "2024-08-01 10:30:00",
            "reason_for_visit": "Checkup"
        }
        response_req_appt = self._post_json('/api/appointments/request', appt_payload)
        self.assertEqual(response_req_appt.status_code, 201)
        appt_data = json.loads(response_req_appt.data.decode())
        self.assertIn("appointment_id", appt_data)
        appointment_id = appt_data['appointment_id']

        # 3. Provider1 confirms the appointment
        confirm_payload = {"provider_id": self.provider1_id} # Simulating auth context
        response_confirm = self._put_json(f'/api/appointments/{appointment_id}/confirm', confirm_payload)
        self.assertEqual(response_confirm.status_code, 200)
        confirm_data = json.loads(response_confirm.data.decode())
        self.assertEqual(confirm_data['appointment']['status'], 'confirmed')
        self.assertIsNotNone(confirm_data['appointment']['video_room_name'])

        # 4. Patient1 gets their appointments
        response_pat_appts = self.client.get(f'/api/patients/{self.patient1_id}/appointments')
        self.assertEqual(response_pat_appts.status_code, 200)
        pat_appts_data = json.loads(response_pat_appts.data.decode())
        self.assertEqual(len(pat_appts_data['appointments']), 1)
        self.assertEqual(pat_appts_data['appointments'][0]['status'], 'confirmed')
        self.assertEqual(pat_appts_data['appointments'][0]['appointment_id'], appointment_id)

        # 5. Provider1 gets their appointments
        response_prov_appts = self.client.get(f'/api/providers/{self.provider1_id}/appointments')
        self.assertEqual(response_prov_appts.status_code, 200)
        prov_appts_data = json.loads(response_prov_appts.data.decode())
        self.assertEqual(len(prov_appts_data['appointments']), 1)
        self.assertEqual(prov_appts_data['appointments'][0]['status'], 'confirmed')

        # 6. Patient1 gets appointment details
        response_appt_details = self.client.get(f'/api/appointments/{appointment_id}?user_id={self.patient1_id}')
        self.assertEqual(response_appt_details.status_code, 200)
        appt_details_data = json.loads(response_appt_details.data.decode())
        self.assertEqual(appt_details_data['appointment']['appointment_id'], appointment_id)
        self.assertEqual(appt_details_data['appointment']['patient_username'], 'integ_patient1')

    def test_appointment_cancellation_flow(self):
        print("\nRunning: test_appointment_cancellation_flow")
        # Setup: Provider1 adds availability, Patient2 books, Provider1 confirms
        db_add_provider_availability(self.db_conn, self.provider1_id, "2024-08-02 09:00:00", "2024-08-02 12:00:00")
        appointment_id = db_request_appointment(self.db_conn, self.patient2_id, self.provider1_id,
                                               "2024-08-02 09:00:00", "2024-08-02 09:30:00", "Follow-up")
        db_update_appointment_status(self.db_conn, appointment_id, 'confirmed', self.provider1_id, 'provider')

        # Patient2 cancels the appointment
        cancel_payload_patient = {
            "user_id": self.patient2_id,
            "cancelled_by_role": "patient",
            "reason": "Feeling better now"
        }
        response_cancel_pat = self._put_json(f'/api/appointments/{appointment_id}/cancel', cancel_payload_patient)
        self.assertEqual(response_cancel_pat.status_code, 200)
        cancel_data_pat = json.loads(response_cancel_pat.data.decode())
        self.assertEqual(cancel_data_pat['new_appointment_status'], 'cancelled_by_patient')

        # Verify status in DB
        appt_details = get_appointment_by_id(self.db_conn, appointment_id)
        self.assertEqual(appt_details['status'], 'cancelled_by_patient')
        self.assertIn("Feeling better now", appt_details['notes_by_patient'])

        # Setup for provider cancellation
        appointment_id2 = db_request_appointment(self.db_conn, self.patient1_id, self.provider1_id,
                                                 "2024-08-02 10:00:00", "2024-08-02 10:30:00", "Consultation")
        db_update_appointment_status(self.db_conn, appointment_id2, 'confirmed', self.provider1_id, 'provider')

        # Provider1 cancels the appointment
        cancel_payload_provider = {
            "user_id": self.provider1_id,
            "cancelled_by_role": "provider",
            "reason": "Emergency"
        }
        response_cancel_prov = self._put_json(f'/api/appointments/{appointment_id2}/cancel', cancel_payload_provider)
        self.assertEqual(response_cancel_prov.status_code, 200)
        cancel_data_prov = json.loads(response_cancel_prov.data.decode())
        self.assertEqual(cancel_data_prov['new_appointment_status'], 'cancelled_by_provider')

        appt_details2 = get_appointment_by_id(self.db_conn, appointment_id2)
        self.assertEqual(appt_details2['status'], 'cancelled_by_provider')
        self.assertIn("Emergency", appt_details2['notes_by_provider'])


    def test_delete_provider_availability(self):
        print("\nRunning: test_delete_provider_availability")
        # Provider1 adds an availability slot
        avail_id = db_add_provider_availability(self.db_conn, self.provider1_id, "2024-08-03 10:00:00", "2024-08-03 11:00:00")
        self.assertIsNotNone(avail_id)

        # Provider1 deletes that slot
        delete_payload = {"provider_id": self.provider1_id} # Simulating auth context
        response_delete = self._delete_json(f'/api/providers/availability/{avail_id}', delete_payload)
        self.assertEqual(response_delete.status_code, 200)

        # Verify slot is gone (attempting to get it should be empty for this provider)
        avail_slots = appointment_api.db_utils_appointment.get_provider_availability(self.db_conn, self.provider1_id)
        found = any(slot['availability_id'] == avail_id for slot in avail_slots)
        self.assertFalse(found, "Deleted availability slot was still found.")

    def test_unauthorized_operations(self):
        print("\nRunning: test_unauthorized_operations")
        # Setup: Provider1 adds availability, Patient1 books, Provider1 confirms
        db_add_provider_availability(self.db_conn, self.provider1_id, "2024-08-04 09:00:00", "2024-08-04 10:00:00")
        appointment_id = db_request_appointment(self.db_conn, self.patient1_id, self.provider1_id,
                                                "2024-08-04 09:00:00", "2024-08-04 09:30:00")
        db_update_appointment_status(self.db_conn, appointment_id, 'confirmed', self.provider1_id, 'provider')

        # Patient2 (not involved) tries to get details of this appointment_id
        response_unauth_get = self.client.get(f'/api/appointments/{appointment_id}?user_id={self.patient2_id}')
        self.assertEqual(response_unauth_get.status_code, 403)

        # Patient1 tries to confirm their own appointment (API expects provider_id in payload for confirm)
        confirm_payload_pat = {"provider_id": self.patient1_id} # Wrong ID type for action
        response_unauth_confirm = self._put_json(f'/api/appointments/{appointment_id}/confirm', confirm_payload_pat)
        self.assertEqual(response_unauth_confirm.status_code, 403) # update_appointment_status should prevent this

        # Provider2 tries to delete Provider1's availability slot
        avail_id_p1 = db_add_provider_availability(self.db_conn, self.provider1_id, "2024-08-04 11:00:00", "2024-08-04 12:00:00")
        delete_payload_p2 = {"provider_id": self.provider2_id}
        response_unauth_delete = self._delete_json(f'/api/providers/availability/{avail_id_p1}', delete_payload_p2)
        self.assertEqual(response_unauth_delete.status_code, 404) # API returns 404 if not found for that provider

    def test_get_appointments_needing_reminders_logic(self):
        print("\nRunning: test_get_appointments_needing_reminders_logic")
        now = datetime.now(timezone.utc) # Use timezone aware datetime

        # Helper to create datetime strings
        def dt_str(dt_obj):
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')

        # Scenario 1: Appointment needs reminder (in window, not reminded)
        start1 = now + timedelta(hours=23, minutes=30)
        appt1_id = db_request_appointment(self.db_conn, self.patient1_id, self.provider1_id, dt_str(start1), dt_str(start1 + timedelta(minutes=30)), "Reminder Test 1")
        db_update_appointment_status(self.db_conn, appt1_id, 'confirmed', self.provider1_id, 'provider')

        # Scenario 2: Appointment needs reminder (in window, reminded long ago)
        start2 = now + timedelta(hours=23, minutes=40)
        appt2_id = db_request_appointment(self.db_conn, self.patient2_id, self.provider1_id, dt_str(start2), dt_str(start2 + timedelta(minutes=30)), "Reminder Test 2")
        db_update_appointment_status(self.db_conn, appt2_id, 'confirmed', self.provider1_id, 'provider')
        mark_reminder_sent(self.db_conn, appt2_id, dt_str(now - timedelta(hours=5))) # Reminded 5 hours ago

        # Scenario 3: Appointment does NOT need reminder (in window, but reminded recently)
        start3 = now + timedelta(hours=23, minutes=50)
        appt3_id = db_request_appointment(self.db_conn, self.patient1_id, self.provider1_id, dt_str(start3), dt_str(start3 + timedelta(minutes=30)), "Reminder Test 3")
        db_update_appointment_status(self.db_conn, appt3_id, 'confirmed', self.provider1_id, 'provider')
        mark_reminder_sent(self.db_conn, appt3_id, dt_str(now - timedelta(minutes=30))) # Reminded 30 mins ago

        # Scenario 4: Appointment outside window (starts too soon)
        start4 = now + timedelta(hours=1)
        appt4_id = db_request_appointment(self.db_conn, self.patient2_id, self.provider1_id, dt_str(start4), dt_str(start4 + timedelta(minutes=30)), "Reminder Test 4")
        db_update_appointment_status(self.db_conn, appt4_id, 'confirmed', self.provider1_id, 'provider')

        # Scenario 5: Appointment not confirmed
        start5 = now + timedelta(hours=23, minutes=55)
        appt5_id = db_request_appointment(self.db_conn, self.patient1_id, self.provider1_id, dt_str(start5), dt_str(start5 + timedelta(minutes=30)), "Reminder Test 5")
        # Status is 'pending_provider_confirmation' by default

        # Define reminder window (e.g., appointments starting between 23 and 24 hours from now)
        # For db_utils function, window times are absolute strings
        query_window_start = dt_str(now + timedelta(hours=23))
        query_window_end = dt_str(now + timedelta(hours=24))
        grace_period_hours = 2

        reminders = get_appointments_needing_reminders(self.db_conn, query_window_start, query_window_end, grace_period_hours)

        reminded_appt_ids = [r['appointment_id'] for r in reminders]
        print(f"Appointments needing reminders: {reminded_appt_ids}")

        self.assertIn(appt1_id, reminded_appt_ids, "Appt1 (not reminded) should be in list.")
        self.assertIn(appt2_id, reminded_appt_ids, "Appt2 (reminded long ago) should be in list.")
        self.assertNotIn(appt3_id, reminded_appt_ids, "Appt3 (reminded recently) should NOT be in list.")
        self.assertNotIn(appt4_id, reminded_appt_ids, "Appt4 (outside window) should NOT be in list.")
        self.assertNotIn(appt5_id, reminded_appt_ids, "Appt5 (not confirmed) should NOT be in list.")

        # Test marking a reminder
        if appt1_id in reminded_appt_ids:
            mark_reminder_sent(self.db_conn, appt1_id)
            appt1_details_after_mark = get_appointment_by_id(self.db_conn, appt1_id)
            self.assertIsNotNone(appt1_details_after_mark['last_reminder_sent_at'])
            print(f"Appt1 last_reminder_sent_at after marking: {appt1_details_after_mark['last_reminder_sent_at']}")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
