import sqlite3
from datetime import datetime # For type hinting and potential future use, though SQLite handles text dates

# --- Database Schema (SQLite Compatible) ---
APPOINTMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT NULLABLE, -- Added for reminders
    phone TEXT NULLABLE, -- Added for reminders
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) -- SQLite specific default
);

CREATE TABLE IF NOT EXISTS provider_availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    recurring_rule TEXT NULL, -- Storing as TEXT, actual parsing/handling in app logic
    FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_start_end_availability CHECK (STRFTIME('%s', end_datetime) > STRFTIME('%s', start_datetime)) -- Compare as unix timestamps
);

CREATE INDEX IF NOT EXISTS idx_pa_provider_id ON provider_availability(provider_id);
CREATE INDEX IF NOT EXISTS idx_pa_start_datetime ON provider_availability(start_datetime);
CREATE INDEX IF NOT EXISTS idx_pa_end_datetime ON provider_availability(end_datetime);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    appointment_start_time DATETIME NOT NULL,
    appointment_end_time DATETIME NOT NULL,
    reason_for_visit TEXT NULL,
    status TEXT NOT NULL DEFAULT 'pending_provider_confirmation', -- VARCHAR(50) becomes TEXT
    video_room_name TEXT NULL, -- VARCHAR(255) becomes TEXT
    notes_by_patient TEXT NULL,
    notes_by_provider TEXT NULL,
    last_reminder_sent_at DATETIME NULL, -- New column for reminder tracking
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    updated_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_start_end_appointment CHECK (STRFTIME('%s', appointment_end_time) > STRFTIME('%s', appointment_start_time))
);

CREATE INDEX IF NOT EXISTS idx_appt_patient_id ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appt_provider_id ON appointments(provider_id);
CREATE INDEX IF NOT EXISTS idx_appt_start_time ON appointments(appointment_start_time);
CREATE INDEX IF NOT EXISTS idx_appt_status ON appointments(status);

-- Trigger for appointments.updated_at
CREATE TRIGGER IF NOT EXISTS update_appointments_updated_at
AFTER UPDATE ON appointments
FOR EACH ROW
WHEN OLD.updated_at = NEW.updated_at -- Avoid infinite loop if updated_at was explicitly set
BEGIN
    UPDATE appointments SET updated_at = (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
    WHERE appointment_id = OLD.appointment_id;
END;
"""
# Note on recurring_rule: VARCHAR(255) becomes TEXT in SQLite.
# Note on chk_start_end_availability and chk_start_end_appointment:
# SQLite datetime comparisons are safer with unix timestamps (STRFTIME('%s', ...)) or ensuring ISO8601 format.

def get_db_connection(db_name='appointment_app.db'):
    """
    Establishes and returns an SQLite3 connection object.
    Configured for row factory access and foreign key enforcement.
    """
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraint enforcement
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error to '{db_name}': {e}")
        raise

def initialize_appointment_schema(conn: sqlite3.Connection):
    """
    Initializes the appointment-related database schema.
    Creates users, provider_availability, and appointments tables, and associated triggers.
    """
    try:
        cursor = conn.cursor()
        cursor.executescript(APPOINTMENT_SCHEMA)
        conn.commit()
        print("Appointment database schema initialized successfully.")
    except sqlite3.Error as e:
        print(f"Appointment schema initialization error: {e}")
        conn.rollback()
        raise

def add_provider_availability(conn: sqlite3.Connection, provider_id: int, start_datetime: str, end_datetime: str, recurring_rule: str = None) -> int | None:
    """
    Adds a new availability block for a provider.

    Args:
        conn: Active SQLite3 connection.
        provider_id: The ID of the provider.
        start_datetime: Availability start time (YYYY-MM-DD HH:MM:SS string).
        end_datetime: Availability end time (YYYY-MM-DD HH:MM:SS string).
        recurring_rule: Optional iCalendar RRULE string for recurring availability.

    Returns:
        The availability_id of the newly added record, or None on failure before insert.

    Raises:
        ValueError: If input parameters are invalid.
        sqlite3.Error: If a database error occurs (e.g., IntegrityError for FK or CHECK constraint).
    """
    if not all([isinstance(provider_id, int), isinstance(start_datetime, str), isinstance(end_datetime, str)]):
        raise ValueError("Invalid input types for provider availability.")
    # Basic format validation could be added here for datetime strings.
    # The CHECK constraint in DB handles start_datetime < end_datetime.

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO provider_availability (provider_id, start_datetime, end_datetime, recurring_rule)
            VALUES (?, ?, ?, ?)
            """,
            (provider_id, start_datetime, end_datetime, recurring_rule)
        )
        conn.commit()
        new_availability_id = cursor.lastrowid
        if new_availability_id is None:
             raise sqlite3.Error("Failed to retrieve lastrowid for new availability.")
        return new_availability_id
    except sqlite3.Error as e:
        print(f"Error in add_provider_availability for provider {provider_id}: {e}")
        conn.rollback()
        raise # Re-raise to allow API layer to handle it

def get_provider_availability(conn: sqlite3.Connection, provider_id: int, start_filter: str = None, end_filter: str = None) -> list[dict]:
    """
    Fetches availability blocks for a given provider, optionally filtered by a time range.

    Args:
        conn: Active SQLite3 connection.
        provider_id: The ID of the provider.
        start_filter: Optional start of the filter window (YYYY-MM-DD HH:MM:SS string).
        end_filter: Optional end of the filter window (YYYY-MM-DD HH:MM:SS string).
                      If filtering, both start_filter and end_filter should be provided.

    Returns:
        A list of dictionaries, each representing an availability block.
        Returns empty list if no availability or on error.
    """
    if not isinstance(provider_id, int):
        raise ValueError("provider_id must be an integer.")

    cursor = conn.cursor()
    availability_blocks = []

    query = "SELECT availability_id, provider_id, start_datetime, end_datetime, recurring_rule FROM provider_availability WHERE provider_id = ?"
    params = [provider_id]

    if start_filter and end_filter:
        # Find availability blocks that overlap with the filter window [start_filter, end_filter)
        # Overlap condition: avail.start_datetime < end_filter AND avail.end_datetime > start_filter
        query += " AND start_datetime < ? AND end_datetime > ?"
        params.extend([end_filter, start_filter])

    query += " ORDER BY start_datetime ASC"

    try:
        cursor.execute(query, tuple(params))
        for row in cursor.fetchall():
            availability_blocks.append(dict(row))
        return availability_blocks
    except sqlite3.Error as e:
        print(f"Error in get_provider_availability for provider {provider_id}: {e}")
        return [] # Return empty list on error

def delete_provider_availability(conn: sqlite3.Connection, availability_id: int, provider_id: int) -> bool:
    """
    Deletes a specific availability block if it belongs to the specified provider.

    Args:
        conn: Active SQLite3 connection.
        availability_id: The ID of the availability block to delete.
        provider_id: The ID of the provider claiming ownership (for authorization).

    Returns:
        True if the deletion was successful (1 row affected), False otherwise.

    Raises:
        ValueError: If input IDs are not integers.
        sqlite3.Error: If a database error occurs.
    """
    if not isinstance(availability_id, int) or not isinstance(provider_id, int):
        raise ValueError("availability_id and provider_id must be integers.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM provider_availability WHERE availability_id = ? AND provider_id = ?",
            (availability_id, provider_id)
        )
        conn.commit()
        return cursor.rowcount > 0 # True if a row was deleted
    except sqlite3.Error as e:
        print(f"Error in delete_provider_availability for ID {availability_id}, provider {provider_id}: {e}")
        conn.rollback()
        raise


if __name__ == '__main__':
    import os
    db_file = 'test_appointment_utils.db'
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = get_db_connection(db_file)
    print(f"\nInitializing appointment schema in {db_file}...")
    initialize_appointment_schema(conn)

    try:
        print("\n--- Testing Appointment DB Utils ---")
        cursor = conn.cursor()

        # 1. Create Test Users (Providers)
        provider1_id, provider2_id = None, None
        try:
            cursor.execute("INSERT INTO users (username) VALUES (?)", ('prov_alice',))
            provider1_id = cursor.lastrowid
            cursor.execute("INSERT INTO users (username) VALUES (?)", ('prov_bob',))
            provider2_id = cursor.lastrowid
            conn.commit()
            print(f"Created providers: Alice (ID: {provider1_id}), Bob (ID: {provider2_id})")
        except sqlite3.IntegrityError: # If run multiple times and users exist
            cursor.execute("SELECT user_id FROM users WHERE username = 'prov_alice'")
            provider1_id = cursor.fetchone()['user_id']
            cursor.execute("SELECT user_id FROM users WHERE username = 'prov_bob'")
            provider2_id = cursor.fetchone()['user_id']
            print(f"Fetched existing providers: Alice (ID: {provider1_id}), Bob (ID: {provider2_id})")

        assert provider1_id is not None and provider2_id is not None

        # 2. Add Provider Availability
        print("\nAdding availability...")
        avail1_p1 = add_provider_availability(conn, provider1_id, "2024-04-01 09:00:00", "2024-04-01 12:00:00")
        avail2_p1 = add_provider_availability(conn, provider1_id, "2024-04-01 14:00:00", "2024-04-01 17:00:00", "FREQ=WEEKLY;BYDAY=MO")
        avail1_p2 = add_provider_availability(conn, provider2_id, "2024-04-02 10:00:00", "2024-04-02 15:00:00")
        print(f"Alice's availability IDs: {avail1_p1}, {avail2_p1}")
        print(f"Bob's availability ID: {avail1_p2}")
        assert avail1_p1 is not None and avail2_p1 is not None and avail1_p2 is not None

        # Test CHECK constraint (start_datetime > end_datetime) - should fail
        try:
            add_provider_availability(conn, provider1_id, "2024-04-01 12:00:00", "2024-04-01 09:00:00")
            print("ERROR: Added availability with start > end, CHECK constraint failed.")
        except sqlite3.IntegrityError as ie:
            print(f"Successfully caught IntegrityError for invalid time range: {ie}")

        # 3. Get Provider Availability
        print(f"\nGetting Alice's (ID: {provider1_id}) availability (all):")
        alice_avail_all = get_provider_availability(conn, provider1_id)
        for slot in alice_avail_all: print(f"  {dict(slot)}")
        assert len(alice_avail_all) == 2

        print(f"\nGetting Alice's availability (filtered for 2024-04-01 08:00 to 10:00):")
        alice_avail_filtered = get_provider_availability(conn, provider1_id, "2024-04-01 08:00:00", "2024-04-01 10:00:00")
        for slot in alice_avail_filtered: print(f"  {dict(slot)}")
        assert len(alice_avail_filtered) == 1
        assert alice_avail_filtered[0]['availability_id'] == avail1_p1

        print(f"\nGetting Alice's availability (filtered, no overlap):")
        alice_avail_none = get_provider_availability(conn, provider1_id, "2024-05-01 08:00:00", "2024-05-01 10:00:00")
        assert len(alice_avail_none) == 0
        print(f"  (Correctly none)")


        # 4. Delete Provider Availability
        print("\nDeleting availability...")
        # Alice tries to delete Bob's slot (should fail)
        deleted_wrong_provider = delete_provider_availability(conn, avail1_p2, provider1_id)
        print(f"Alice deleting Bob's slot (ID {avail1_p2}): Success = {deleted_wrong_provider}")
        assert not deleted_wrong_provider

        # Alice deletes her own slot
        deleted_own = delete_provider_availability(conn, avail1_p1, provider1_id)
        print(f"Alice deleting her own slot (ID {avail1_p1}): Success = {deleted_own}")
        assert deleted_own

        # Verify deletion
        alice_avail_after_delete = get_provider_availability(conn, provider1_id)
        print(f"Alice's availability after delete ({len(alice_avail_after_delete)}):")
        for slot in alice_avail_after_delete: print(f"  {dict(slot)}")
        assert len(alice_avail_after_delete) == 1
        assert alice_avail_after_delete[0]['availability_id'] == avail2_p1

        print("\nAll appointment DB util tests passed successfully (basic assertions).")

    except ValueError as ve:
        print(f"ValueError in example usage: {ve}")
    except sqlite3.Error as e:
        print(f"An SQLite error occurred in example usage: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred in example usage: {ex}")
    finally:
        if conn:
            conn.close()
            print(f"\nClosed connection to {db_file}.")
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed test database {db_file}.")


def get_appointments_needing_reminders(conn: sqlite3.Connection, window_start_iso: str,
                                       window_end_iso: str, reminder_grace_period_hours: int = 1) -> list[dict]:
    """
    Fetches confirmed appointments within a specified time window that need a reminder.

    An appointment needs a reminder if:
    - Its status is 'confirmed'.
    - Its `appointment_start_time` is between `window_start_iso` and `window_end_iso`.
    - Its `last_reminder_sent_at` is NULL OR it was sent earlier than
      (now - reminder_grace_period_hours).

    Args:
        conn: Active SQLite3 connection.
        window_start_iso: ISO format datetime string for the start of the reminder window.
        window_end_iso: ISO format datetime string for the end of the reminder window.
        reminder_grace_period_hours: How many hours ago a reminder must have been sent
                                     for it to be considered "recent enough" to not send another.

    Returns:
        A list of appointment dictionaries, including patient and provider contact info (if available).
        Each dictionary includes: appointment_id, patient_id, provider_id, appointment_start_time,
        patient_username, patient_email, patient_phone, provider_username, provider_email, provider_phone.

    Raises:
        ValueError: For invalid input datetime formats or grace period.
        sqlite3.Error: For database errors.
    """
    if not all(isinstance(arg, str) for arg in [window_start_iso, window_end_iso]):
        raise ValueError("window_start_iso and window_end_iso must be string representations of datetime.")
    try:
        datetime.strptime(window_start_iso, '%Y-%m-%d %H:%M:%S')
        datetime.strptime(window_end_iso, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise ValueError("Invalid ISO datetime format for window_start_iso or window_end_iso. Use YYYY-MM-DD HH:MM:SS.")
    if not isinstance(reminder_grace_period_hours, int) or reminder_grace_period_hours < 0:
        raise ValueError("reminder_grace_period_hours must be a non-negative integer.")

    appointments_to_remind = []
    cursor = conn.cursor()

    # Calculate the cutoff time for "recent enough" reminders
    grace_period_cutoff_dt = datetime.now() - datetime.timedelta(hours=reminder_grace_period_hours)
    grace_period_cutoff_iso = grace_period_cutoff_dt.strftime('%Y-%m-%d %H:%M:%S')

    query = """
    SELECT
        a.appointment_id,
        a.patient_id,
        a.provider_id,
        a.appointment_start_time,
        a.reason_for_visit,
        a.last_reminder_sent_at,
        pat.username AS patient_username,
        pat.email AS patient_email,
        pat.phone AS patient_phone,
        pro.username AS provider_username,
        pro.email AS provider_email,
        pro.phone AS provider_phone
    FROM appointments a
    JOIN users pat ON a.patient_id = pat.user_id
    JOIN users pro ON a.provider_id = pro.user_id
    WHERE
        a.status = 'confirmed'
        AND a.appointment_start_time >= ?
        AND a.appointment_start_time < ?
        AND (
            a.last_reminder_sent_at IS NULL
            OR a.last_reminder_sent_at < ?
        );
    """
    # Parameters for the query
    params = (window_start_iso, window_end_iso, grace_period_cutoff_iso)

    try:
        cursor.execute(query, params)
        for row in cursor.fetchall():
            appointments_to_remind.append(dict(row))
        return appointments_to_remind
    except sqlite3.Error as e:
        print(f"Error in get_appointments_needing_reminders: {e}")
        raise # Re-raise to be handled by the job scheduler or caller


if __name__ == '__main__':
    import os
    db_file = 'test_appointment_utils.db'

def mark_reminder_sent(conn: sqlite3.Connection, appointment_id: int, reminder_time: str = None) -> bool:
    """
    Marks an appointment as having a reminder sent by updating the last_reminder_sent_at field.

    Args:
        conn: Active SQLite3 connection.
        appointment_id: The ID of the appointment to update.
        reminder_time: Optional ISO format datetime string (YYYY-MM-DD HH:MM:SS) for when the
                       reminder was sent. If None, the current timestamp is used.

    Returns:
        True if the update was successful (1 row affected), False otherwise.

    Raises:
        ValueError: If appointment_id is not an integer or reminder_time format is invalid (if provided).
        sqlite3.Error: If a database error occurs.
    """
    if not isinstance(appointment_id, int):
        raise ValueError("appointment_id must be an integer.")

    if reminder_time:
        # Optional: Validate reminder_time format if strictness is needed here,
        # though SQLite will often accept various formats if they are unambiguous.
        # For consistency, ensure YYYY-MM-DD HH:MM:SS
        try:
            datetime.strptime(reminder_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Invalid reminder_time format. Use YYYY-MM-DD HH:MM:SS.")
        timestamp_to_set = reminder_time
    else:
        timestamp_to_set = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE appointments SET last_reminder_sent_at = ? WHERE appointment_id = ?",
            (timestamp_to_set, appointment_id)
        )
        conn.commit()
        return cursor.rowcount > 0 # True if a row was updated
    except sqlite3.Error as e:
        print(f"Error in mark_reminder_sent for appointment {appointment_id}: {e}")
        conn.rollback()
        raise

# --- Appointment Management Functions ---

def request_appointment(conn: sqlite3.Connection, patient_id: int, provider_id: int,
                        start_time: str, end_time: str, reason_for_visit: str = None,
                        notes_by_patient: str = None) -> int | None:
    """
    Inserts a new appointment request into the appointments table.
    The initial status is set to 'pending_provider_confirmation'.

    Args:
        conn: Active SQLite3 connection.
        patient_id: ID of the patient requesting the appointment.
        provider_id: ID of the provider for the appointment.
        start_time: Scheduled start time (YYYY-MM-DD HH:MM:SS string).
        end_time: Scheduled end time (YYYY-MM-DD HH:MM:SS string).
        reason_for_visit: Optional reason for the visit.
        notes_by_patient: Optional notes from the patient.

    Returns:
        The appointment_id of the newly created appointment, or None on failure before insert.

    Raises:
        ValueError: If input parameters are invalid (e.g., non-integer IDs).
        sqlite3.Error: If a database error occurs (e.g., FK constraint, CHECK constraint).
    """
    if not all(isinstance(id_val, int) for id_val in [patient_id, provider_id]):
        raise ValueError("patient_id and provider_id must be integers.")
    if not all(isinstance(time_str, str) for time_str in [start_time, end_time]):
        raise ValueError("start_time and end_time must be string representations of datetime.")
    # DB CHECK constraint handles end_time > start_time

    cursor = conn.cursor()
    initial_status = 'pending_provider_confirmation'
    # created_at and updated_at have defaults in schema. updated_at will be handled by trigger on UPDATE.

    try:
        cursor.execute(
            """
            INSERT INTO appointments (patient_id, provider_id, appointment_start_time, appointment_end_time,
                                      reason_for_visit, status, notes_by_patient)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (patient_id, provider_id, start_time, end_time, reason_for_visit, initial_status, notes_by_patient)
        )
        conn.commit()
        new_appointment_id = cursor.lastrowid
        if new_appointment_id is None:
            raise sqlite3.Error("Failed to retrieve lastrowid for new appointment.")
        return new_appointment_id
    except sqlite3.Error as e:
        print(f"Error in request_appointment: {e}")
        conn.rollback()
        raise

def get_appointment_by_id(conn: sqlite3.Connection, appointment_id: int) -> dict | None:
    """
    Fetches a specific appointment by its appointment_id, including patient and provider usernames.

    Args:
        conn: Active SQLite3 connection.
        appointment_id: The ID of the appointment to fetch.

    Returns:
        A dictionary representing the appointment with 'patient_username' and
        'provider_username', or None if not found or on error.

    Raises:
        ValueError: If appointment_id is not an integer.
    """
    if not isinstance(appointment_id, int):
        raise ValueError("appointment_id must be an integer.")

    cursor = conn.cursor()
    query = """
    SELECT
        a.*,
        p.username AS patient_username,
        pv.username AS provider_username
    FROM appointments a
    JOIN users p ON a.patient_id = p.user_id
    JOIN users pv ON a.provider_id = pv.user_id
    WHERE a.appointment_id = ?;
    """
    try:
        cursor.execute(query, (appointment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error in get_appointment_by_id for appointment {appointment_id}: {e}")
        return None

def get_appointments_for_user(conn: sqlite3.Connection, user_id: int, user_role: str,
                              status_filter: str = None, start_date_filter: str = None,
                              end_date_filter: str = None) -> list[dict]:
    """
    Fetches appointments for a user based on their role (patient or provider),
    with optional filters for status and date range. Includes patient and provider usernames.

    Args:
        conn: Active SQLite3 connection.
        user_id: The ID of the user.
        user_role: Role of the user ('patient' or 'provider').
        status_filter: Optional status to filter appointments by.
        start_date_filter: Optional start date for filtering (YYYY-MM-DD string, inclusive).
        end_date_filter: Optional end date for filtering (YYYY-MM-DD string, inclusive).
                         The filter applies to `appointment_start_time`.

    Returns:
        A list of dictionaries, each representing an appointment. Empty list if none found or on error.

    Raises:
        ValueError: If user_id is not int, or user_role is invalid.
    """
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer.")
    if user_role not in ['patient', 'provider']:
        raise ValueError("user_role must be 'patient' or 'provider'.")

    appointments_list = []
    cursor = conn.cursor()

    params = []
    base_query = """
    SELECT
        a.*,
        p.username AS patient_username,
        pv.username AS provider_username
    FROM appointments a
    JOIN users p ON a.patient_id = p.user_id
    JOIN users pv ON a.provider_id = pv.user_id
    WHERE
    """

    if user_role == 'patient':
        base_query += "a.patient_id = ?"
    else: # user_role == 'provider'
        base_query += "a.provider_id = ?"
    params.append(user_id)

    if status_filter:
        base_query += " AND a.status = ?"
        params.append(status_filter)

    if start_date_filter: # Assumes YYYY-MM-DD, so compare date part of datetime column
        base_query += " AND DATE(a.appointment_start_time) >= DATE(?)"
        params.append(start_date_filter)

    if end_date_filter:
        base_query += " AND DATE(a.appointment_start_time) <= DATE(?)"
        params.append(end_date_filter)

    base_query += " ORDER BY a.appointment_start_time ASC"

    try:
        cursor.execute(base_query, tuple(params))
        for row in cursor.fetchall():
            appointments_list.append(dict(row))
        return appointments_list
    except sqlite3.Error as e:
        print(f"Error in get_appointments_for_user (user {user_id}, role {user_role}): {e}")
        return []

def update_appointment_status(conn: sqlite3.Connection, appointment_id: int, new_status: str,
                              current_user_id: int, user_role: str, notes: str = None) -> bool:
    """
    Updates the status of an appointment with authorization checks.
    Can also update notes and video_room_name based on role and new_status.

    Args:
        conn: Active SQLite3 connection.
        appointment_id: The ID of the appointment to update.
        new_status: The new status for the appointment.
        current_user_id: The ID of the user performing the update.
        user_role: Role of the current user ('patient' or 'provider').
        notes: Optional notes related to the status change.

    Returns:
        True if the update was successful and authorized, False otherwise.

    Raises:
        ValueError: For invalid inputs.
        sqlite3.Error: For database errors during fetch or update.
    """
    if not all(isinstance(val, int) for val in [appointment_id, current_user_id]):
        raise ValueError("appointment_id and current_user_id must be integers.")
    if user_role not in ['patient', 'provider']:
        raise ValueError("user_role must be 'patient' or 'provider'.")
    if not isinstance(new_status, str) or not new_status.strip():
        raise ValueError("new_status must be a non-empty string.")

    cursor = conn.cursor()

    try:
        # 1. Fetch current appointment details for authorization
        cursor.execute("SELECT patient_id, provider_id, status FROM appointments WHERE appointment_id = ?", (appointment_id,))
        appointment = cursor.fetchone()

        if not appointment:
            print(f"Update failed: Appointment ID {appointment_id} not found.")
            return False

        # 2. Authorization Check
        can_update = False
        if user_role == 'patient' and appointment['patient_id'] == current_user_id:
            # Patients might only be allowed to cancel their own appointments to specific statuses
            if new_status == 'cancelled_by_patient':
                can_update = True
        elif user_role == 'provider' and appointment['provider_id'] == current_user_id:
            # Providers can confirm, cancel, or mark as completed their appointments
            if new_status in ['confirmed', 'cancelled_by_provider', 'completed', 'rescheduled_by_provider']: # Example statuses
                can_update = True

        if not can_update:
            print(f"Authorization failed: User {current_user_id} (role: {user_role}) cannot set status '{new_status}' for appointment {appointment_id}.")
            return False

        # 3. Prepare fields to update
        fields_to_update = {"status": new_status}
        if notes:
            if user_role == 'patient':
                fields_to_update["notes_by_patient"] = notes
            elif user_role == 'provider':
                fields_to_update["notes_by_provider"] = notes

        if new_status == 'confirmed' and user_role == 'provider':
            # Generate video_room_name if confirming
            timestamp_part = datetime.now().strftime('%Y%m%d%H%M%S%f') # High precision timestamp part
            fields_to_update["video_room_name"] = f"ApptRoom_{appointment_id}_{timestamp_part[-6:]}" # last 6 for microsecs


        # Build the SET part of the SQL query dynamically
        set_clauses = [f"{field} = ?" for field in fields_to_update.keys()]
        sql_params = list(fields_to_update.values())
        sql_params.append(appointment_id) # For the WHERE clause

        # The updated_at field is handled by the trigger in SQLite for this schema.
        # If not using a trigger, add: `set_clauses.append("updated_at = (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))")`

        update_query = f"UPDATE appointments SET {', '.join(set_clauses)} WHERE appointment_id = ?"

        cursor.execute(update_query, tuple(sql_params))
        conn.commit()

        return cursor.rowcount > 0 # True if a row was updated

    except sqlite3.Error as e:
        print(f"Error in update_appointment_status for appointment {appointment_id}: {e}")
        conn.rollback()
        raise # Re-raise to be handled by API layer or caller


if __name__ == '__main__':
    import os
    db_file = 'test_appointment_utils.db'
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = get_db_connection(db_file)
    print(f"\nInitializing appointment schema in {db_file}...")
    initialize_appointment_schema(conn)

    try:
        print("\n--- Testing Appointment DB Utils ---")
        cursor = conn.cursor()

        # 1. Create Test Users (Providers & Patients)
        provider1_id, provider2_id, patient1_id, patient2_id = None, None, None, None
        users_to_create = {
            'prov_alice': None, 'prov_bob': None,
            'pat_charlie': None, 'pat_dave': None
        }
        print("Creating users with email/phone...")
        users_data = {
            'prov_alice': ("alice@provider.com", "111-222-3333"),
            'prov_bob': ("bob@provider.com", "111-222-4444"),
            'pat_charlie': ("charlie@patient.com", "555-123-4567"),
            'pat_dave': ("dave@patient.com", "555-987-6543")
        }
        for username, details in users_data.items():
            email, phone = details
            try:
                cursor.execute("INSERT INTO users (username, email, phone) VALUES (?, ?, ?)", (username, email, phone))
                users_to_create[username] = cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                users_to_create[username] = cursor.fetchone()['user_id']
                # Optionally update email/phone if they differ, for testing consistency
                cursor.execute("UPDATE users SET email = ?, phone = ? WHERE user_id = ?",
                               (email, phone, users_to_create[username]))

        conn.commit()
        provider1_id = users_to_create['prov_alice']
        provider2_id = users_to_create['prov_bob']
        patient1_id = users_to_create['pat_charlie']
        patient2_id = users_to_create['pat_dave']
        print(f"Provider Alice ID: {provider1_id}, Bob ID: {provider2_id}")
        print(f"Patient Charlie ID: {patient1_id}, Dave ID: {patient2_id}")
        assert all([provider1_id, provider2_id, patient1_id, patient2_id])

        # 2. Add Provider Availability (simplified)
        print("\nAdding availability...")
        avail1_p1 = add_provider_availability(conn, provider1_id, "2024-05-01 09:00:00", "2024-05-01 12:00:00")
        print(f"Alice's availability ID: {avail1_p1}")

        # 3. Request Appointments
        print("\nRequesting appointments...")
        appt1_req_id = request_appointment(conn, patient1_id, provider1_id,
                                           "2024-05-01 09:00:00", "2024-05-01 09:30:00",
                                           "Annual Checkup", "Feeling generally well.")
        print(f"Appointment request 1 ID: {appt1_req_id} (P1 with Dr.Alice)")
        assert appt1_req_id is not None

        appt2_req_id = request_appointment(conn, patient2_id, provider1_id,
                                           "2024-05-01 10:00:00", "2024-05-01 10:30:00",
                                           "Follow-up", "Regarding previous results.")
        print(f"Appointment request 2 ID: {appt2_req_id} (P2 with Dr.Alice)")
        assert appt2_req_id is not None

        # Test CHECK constraint for appointment times
        try:
            request_appointment(conn, patient1_id, provider1_id, "2024-05-01 11:00:00", "2024-05-01 10:00:00")
            print("ERROR: Appt request with end < start succeeded, CHECK constraint failed.")
        except sqlite3.IntegrityError:
            print("Successfully caught IntegrityError for invalid appointment time range.")


        # 4. Get Appointment by ID
        print(f"\nGetting appointment ID {appt1_req_id} details...")
        appt1_details = get_appointment_by_id(conn, appt1_req_id)
        print(f"  Details: {dict(appt1_details) if appt1_details else 'Not Found'}")
        assert appt1_details and appt1_details['appointment_id'] == appt1_req_id
        assert appt1_details['patient_username'] == 'pat_charlie'
        assert appt1_details['provider_username'] == 'prov_alice'
        assert appt1_details['status'] == 'pending_provider_confirmation'

        # 5. Update Appointment Status
        print("\nUpdating appointment statuses...")
        # Provider Alice confirms appt1
        confirmed_appt1 = update_appointment_status(conn, appt1_req_id, 'confirmed',
                                                  provider1_id, 'provider', "Confirmed by Dr. Alice.")
        print(f"Confirmation of Appt1 by Dr.Alice: Success = {confirmed_appt1}")
        assert confirmed_appt1
        appt1_confirmed_details = get_appointment_by_id(conn, appt1_req_id)
        print(f"  Appt1 new status: {appt1_confirmed_details['status']}, Video Room: {appt1_confirmed_details['video_room_name']}")
        assert appt1_confirmed_details['status'] == 'confirmed'
        assert appt1_confirmed_details['video_room_name'] is not None

        # Mark reminder sent for Appt1 (simulating it was sent long ago)
        long_ago_ts = (datetime.now() - datetime.timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
        mark_reminder_sent(conn, appt1_req_id, long_ago_ts)
        print(f"\nAppt1 (ID: {appt1_req_id}) marked with old reminder: {long_ago_ts}")

        # Provider Alice also confirms appt2
        confirmed_appt2 = update_appointment_status(conn, appt2_req_id, 'confirmed',
                                                    provider1_id, 'provider', "Also confirmed by Dr. Alice.")
        print(f"Confirmation of Appt2 by Dr.Alice: Success = {confirmed_appt2}")
        assert confirmed_appt2
        # Appt2 will have last_reminder_sent_at = NULL initially

        # 7. Test get_appointments_needing_reminders
        print("\nTesting get_appointments_needing_reminders...")
        # Window for next 24 hours, grace period 1 hour.
        # Appt1: confirmed, start_time is 2024-05-01 09:00:00, reminder sent 48hrs ago -> should be included
        # Appt2: confirmed, start_time is 2024-05-01 10:00:00, reminder NULL -> should be included

        # To make this test robust, we need to set appointment_start_time relative to now for the test
        # Let's create new appointments for this specific test.

        # Appointment in 23.5 hours, not reminded
        appt3_start = (datetime.now() + datetime.timedelta(hours=23.5)).strftime('%Y-%m-%d %H:%M:%S')
        appt3_end = (datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        appt3_id = request_appointment(conn, patient1_id, provider1_id, appt3_start, appt3_end, "Reminder Test 1")
        update_appointment_status(conn, appt3_id, 'confirmed', provider1_id, 'provider')
        print(f"Created Confirmed Appt3 (ID: {appt3_id}) at {appt3_start} - needs reminder.")

        # Appointment in 22 hours, already reminded 30 mins ago (within grace period if grace=1hr)
        appt4_start = (datetime.now() + datetime.timedelta(hours=22)).strftime('%Y-%m-%d %H:%M:%S')
        appt4_end = (datetime.now() + datetime.timedelta(hours=22.5)).strftime('%Y-%m-%d %H:%M:%S')
        appt4_id = request_appointment(conn, patient2_id, provider1_id, appt4_start, appt4_end, "Reminder Test 2")
        update_appointment_status(conn, appt4_id, 'confirmed', provider1_id, 'provider')
        recent_reminder_ts = (datetime.now() - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        mark_reminder_sent(conn, appt4_id, recent_reminder_ts)
        print(f"Created Confirmed Appt4 (ID: {appt4_id}) at {appt4_start} - recently reminded at {recent_reminder_ts}.")

        # Appointment in 23 hours, status pending (should not be included)
        appt5_start = (datetime.now() + datetime.timedelta(hours=23)).strftime('%Y-%m-%d %H:%M:%S')
        appt5_end = (datetime.now() + datetime.timedelta(hours=23.5)).strftime('%Y-%m-%d %H:%M:%S')
        appt5_id = request_appointment(conn, patient1_id, provider2_id, appt5_start, appt5_end, "Reminder Test 3 Pending")
        print(f"Created Pending Appt5 (ID: {appt5_id}) at {appt5_start} - should not be reminded.")


        # Define reminder window: e.g., appointments starting in the next 20 to 24 hours
        window_start = (datetime.now() + datetime.timedelta(hours=20)).strftime('%Y-%m-%d %H:%M:%S')
        window_end = (datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        reminders_needed = get_appointments_needing_reminders(conn, window_start, window_end, reminder_grace_period_hours=1)
        print(f"Appointments needing reminders (window {window_start} to {window_end}, grace 1hr):")
        found_appt3 = False
        for appt_rem in reminders_needed:
            print(f"  Appt ID: {appt_rem['appointment_id']}, Start: {appt_rem['appointment_start_time']}, Last Reminder: {appt_rem['last_reminder_sent_at']}")
            if appt_rem['appointment_id'] == appt3_id:
                found_appt3 = True
            assert appt_rem['appointment_id'] != appt4_id, "Appt4 should not be in list (reminded recently)"
            assert appt_rem['appointment_id'] != appt5_id, "Appt5 should not be in list (not confirmed)"

        assert found_appt3, f"Appt3 (ID: {appt3_id}) should be in the reminder list."
        # The exact number depends on how many old appointments fall into this window now.
        # For this test, we focus on appt3 being present and appt4/appt5 being absent.
        print(f"Found {len(reminders_needed)} appointments needing reminders matching criteria.")


        print("\nAll appointment DB util tests passed successfully (basic assertions).")
        charlie_confirms_appt2 = update_appointment_status(conn, appt2_req_id, 'confirmed',
                                                           patient1_id, 'patient')
        print(f"Patient Charlie confirming Appt2: Success = {charlie_confirms_appt2}")
        assert not charlie_confirms_appt2

        # Patient Dave cancels appt2
        cancelled_appt2 = update_appointment_status(conn, appt2_req_id, 'cancelled_by_patient',
                                                    patient2_id, 'patient', "No longer needed.")
        print(f"Cancellation of Appt2 by Patient Dave: Success = {cancelled_appt2}")
        assert cancelled_appt2
        appt2_cancelled_details = get_appointment_by_id(conn, appt2_req_id)
        print(f"  Appt2 new status: {appt2_cancelled_details['status']}")
        assert appt2_cancelled_details['status'] == 'cancelled_by_patient'
        assert "No longer needed." in appt2_cancelled_details['notes_by_patient']

        # Provider Bob (not related to appt1) tries to cancel appt1 (should fail)
        bob_cancels_appt1 = update_appointment_status(conn, appt1_req_id, 'cancelled_by_provider',
                                                      provider2_id, 'provider')
        print(f"Dr.Bob cancelling Appt1: Success = {bob_cancels_appt1}")
        assert not bob_cancels_appt1


        # 6. Get Appointments for User
        print(f"\nGetting appointments for Patient Charlie (ID: {patient1_id})...")
        charlie_appts = get_appointments_for_user(conn, patient1_id, 'patient')
        print(f"  Charlie has {len(charlie_appts)} appointments.")
        for appt in charlie_appts: print(f"    {dict(appt)}")
        assert len(charlie_appts) == 1 and charlie_appts[0]['appointment_id'] == appt1_req_id

        print(f"\nGetting appointments for Provider Alice (ID: {provider1_id})...")
        alice_appts = get_appointments_for_user(conn, provider1_id, 'provider')
        print(f"  Dr.Alice has {len(alice_appts)} appointments.")
        for appt in alice_appts: print(f"    {dict(appt)}")
        assert len(alice_appts) == 2 # appt1 (confirmed) and appt2 (cancelled_by_patient)

        print(f"\nGetting 'confirmed' appointments for Provider Alice...")
        alice_confirmed_appts = get_appointments_for_user(conn, provider1_id, 'provider', status_filter='confirmed')
        print(f"  Dr.Alice has {len(alice_confirmed_appts)} confirmed appointments.")
        assert len(alice_confirmed_appts) == 1 and alice_confirmed_appts[0]['appointment_id'] == appt1_req_id

        print(f"\nGetting appointments for Dr.Alice on 2024-05-01...")
        alice_may1_appts = get_appointments_for_user(conn, provider1_id, 'provider', start_date_filter="2024-05-01", end_date_filter="2024-05-01")
        print(f"  Dr.Alice has {len(alice_may1_appts)} appointments on 2024-05-01.")
        assert len(alice_may1_appts) == 2

        print("\nAll appointment DB util tests passed successfully (basic assertions).")

    except ValueError as ve:
        print(f"ValueError in example usage: {ve}")
    except sqlite3.Error as e:
        print(f"An SQLite error occurred in example usage: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred in example usage: {ex}")
    finally:
        if conn:
            conn.close()
            print(f"\nClosed connection to {db_file}.")
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed test database {db_file}.")