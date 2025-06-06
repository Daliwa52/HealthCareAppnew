from datetime import datetime, timedelta
import os
import sqlite3 # For specific error handling if needed by the job
from db_utils_appointment import (
    get_db_connection,
    get_appointments_needing_reminders,
    mark_reminder_sent,
    initialize_appointment_schema,
    request_appointment, # For test data setup
    update_appointment_status  # For test data setup
)

# Configure DB_NAME using an environment variable with a default
DB_NAME = os.getenv('APPOINTMENT_DB_NAME', 'appointment_app.db')

# --- Notification Service Placeholders ---

def send_email_reminder(email_address: str, appointment_details: dict) -> bool:
    """
    Simulates sending an email reminder for an appointment.

    In a real application, this function would integrate with an email service
    (e.g., SMTP, SendGrid, AWS SES) to dispatch actual emails. It would format
    a user-friendly message containing key appointment information.

    Args:
        email_address (str): The recipient's email address.
        appointment_details (dict): A dictionary containing details of the appointment,
                                    expected to include keys like 'appointment_id',
                                    'appointment_start_time', 'patient_username',
                                    'provider_username', 'reason_for_visit'.

    Returns:
        bool: True if the email was "sent" successfully (simulated), False otherwise
              (e.g., if no email address was provided).
    """
    if not email_address:
        print(f"  - Skipping email: No email address provided for appointment ID {appointment_details.get('appointment_id')}.")
        return False

    # Simulate sending: Log the action
    print(f"  - SIMULATING: Sending EMAIL reminder to {email_address} for appointment ID {appointment_details.get('appointment_id')} "
          f"at {appointment_details.get('appointment_start_time')} with {appointment_details.get('provider_username')}.")

    # Example of how a real email might be constructed:
    # subject = f"Appointment Reminder: {appointment_details.get('reason_for_visit', 'Your upcoming appointment')}"
    # patient_name = appointment_details.get('patient_username', 'Patient')
    # provider_name = appointment_details.get('provider_username', 'your provider')
    # appt_start_time_str = appointment_details.get('appointment_start_time')
    # reason = appointment_details.get('reason_for_visit', 'your scheduled check-up')
    # try:
    #     appt_dt_obj = datetime.strptime(appt_start_time_str, '%Y-%m-%d %H:%M:%S')
    #     formatted_time = appt_dt_obj.strftime('%B %d, %Y at %I:%M %p') # Example: March 15, 2024 at 02:30 PM
    # except (ValueError, TypeError):
    #     formatted_time = appt_start_time_str # Fallback if parsing fails
    # body = (f"Dear {patient_name},\n\n"
    #         f"This is a reminder for your appointment for '{reason}' "
    #         f"scheduled for {formatted_time} with {provider_name}.\n\n"
    #         f"If you need to reschedule, please contact us as soon as possible.\n\n"
    #         f"Thank you,\nYour Clinic")
    # print(f"    Subject: {subject}")
    # print(f"    Body Preview: {body[:100]}...") # Preview
    # result = actual_email_sending_logic(email_address, subject, body)
    # return result
    return True # Simulate success

def send_sms_reminder(phone_number: str, appointment_details: dict) -> bool:
    """
    Simulates sending an SMS reminder for an appointment.

    In a real application, this function would integrate with an SMS gateway
    (e.g., Twilio, Vonage) to dispatch actual text messages. It would format
    a concise message with key appointment information.

    Args:
        phone_number (str): The recipient's phone number.
        appointment_details (dict): A dictionary containing details of the appointment.
                                    Expected keys are similar to `send_email_reminder`.

    Returns:
        bool: True if the SMS was "sent" successfully (simulated), False otherwise.
    """
    if not phone_number:
        print(f"  - Skipping SMS: No phone number provided for appointment ID {appointment_details.get('appointment_id')}.")
        return False

    # Simulate sending: Log the action
    print(f"  - SIMULATING: Sending SMS reminder to {phone_number} for appointment ID {appointment_details.get('appointment_id')} "
          f"at {appointment_details.get('appointment_start_time')}.")

    # Example of how a real SMS might be constructed:
    # provider_name = appointment_details.get('provider_username', 'your provider')
    # appt_start_time_str = appointment_details.get('appointment_start_time')
    # reason_summary = appointment_details.get('reason_for_visit', 'check-up')
    # if len(reason_summary) > 20: reason_summary = reason_summary[:17] + "..." # Keep it short
    # try:
    #     appt_dt_obj = datetime.strptime(appt_start_time_str, '%Y-%m-%d %H:%M:%S')
    #     formatted_time = appt_dt_obj.strftime('%b %d, %I:%M%p') # E.g., Mar 15, 02:30PM
    # except (ValueError, TypeError):
    #     formatted_time = appt_start_time_str # Fallback
    # message = (f"Reminder: Your appt for '{reason_summary}' with {provider_name} is on {formatted_time}.")
    # print(f"    SMS Message: {message}")
    # result = actual_sms_sending_logic(phone_number, message)
    # return result
    return True # Simulate success

# --- Core Logic ---

def send_reminders(time_window_start_hours_ahead: int = 23,
                   time_window_end_hours_ahead: int = 24,
                   reminder_grace_period_hours: int = 2
                  ):
    """
    Fetches upcoming confirmed appointments that require reminders and processes them.

    This function is designed to be run periodically (e.g., as a cron job).
    It identifies appointments within a specified future time window
    (e.g., those starting between 23 and 24 hours from now) for which
    reminders haven't been sent recently (respecting a grace period).

    For each such appointment, it attempts to send email and/or SMS reminders
    (using placeholder functions) and then updates the appointment record to
    mark that a reminder has been sent.

    Args:
        time_window_start_hours_ahead (int): Defines the start of the time window (in hours
                                             from the current time) for appointments to consider.
                                             Default is 23 hours.
        time_window_end_hours_ahead (int): Defines the end of the time window (in hours
                                           from the current time) for appointments to consider.
                                           The window is effectively [start, end). Default is 24 hours.
        reminder_grace_period_hours (int): If a reminder was already sent for an appointment
                                           within this many hours from the current time,
                                           another reminder will not be sent. This prevents
                                           sending multiple reminders if the job runs frequently.
                                           Default is 2 hours.
    """
    job_start_time = datetime.now()
    print(f"\n--- Starting Reminder Job ({job_start_time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
    print(f"Looking for appointments between {time_window_start_hours_ahead} and "
          f"{time_window_end_hours_ahead} hours from now.")
    print(f"Reminder grace period: {reminder_grace_period_hours} hours (reminders sent more recently than this will be skipped).")

    # Calculate the absolute start and end times for the database query window
    window_start_dt = job_start_time + timedelta(hours=time_window_start_hours_ahead)
    window_end_dt = job_start_time + timedelta(hours=time_window_end_hours_ahead)
    window_start_iso = window_start_dt.strftime('%Y-%m-%d %H:%M:%S')
    window_end_iso = window_end_dt.strftime('%Y-%m-%d %H:%M:%S')

    print(f"Calculated reminder query window: START_TIME >= '{window_start_iso}' AND START_TIME < '{window_end_iso}'")

    # Establish database connection using a context manager
    with get_db_connection(DB_NAME) as conn:
        try:
            # Fetch appointments that are confirmed and need reminders
            appointments_to_remind = get_appointments_needing_reminders(
                conn, window_start_iso, window_end_iso, reminder_grace_period_hours
            )

            if not appointments_to_remind:
                print("No appointments found needing reminders in the specified window.")
                return

            print(f"Found {len(appointments_to_remind)} appointments needing reminders.")
            successful_reminders_marked = 0
            failed_reminders_marked = 0
            notifications_attempted_count = 0

            for appt in appointments_to_remind:
                print(f"\nProcessing Appointment ID: {appt['appointment_id']} "
                      f"(Patient: {appt['patient_username']}, Provider: {appt['provider_username']}) "
                      f"scheduled at {appt['appointment_start_time']}")
                print(f"  Details: Last reminder sent at: {appt['last_reminder_sent_at'] or 'Never'}")

                at_least_one_notification_sent = False

                # Attempt to send email reminder (assuming reminder goes to patient)
                if appt.get("patient_email"):
                    if send_email_reminder(appt["patient_email"], appt): # appt dict contains all details
                        at_least_one_notification_sent = True
                else:
                    print(f"  - No patient email found for appointment {appt['appointment_id']}.")

                # Attempt to send SMS reminder (assuming reminder goes to patient)
                if appt.get("patient_phone"):
                    if send_sms_reminder(appt["patient_phone"], appt): # appt dict contains all details
                        at_least_one_notification_sent = True
                else:
                    print(f"  - No patient phone found for appointment {appt['appointment_id']}.")

                if at_least_one_notification_sent:
                    notifications_attempted_count +=1
                    # Mark reminder as sent only if at least one notification was "successfully" processed/attempted.
                    # In a real system with actual send status, this logic might be more nuanced.
                    try:
                        if mark_reminder_sent(conn, appt['appointment_id']): # Uses current time by default
                            print(f"  Successfully marked reminder as sent for appointment ID {appt['appointment_id']}.")
                            successful_reminders_marked +=1
                        else:
                            # This case implies appointment_id not found during update, which shouldn't happen if fetched.
                            print(f"  WARNING: Failed to mark reminder (rowcount 0) for appointment ID {appt['appointment_id']}.")
                            failed_reminders_marked += 1
                    except sqlite3.Error as e_mark: # Catch specific error from mark_reminder_sent
                        print(f"  ERROR: Database error while marking reminder for appointment ID {appt['appointment_id']}: {e_mark}")
                        failed_reminders_marked += 1
                else:
                    print(f"  No contact information (email/phone) suitable for sending for appointment ID {appt['appointment_id']}.")

            print(f"\n--- Reminder Processing Summary ---")
            print(f"  Appointments processed: {len(appointments_to_remind)}")
            print(f"  Notifications attempted for: {notifications_attempted_count} appointments")
            print(f"  Successfully marked as reminded: {successful_reminders_marked}")
            print(f"  Failed to mark as reminded (after attempt): {failed_reminders_marked}")


        except sqlite3.Error as e_db: # Errors from get_appointments_needing_reminders or connection issues
            print(f"A database error occurred during the reminder job: {e_db}")
        except ValueError as ve:
             print(f"Configuration or data error for reminder job: {ve}")
        except Exception as e_unexpected: # Catch any other unexpected errors
            print(f"An unexpected error occurred during the reminder job: {e_unexpected}")
        finally:
            job_end_time = datetime.now()
            print(f"--- Reminder Job Finished ({job_end_time.strftime('%Y-%m-%d %H:%M:%S')}, Duration: {job_end_time - job_start_time}) ---")

if __name__ == '__main__':
    """
    This script is intended to be run as a scheduled job (e.g., using cron or a task scheduler).

    Prerequisites for running:
    1. Database Accessibility: The database file specified by `DB_NAME` (or the default)
       must be accessible and writable by the user running this script.
    2. Schema Initialization: The database schema (tables like `users`, `appointments`)
       must be initialized. This can be done by running `db_utils_appointment.py` directly
       if it contains schema setup in its `if __name__ == '__main__':` block, or by using
       a separate migration/setup script.
    3. Populated Data: There should be user and appointment data in the database.
       Specifically, `users` should have `email` and `phone` fields populated for
       patients who should receive reminders. Appointments should be in 'confirmed' status.
    4. Notification Service Integration: The placeholder functions `send_email_reminder`
       and `send_sms_reminder` must be replaced with actual integrations with
       email and SMS sending services (e.g., SMTP libraries, Twilio API, AWS SES/SNS).

    Example for setting up test data (run this once, or manage via an env var):
    If you set the environment variable SETUP_TEST_DATA_FOR_REMINDER_JOB=true,
    the example block below will attempt to initialize the schema and add sample data.
    """
    print(f"Running Appointment Reminder Job for DB: {DB_NAME}")

    if os.getenv('SETUP_TEST_DATA_FOR_REMINDER_JOB', 'false').lower() == 'true':
        print("Attempting to set up test data for reminder job demo...")
        try:
            with get_db_connection(DB_NAME) as conn_setup:
                initialize_appointment_schema(conn_setup) # Ensure schema exists
                cursor = conn_setup.cursor()

                users_for_job_data = [
                    ('rem_patient1', 'patient1.rem@example.com', '5550001111'),
                    ('rem_provider1', 'provider.rem@example.com', '5550002222'),
                    ('rem_patient2_noemail', None, '5550003333'),
                    ('rem_patient3_nophone', 'patient3.rem@example.com', None),
                ]
                user_ids_map = {}
                print("  Ensuring test users exist...")
                for uname, uemail, uphone in users_for_job_data:
                    cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?,?,?)", (uname, uemail, uphone))
                    if cursor.lastrowid == 0: # User likely existed
                        cursor.execute("SELECT user_id FROM users WHERE username = ?", (uname,))
                        user_ids_map[uname] = cursor.fetchone()['user_id']
                    else:
                        user_ids_map[uname] = cursor.lastrowid
                conn_setup.commit()

                p1_id = user_ids_map['rem_patient1']
                pv1_id = user_ids_map['rem_provider1']
                p2_id = user_ids_map['rem_patient2_noemail']
                p3_id = user_ids_map['rem_patient3_nophone']
                print(f"  Test user IDs: Patient1={p1_id}, Provider1={pv1_id}, Patient2(no_email)={p2_id}, Patient3(no_phone)={p3_id}")

                print("  Setting up test appointments...")
                # Appt 1: Needs reminder (in 23.5 hours, never reminded)
                appt1_start = (datetime.now() + timedelta(hours=23.5)).strftime('%Y-%m-%d %H:%M:%S')
                appt1_end = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                appt1_id = request_appointment(conn_setup, p1_id, pv1_id, appt1_start, appt1_end, "Annual Physical")
                if appt1_id: update_appointment_status(conn_setup, appt1_id, 'confirmed', pv1_id, 'provider')

                # Appt 2: Needs reminder (in 23.7 hours, reminder sent long ago)
                appt2_start = (datetime.now() + timedelta(hours=23.7)).strftime('%Y-%m-%d %H:%M:%S')
                appt2_end = (datetime.now() + timedelta(hours=24.2)).strftime('%Y-%m-%d %H:%M:%S')
                appt2_id = request_appointment(conn_setup, p2_id, pv1_id, appt2_start, appt2_end, "Lab Follow-up")
                if appt2_id:
                    update_appointment_status(conn_setup, appt2_id, 'confirmed', pv1_id, 'provider')
                    mark_reminder_sent(conn_setup, appt2_id, (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'))

                # Appt 3: Too recent reminder (in 23.6 hours, reminded 30 mins ago)
                appt3_start = (datetime.now() + timedelta(hours=23.6)).strftime('%Y-%m-%d %H:%M:%S')
                appt3_end = (datetime.now() + timedelta(hours=24.1)).strftime('%Y-%m-%d %H:%M:%S')
                appt3_id = request_appointment(conn_setup, p3_id, pv1_id, appt3_start, appt3_end, "Prescription Refill")
                if appt3_id:
                    update_appointment_status(conn_setup, appt3_id, 'confirmed', pv1_id, 'provider')
                    mark_reminder_sent(conn_setup, appt3_id, (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'))

                # Appt 4: Not confirmed (in 23.8 hours)
                appt4_start = (datetime.now() + timedelta(hours=23.8)).strftime('%Y-%m-%d %H:%M:%S')
                appt4_end = (datetime.now() + timedelta(hours=24.3)).strftime('%Y-%m-%d %H:%M:%S')
                request_appointment(conn_setup, p1_id, pv1_id, appt4_start, appt4_end, "Pending Consultation")

                print(f"  Test appointments created: Appt1={appt1_id}, Appt2={appt2_id}, Appt3={appt3_id}, Appt4(pending)")
                print("Test data setup finished.")
        except Exception as e_setup:
            print(f"ERROR during test data setup for reminder job: {e_setup}")

    # Default run: Send reminders for appointments that are approximately 24 hours away.
    send_reminders(time_window_start_hours_ahead=23,
                   time_window_end_hours_ahead=24,
                   reminder_grace_period_hours=2) # Don't resend if reminded in last 2 hours.

    # Example for a more immediate reminder window (e.g., 1 hour away)
    # print("\nRunning for 1-hour window (0-1 hours ahead), 0 grace period:")
    # send_reminders(time_window_start_hours_ahead=0,
    #                time_window_end_hours_ahead=1,
    #                reminder_grace_period_hours=0)
