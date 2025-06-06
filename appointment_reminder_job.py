from datetime import datetime, timedelta
import os
import sqlite3 # For specific error handling if needed by the job
from db_utils_appointment import (
    get_db_connection,
    get_appointments_needing_reminders,
    mark_reminder_sent,
    initialize_appointment_schema,
    request_appointment,
    update_appointment_status
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
    if not email_address: # Basic check for an email address
        print(f"  - Skipping email: No email address provided for appointment ID {appointment_details.get('appointment_id')}.")
        return False

    # Simulate sending: Log the action
    print(f"  - SIMULATING: Sending EMAIL reminder to {email_address} for appointment ID {appointment_details.get('appointment_id')} "
          f"at {appointment_details.get('appointment_start_time')} with {appointment_details.get('provider_username')}.")

    # Example of how a real email might be constructed and sent:
    # subject = f"Appointment Reminder: Your appointment for '{appointment_details.get('reason_for_visit', 'your visit')}'"
    # patient_name = appointment_details.get('patient_username', 'Patient')
    # provider_name = appointment_details.get('provider_username', 'your provider')
    # appt_start_time_str = appointment_details.get('appointment_start_time')
    # reason = appointment_details.get('reason_for_visit', 'your scheduled check-up')
    #
    # # Attempt to parse the datetime string to a datetime object for better formatting
    # try:
    #     appt_dt_obj = datetime.strptime(appt_start_time_str, '%Y-%m-%d %H:%M:%S')
    #     formatted_time = appt_dt_obj.strftime('%B %d, %Y at %I:%M %p') # Example: March 15, 2024 at 02:30 PM
    # except (ValueError, TypeError): # Fallback if parsing fails or appt_start_time_str is not a string
    #     formatted_time = appt_start_time_str
    #
    # body = (f"Dear {patient_name},\n\n"
    #         f"This is a reminder for your appointment for '{reason}' "
    #         f"scheduled for {formatted_time} with {provider_name}.\n\n"
    #         f"If you need to reschedule, please contact us as soon as possible.\n\n"
    #         f"Thank you,\nYour Healthcare Team")
    # print(f"    Subject: {subject}") # For logging/debugging
    # print(f"    Body Preview: {body[:100]}...") # Log a preview
    #
    # # Placeholder for actual email sending call, e.g.:
    # # email_send_success = send_email_via_external_service(email_address, subject, body)
    # # return email_send_success
    return True # Simulate successful sending

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
    if not phone_number: # Basic check for a phone number
        print(f"  - Skipping SMS: No phone number provided for appointment ID {appointment_details.get('appointment_id')}.")
        return False

    # Simulate sending: Log the action
    print(f"  - SIMULATING: Sending SMS reminder to {phone_number} for appointment ID {appointment_details.get('appointment_id')} "
          f"at {appointment_details.get('appointment_start_time')}.")

    # Example of how a real SMS might be constructed and sent:
    # provider_name = appointment_details.get('provider_username', 'your provider')
    # appt_start_time_str = appointment_details.get('appointment_start_time')
    # reason_summary = appointment_details.get('reason_for_visit', 'check-up')
    # if len(reason_summary) > 25: reason_summary = reason_summary[:22] + "..." # Keep SMS concise
    #
    # try:
    #     appt_dt_obj = datetime.strptime(appt_start_time_str, '%Y-%m-%d %H:%M:%S')
    #     formatted_time = appt_dt_obj.strftime('%b %d, %I:%M%p') # E.g., Mar 15, 02:30PM
    # except (ValueError, TypeError): # Fallback
    #     formatted_time = appt_start_time_str
    #
    # message = (f"Reminder: Your appt for '{reason_summary}' with {provider_name} is on {formatted_time}.")
    # print(f"    SMS Message: {message}") # For logging/debugging
    #
    # # Placeholder for actual SMS sending call, e.g.:
    # # sms_send_success = send_sms_via_gateway(phone_number, message)
    # # return sms_send_success
    return True # Simulate successful sending

# --- Core Logic ---

def send_reminders(time_window_start_hours_ahead: int = 23,
                   time_window_end_hours_ahead: int = 24,
                   reminder_grace_period_hours: int = 2
                  ):
    """
    Fetches upcoming confirmed appointments that require reminders and processes them.

    This function is designed to be run periodically (e.g., as a cron job).
    It identifies appointments within a specified future time window for which
    reminders haven't been sent recently (respecting a grace period).

    For each eligible appointment, it attempts to send email and/or SMS reminders
    (using placeholder functions for actual dispatch) to the patient. After attempting
    notifications, it updates the appointment record to mark that a reminder has been sent.

    Args:
        time_window_start_hours_ahead (int): Defines the start of the time window (in hours
                                             from the current time) for appointments to consider.
                                             E.g., 23 means appointments starting from 23 hours from now.
        time_window_end_hours_ahead (int): Defines the end of the time window (in hours
                                           from the current time) for appointments to consider.
                                           The window is effectively [start, end).
                                           E.g., 24 means appointments starting up to (but not including)
                                           24 hours from now.
        reminder_grace_period_hours (int): If a reminder was already sent for an appointment
                                           within this many hours from the current time,
                                           another reminder will not be sent. This prevents
                                           sending multiple reminders if the job runs frequently.
    """
    job_start_time = datetime.now()
    print(f"\n--- Starting Appointment Reminder Job ({job_start_time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
    print(f"Searching for appointments starting between {time_window_start_hours_ahead} and "
          f"{time_window_end_hours_ahead} hours from now.")
    print(f"Reminder grace period: {reminder_grace_period_hours} hours (reminders sent more recently than this will be skipped).")

    # Calculate the absolute start and end datetime strings for the database query window
    # Example: If job runs at 10:00, start_hours=23, end_hours=24,
    # window will be from 09:00 tomorrow to 10:00 tomorrow.
    window_start_dt = job_start_time + timedelta(hours=time_window_start_hours_ahead)
    window_end_dt = job_start_time + timedelta(hours=time_window_end_hours_ahead)
    window_start_iso = window_start_dt.strftime('%Y-%m-%d %H:%M:%S')
    window_end_iso = window_end_dt.strftime('%Y-%m-%d %H:%M:%S')

    print(f"Calculated reminder query window: APPOINTMENT_START_TIME >= '{window_start_iso}' AND APPOINTMENT_START_TIME < '{window_end_iso}'")

    # Establish database connection using a context manager to ensure it's closed
    with get_db_connection(DB_NAME) as conn:
        try:
            # Fetch appointments that are confirmed and meet the criteria for needing a reminder
            appointments_to_remind = get_appointments_needing_reminders(
                conn, window_start_iso, window_end_iso, reminder_grace_period_hours
            )

            if not appointments_to_remind:
                print("No appointments found needing reminders in the specified window.")
                return

            print(f"Found {len(appointments_to_remind)} appointments needing reminders.")
            successful_reminders_marked_count = 0
            failed_reminders_marked_count = 0
            notifications_attempted_for_appt_count = 0

            for appt_details in appointments_to_remind:
                appt_id = appt_details['appointment_id'] # For convenience
                print(f"\nProcessing Appointment ID: {appt_id} "
                      f"(Patient: {appt_details['patient_username']}, Provider: {appt_details['provider_username']}) "
                      f"scheduled at {appt_details['appointment_start_time']}")
                print(f"  Details: Last reminder sent at: {appt_details['last_reminder_sent_at'] or 'Never'}")

                at_least_one_notification_sent_successfully = False # Tracks if any send attempt was "successful"

                # Attempt to send email reminder to the patient
                if appt_details.get("patient_email"):
                    if send_email_reminder(appt_details["patient_email"], appt_details):
                        at_least_one_notification_sent_successfully = True
                else:
                    print(f"  - No patient email found for appointment {appt_id}.")

                # Attempt to send SMS reminder to the patient
                if appt_details.get("patient_phone"):
                    if send_sms_reminder(appt_details["patient_phone"], appt_details):
                        at_least_one_notification_sent_successfully = True
                else:
                    print(f"  - No patient phone found for appointment {appt_id}.")

                if at_least_one_notification_sent_successfully:
                    notifications_attempted_for_appt_count +=1
                    # Mark reminder as sent only if at least one notification was "successfully" processed/attempted.
                    # In a real system with actual send status from providers, this logic might be more nuanced
                    # (e.g., mark only if confirmed delivery, or mark per channel).
                    try:
                        if mark_reminder_sent(conn, appt_id): # Uses current time by default
                            print(f"  Successfully marked reminder as sent for appointment ID {appt_id}.")
                            successful_reminders_marked_count +=1
                        else:
                            # This case implies appointment_id was not found during UPDATE by mark_reminder_sent,
                            # which should be unlikely if it was just fetched.
                            print(f"  WARNING: Failed to mark reminder (rowcount 0) for appointment ID {appt_id}.")
                            failed_reminders_marked_count += 1
                    except sqlite3.Error as e_mark: # Catch specific error from mark_reminder_sent
                        print(f"  ERROR: Database error while marking reminder for appointment ID {appt_id}: {e_mark}")
                        failed_reminders_marked_count += 1 # Count as failed if marking in DB fails
                else:
                    print(f"  No contact information (email/phone) suitable for sending for appointment ID {appt_id}, "
                          f"or both simulated sends failed.")

            # Summary logging
            print(f"\n--- Reminder Processing Summary ---")
            print(f"  Appointments processed for potential reminders: {len(appointments_to_remind)}")
            print(f"  Notifications attempted for (had contacts & at least one simulated send success): {notifications_attempted_for_appt_count} appointments")
            print(f"  Successfully marked as reminded in DB: {successful_reminders_marked_count}")
            # This counts appointments where marking failed OR where no notification was even attempted due to missing contacts/send failures.
            truly_failed_or_skipped_marking = len(appointments_to_remind) - successful_reminders_marked_count
            print(f"  Failed to mark or skipped marking (no contacts/send fail): {truly_failed_or_skipped_marking}")


        except sqlite3.Error as e_db:
            # Errors from get_appointments_needing_reminders or connection issues
            print(f"A database error occurred during the reminder job's main processing: {e_db}")
        except ValueError as ve:
             # Catches ValueErrors from get_appointments_needing_reminders (e.g., bad date format in args)
             print(f"Configuration or data error for reminder job: {ve}")
        except Exception as e_unexpected:
            # Catch any other unexpected errors to prevent the job from crashing silently
            print(f"An unexpected error occurred during the reminder job: {e_unexpected}")
        finally:
            job_end_time = datetime.now()
            print(f"--- Reminder Job Finished ({job_end_time.strftime('%Y-%m-%d %H:%M:%S')}, Duration: {job_end_time - job_start_time}) ---")

if __name__ == '__main__':
    """
    This script is intended to be run as a scheduled job (e.g., using cron or a task scheduler).

    Prerequisites for running:
    1. Database Accessibility: The database file specified by `DB_NAME` (or the default
       'appointment_app.db') must be accessible and writable by the user running this script.
       The `APPOINTMENT_DB_NAME` environment variable can be set to specify a different database file.
    2. Schema Initialization: The database schema (tables like `users`, `appointments`)
       must be initialized. This can be done by running `db_utils_appointment.py` directly
       if its `if __name__ == '__main__':` block includes schema setup, or by using
       a separate migration/setup script.
    3. Populated Data: There should be user and appointment data in the database.
       Specifically, `users` should have `email` and `phone` fields populated for
       patients who should receive reminders. Appointments should be in 'confirmed' status
       and fall within the job's processing window.
    4. Notification Service Integration: The placeholder functions `send_email_reminder`
       and `send_sms_reminder` must be replaced with actual integrations with
       email and SMS sending services (e.g., SMTP libraries, Twilio API, AWS SES/SNS).

    Example for setting up test data (run this once, or manage via an env var):
    If you set the environment variable SETUP_TEST_DATA_FOR_REMINDER_JOB=true,
    the example block below will attempt to initialize the schema and add sample data.
    This helps in testing the reminder job directly.
    """
    print(f"Running Appointment Reminder Job for DB: {DB_NAME}")

    # Optional: Setup test data if an environment variable is set
    if os.getenv('SETUP_TEST_DATA_FOR_REMINDER_JOB', 'false').lower() == 'true':
        print("Attempting to set up test data for reminder job demo...")
        try:
            # Use a 'with' statement to ensure the setup connection is closed.
            with get_db_connection(DB_NAME) as conn_setup:
                initialize_appointment_schema(conn_setup) # Ensure schema exists
                cursor = conn_setup.cursor()

                users_for_job_data = [
                    ('rem_patient1', 'patient1.rem@example.com', '5550001111'),
                    ('rem_provider1', 'provider.rem@example.com', '5550002222'),
                    ('rem_patient2_noemail', None, '5550003333'), # Patient with no email
                    ('rem_patient3_nophone', 'patient3.rem@example.com', None), # Patient with no phone
                ]
                user_ids_map = {}
                print("  Ensuring test users exist...")
                for uname, uemail, uphone in users_for_job_data:
                    # Using INSERT OR IGNORE to avoid errors if users already exist.
                    # Then, update email/phone to ensure they have the test values.
                    cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?,?,?)", (uname, uemail, uphone))
                    if cursor.lastrowid == 0: # User likely existed if lastrowid is 0 after OR IGNORE
                        cursor.execute("SELECT user_id FROM users WHERE username = ?", (uname,))
                        user_id = cursor.fetchone()['user_id']
                        # Update email/phone in case they changed for the test run or were missing
                        cursor.execute("UPDATE users SET email=?, phone=? WHERE user_id=?", (uemail, uphone, user_id))
                        user_ids_map[uname] = user_id
                    else:
                        user_ids_map[uname] = cursor.lastrowid
                conn_setup.commit() # Commit user creation/updates

                p1_id = user_ids_map['rem_patient1']
                pv1_id = user_ids_map['rem_provider1']
                p2_id = user_ids_map['rem_patient2_noemail']
                p3_id = user_ids_map['rem_patient3_nophone']
                print(f"  Test user IDs: Patient1={p1_id}, Provider1={pv1_id}, Patient2(no_email)={p2_id}, Patient3(no_phone)={p3_id}")

                print("  Setting up test appointments...")
                # Appt 1: Needs reminder (in 23.5 hours, never reminded) - Patient1 has email & phone
                appt1_start = (datetime.now() + timedelta(hours=23.5)).strftime('%Y-%m-%d %H:%M:%S')
                appt1_end = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                appt1_id = request_appointment(conn_setup, p1_id, pv1_id, appt1_start, appt1_end, "Annual Physical Reminder")
                if appt1_id: update_appointment_status(conn_setup, appt1_id, 'confirmed', pv1_id, 'provider')

                # Appt 2: Needs reminder (in 23.7 hours, reminder sent long ago) - Patient2 has only phone
                appt2_start = (datetime.now() + timedelta(hours=23.7)).strftime('%Y-%m-%d %H:%M:%S')
                appt2_end = (datetime.now() + timedelta(hours=24.2)).strftime('%Y-%m-%d %H:%M:%S')
                appt2_id = request_appointment(conn_setup, p2_id, pv1_id, appt2_start, appt2_end, "Lab Follow-up Reminder")
                if appt2_id:
                    update_appointment_status(conn_setup, appt2_id, 'confirmed', pv1_id, 'provider')
                    # Mark as reminded more than 'reminder_grace_period_hours' ago
                    mark_reminder_sent(conn_setup, appt2_id, (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'))

                # Appt 3: Too recent reminder (in 23.6 hours, reminded 30 mins ago) - Patient3 has only email
                appt3_start = (datetime.now() + timedelta(hours=23.6)).strftime('%Y-%m-%d %H:%M:%S')
                appt3_end = (datetime.now() + timedelta(hours=24.1)).strftime('%Y-%m-%d %H:%M:%S')
                appt3_id = request_appointment(conn_setup, p3_id, pv1_id, appt3_start, appt3_end, "Prescription Check Reminder")
                if appt3_id:
                    update_appointment_status(conn_setup, appt3_id, 'confirmed', pv1_id, 'provider')
                    # Mark as reminded very recently
                    mark_reminder_sent(conn_setup, appt3_id, (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'))

                # Appt 4: Not confirmed (in 23.8 hours) - Patient1
                appt4_start = (datetime.now() + timedelta(hours=23.8)).strftime('%Y-%m-%d %H:%M:%S')
                appt4_end = (datetime.now() + timedelta(hours=24.3)).strftime('%Y-%m-%d %H:%M:%S')
                request_appointment(conn_setup, p1_id, pv1_id, appt4_start, appt4_end, "Pending Consultation") # Remains pending

                print(f"  Test appointments created/updated: Appt1_ID={appt1_id}, Appt2_ID={appt2_id}, Appt3_ID={appt3_id}, Appt4(pending)")
                print("Test data setup finished.")
        except Exception as e_setup:
            print(f"ERROR during test data setup for reminder job: {e_setup}")

    # Default run: Send reminders for appointments that are approximately 24 hours away.
    # This means appointments starting between 23 and 24 hours (exclusive of 24) from the current time.
    send_reminders(time_window_start_hours_ahead=23,
                   time_window_end_hours_ahead=24,
                   reminder_grace_period_hours=2) # Don't resend if reminded in last 2 hours.

    # Example for a more immediate reminder window (e.g., for appointments starting in next hour)
    # print("\nRunning for 1-hour window (0-1 hours ahead), 0 grace period (send even if reminded recently):")
    # send_reminders(time_window_start_hours_ahead=0,
    #                time_window_end_hours_ahead=1,
    #                reminder_grace_period_hours=0) # Set grace to 0 to force reminder for testing this window
