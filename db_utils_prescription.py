import sqlite3
from datetime import datetime, date # For type hinting and default date values
import json # Not strictly needed if details are TEXT, but good for conceptual JSON

# --- Database Schema (SQLite Compatible) ---
PRESCRIPTION_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT NULLABLE,
    phone TEXT NULLABLE,
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    appointment_start_time DATETIME NOT NULL,
    -- Add other essential appointment fields if needed for context, keeping it minimal for FK
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NULLABLE,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    issue_date DATE NOT NULL DEFAULT (STRFTIME('%Y-%m-%d', 'now')), -- SQLite CURRENT_DATE
    notes_for_patient TEXT NULLABLE,
    notes_for_pharmacist TEXT NULLABLE,
    status TEXT NOT NULL DEFAULT 'active', -- VARCHAR(50) becomes TEXT
    pharmacy_details TEXT NULLABLE,
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    updated_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_presc_patient_id ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_presc_provider_id ON prescriptions(provider_id);
CREATE INDEX IF NOT EXISTS idx_presc_appointment_id ON prescriptions(appointment_id);
CREATE INDEX IF NOT EXISTS idx_presc_issue_date ON prescriptions(issue_date);
CREATE INDEX IF NOT EXISTS idx_presc_status ON prescriptions(status);

CREATE TABLE IF NOT EXISTS prescription_medications (
    prescription_medication_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    medication_name TEXT NOT NULL, -- VARCHAR(255) becomes TEXT
    dosage TEXT NOT NULL,          -- VARCHAR(100) becomes TEXT
    frequency TEXT NOT NULL,       -- VARCHAR(100) becomes TEXT
    duration TEXT NULLABLE,        -- VARCHAR(100) becomes TEXT
    quantity TEXT NOT NULL,        -- VARCHAR(100) becomes TEXT
    refills_available INTEGER NOT NULL DEFAULT 0,
    instructions TEXT NULLABLE,
    is_prn INTEGER DEFAULT 0 NOT NULL, -- BOOLEAN becomes INTEGER (0 for False, 1 for True)
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_presc_med_prescription_id ON prescription_medications(prescription_id);
CREATE INDEX IF NOT EXISTS idx_presc_med_medication_name ON prescription_medications(medication_name);

-- Trigger for prescriptions.updated_at
CREATE TRIGGER IF NOT EXISTS update_prescriptions_updated_at
AFTER UPDATE ON prescriptions
FOR EACH ROW
BEGIN
    UPDATE prescriptions SET updated_at = (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
    WHERE prescription_id = OLD.prescription_id;
END;
"""

# --- Database Utility Functions ---

def get_db_connection(db_name='prescription_app.db') -> sqlite3.Connection:
    """
    Establishes and returns an SQLite3 connection object.

    The connection is configured to:
    - Use `sqlite3.Row` as the row_factory for accessing columns by name.
    - Enable foreign key constraint enforcement (`PRAGMA foreign_keys = ON`).

    Args:
        db_name (str): The name of the SQLite database file.
                       Defaults to 'prescription_app.db'.

    Returns:
        sqlite3.Connection: The SQLite3 connection object.

    Raises:
        sqlite3.Error: If any error occurs during database connection.
    """
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error to '{db_name}': {e}")
        raise

def initialize_prescription_schema(conn: sqlite3.Connection):
    """
    Initializes the prescription-related database schema.

    Executes the SQL statements defined in `PRESCRIPTION_SCHEMA` to create
    `users`, a minimal `appointments` table (for FKs), `prescriptions`,
    and `prescription_medications` tables, along with their indexes and triggers,
    if they do not already exist. This is idempotent due to `IF NOT EXISTS`.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.

    Raises:
        sqlite3.Error: If any error occurs during schema execution.
                       Changes are rolled back on error.
    """
    try:
        cursor = conn.cursor()
        cursor.executescript(PRESCRIPTION_SCHEMA)
        conn.commit()
        print("Prescription database schema initialized successfully.")
    except sqlite3.Error as e:
        print(f"Prescription schema initialization error: {e}")
        conn.rollback()
        raise

def create_prescription(conn: sqlite3.Connection, patient_id: int, provider_id: int,
                        issue_date: str, medications_list: list[dict],
                        appointment_id: int = None, notes_for_patient: str = None,
                        notes_for_pharmacist: str = None, pharmacy_details: str = None,
                        status: str = 'active') -> int:
    """
    Creates a new prescription and its associated medications within a database transaction.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection.
        patient_id (int): ID of the patient.
        provider_id (int): ID of the prescribing provider.
        issue_date (str): Date of issue in 'YYYY-MM-DD' format.
        medications_list (list[dict]): A list of dictionaries, each representing a medication.
                                      Required keys per medication: 'medication_name', 'dosage',
                                      'frequency', 'quantity'.
                                      Optional: 'duration', 'refills_available',
                                      'instructions', 'is_prn'.
        appointment_id (int, optional): ID of the appointment related to this prescription.
        notes_for_patient (str, optional): Optional notes for the patient.
        notes_for_pharmacist (str, optional): Optional notes for the pharmacist.
        pharmacy_details (str, optional): Optional details of the designated pharmacy.
        status (str, optional): Status of the prescription, defaults to 'active'.

    Returns:
        int: The `prescription_id` of the newly created prescription.

    Raises:
        ValueError: For invalid input types (e.g., non-integer IDs, malformed date,
                    empty medications_list, or missing required medication fields).
        sqlite3.IntegrityError: If foreign key constraints fail (e.g., patient_id or
                                provider_id do not exist) or other integrity issues.
        sqlite3.Error: For other database operational errors.
                       The entire transaction is rolled back if any part fails.
    """
    # Validate input types
    if not all(isinstance(id_val, int) for id_val in [patient_id, provider_id]):
        raise ValueError("patient_id and provider_id must be integers.")
    if appointment_id is not None and not isinstance(appointment_id, int):
        raise ValueError("appointment_id must be an integer if provided.")
    if not isinstance(issue_date, str):
        raise ValueError("issue_date must be a string.")
    try: # Validate date format
        datetime.strptime(issue_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("issue_date must be in YYYY-MM-DD format.")
    if not isinstance(medications_list, list) or not medications_list: # Must be a non-empty list
        raise ValueError("medications_list must be a non-empty list of medication dictionaries.")

    cursor = conn.cursor()
    try:
        # Explicitly start a transaction.
        # While sqlite3 connection objects operate in "autocommit" mode by default (meaning
        # DML statements outside an explicit transaction are committed immediately),
        # for multi-statement operations that must succeed or fail together,
        # explicit transaction control is best practice.
        cursor.execute("BEGIN")

        # Insert into prescriptions table
        cursor.execute(
            """
            INSERT INTO prescriptions (appointment_id, patient_id, provider_id, issue_date,
                                     notes_for_patient, notes_for_pharmacist, status, pharmacy_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (appointment_id, patient_id, provider_id, issue_date, notes_for_patient,
             notes_for_pharmacist, status, pharmacy_details)
        )
        new_prescription_id = cursor.lastrowid
        if new_prescription_id is None: # Should not happen with AUTOINCREMENT if insert was successful
            raise sqlite3.Error("Failed to retrieve lastrowid for new prescription after insert.")

        # Insert into prescription_medications table
        required_med_fields = ['medication_name', 'dosage', 'frequency', 'quantity']
        for med_item in medications_list:
            # Validate each medication item
            for field in required_med_fields:
                if field not in med_item or not med_item[field]: # Also check for empty values
                    raise ValueError(f"Medication item missing required or has empty field: '{field}'. Medication: {med_item}")

            cursor.execute(
                """
                INSERT INTO prescription_medications
                    (prescription_id, medication_name, dosage, frequency, duration,
                     quantity, refills_available, instructions, is_prn)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (new_prescription_id, med_item['medication_name'], med_item['dosage'], med_item['frequency'],
                 med_item.get('duration'), med_item['quantity'],
                 int(med_item.get('refills_available', 0)), # Ensure integer
                 med_item.get('instructions'),
                 1 if med_item.get('is_prn', False) else 0) # Convert boolean to 0/1 for SQLite
            )

        conn.commit() # Commit transaction only if all operations succeed
        return new_prescription_id

    except (ValueError, sqlite3.Error) as e:
        print(f"Error in create_prescription: {e}. Rolling back transaction.")
        conn.rollback() # Rollback transaction on any error (ValueError or sqlite3.Error)
        raise # Re-raise the caught exception to inform the caller

def get_prescription_by_id(conn: sqlite3.Connection, prescription_id: int) -> dict | None:
    """
    Fetches a specific prescription by its ID, including its medications and user details.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection.
        prescription_id (int): The ID of the prescription to fetch.

    Returns:
        dict | None: A dictionary representing the prescription with a nested list
                      of its medications, and patient/provider usernames.
                      Returns `None` if the prescription is not found.

    Raises:
        ValueError: If `prescription_id` is not an integer.
        sqlite3.Error: For database operational errors during the query.
    """
    if not isinstance(prescription_id, int):
        raise ValueError("prescription_id must be an integer.")

    cursor = conn.cursor()
    prescription_data = None

    # Step 1: Fetch main prescription details and join with users for names
    main_query = """
    SELECT
        pr.*,  -- Select all columns from prescriptions table
        pt.username AS patient_username,
        pv.username AS provider_username
    FROM prescriptions pr
    JOIN users pt ON pr.patient_id = pt.user_id   -- Join for patient's username
    JOIN users pv ON pr.provider_id = pv.user_id -- Join for provider's username
    WHERE pr.prescription_id = ?;
    """
    try:
        cursor.execute(main_query, (prescription_id,))
        prescription_row = cursor.fetchone()

        if prescription_row:
            prescription_data = dict(prescription_row) # Convert sqlite3.Row to dict

            # Step 2: Fetch associated medications for this prescription_id
            medications_query = """
            SELECT * FROM prescription_medications
            WHERE prescription_id = ?
            ORDER BY prescription_medication_id ASC; -- Consistent ordering
            """
            cursor.execute(medications_query, (prescription_id,))
            medications_list = [dict(med_row) for med_row in cursor.fetchall()]

            # Store booleans correctly from DB (0/1) to Python bool
            for med in medications_list:
                med['is_prn'] = bool(med['is_prn'])

            prescription_data['medications'] = medications_list

        return prescription_data # Returns None if prescription_row was None

    except sqlite3.Error as e:
        print(f"Error in get_prescription_by_id for prescription {prescription_id}: {e}")
        raise # Re-raise to be handled by caller


if __name__ == '__main__':
    import os
    db_file = 'test_prescription_utils.db'
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = get_db_connection(db_file)
    print(f"\nInitializing prescription schema in {db_file}...")
    initialize_prescription_schema(conn)

    try:
        print("\n--- Testing Prescription DB Utils ---")
        cursor = conn.cursor()

        # 1. Create Test Users and a dummy Appointment for FK
        print("Creating test users and appointment...")
        users_data = {
            'doc_prescriber': ("prescriber@clinic.com", "777-111-0000"),
            'patient_rx': ("rxpatient@mail.com", "777-222-0000")
        }
        user_ids = {}
        for uname, details in users_data.items():
            email, phone = details
            cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?,?,?)", (uname, email, phone))
            user_ids[uname] = cursor.lastrowid if cursor.lastrowid != 0 else conn.execute("SELECT user_id FROM users WHERE username=?",(uname,)).fetchone()['user_id']
        conn.commit()

        provider_id = user_ids['doc_prescriber']
        patient_id = user_ids['patient_rx']
        print(f"Provider ID: {provider_id}, Patient ID: {patient_id}")

        cursor.execute("INSERT INTO appointments (patient_id, provider_id, appointment_start_time) VALUES (?, ?, ?)",
                       (patient_id, provider_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        appt_id = cursor.lastrowid
        conn.commit()
        print(f"Dummy Appointment ID: {appt_id}")

        # 2. Create a valid prescription
        print("\nCreating a valid prescription...")
        valid_medications = [
            {
                "medication_name": "Amoxicillin", "dosage": "250mg", "frequency": "TID",
                "duration": "7 days", "quantity": "21 tablets", "refills_available": 0,
                "instructions": "Take with food.", "is_prn": False
            },
            {
                "medication_name": "Ibuprofen", "dosage": "400mg", "frequency": "PRN pain",
                "duration": None, "quantity": "50 tablets", "refills_available": 2,
                "instructions": "Max 3 per day.", "is_prn": True
            }
        ]
        prescription_id_valid = create_prescription(
            conn, patient_id, provider_id, date.today().isoformat(), valid_medications,
            appointment_id=appt_id, notes_for_patient="Finish all antibiotics."
        )
        assert prescription_id_valid is not None, "Valid prescription creation failed."
        print(f"Successfully created prescription ID: {prescription_id_valid}")

        # 3. Fetch and verify the created prescription
        print(f"\nFetching prescription ID: {prescription_id_valid}...")
        fetched_prescription = get_prescription_by_id(conn, prescription_id_valid)
        assert fetched_prescription is not None, "Failed to fetch created prescription."
        assert fetched_prescription['prescription_id'] == prescription_id_valid
        assert fetched_prescription['patient_id'] == patient_id
        assert fetched_prescription['provider_id'] == provider_id
        assert fetched_prescription['patient_username'] == 'patient_rx'
        assert fetched_prescription['provider_username'] == 'doc_prescriber'
        assert len(fetched_prescription['medications']) == 2
        assert fetched_prescription['medications'][0]['medication_name'] == "Amoxicillin"
        assert fetched_prescription['medications'][1]['is_prn'] == 1 # SQLite stores boolean True as 1
        print("Fetched prescription details:")
        for key, value in fetched_prescription.items():
            if key != 'medications':
                print(f"  {key}: {value}")
            else:
                print("  Medications:")
                for med in value:
                    print(f"    {dict(med)}")

        # 4. Test transactionality: Attempt to create a prescription with an invalid medication item
        print("\nAttempting to create a prescription with an invalid medication (missing dosage)...")
        invalid_medications = [
            {"medication_name": "ValidMed", "dosage": "10mg", "frequency": "QD", "quantity": "30"},
            {"medication_name": "InvalidMed", "frequency": "BID", "quantity": "10"} # Missing dosage
        ]
        rolled_back_prescription_id = None
        try:
            rolled_back_prescription_id = create_prescription(
                conn, patient_id, provider_id, date.today().isoformat(), invalid_medications
            )
        except ValueError as ve:
            print(f"Caught expected ValueError: {ve}") # Expected due to missing field
        except sqlite3.Error as e: # Should also be caught by the function itself
            print(f"Caught expected sqlite3.Error: {e}")

        assert rolled_back_prescription_id is None, "Transaction should have rolled back, prescription ID should be None."

        # Verify that no new prescription was created due to rollback
        # (assuming prescription_id_valid was the last successful one)
        cursor.execute("SELECT MAX(prescription_id) FROM prescriptions")
        max_id_after_rollback_attempt = cursor.fetchone()[0]
        assert max_id_after_rollback_attempt == prescription_id_valid, \
            "A new prescription was created despite invalid medication data; transaction rollback failed."
        print("Transaction rollback test successful: No new prescription created with invalid medication.")

        print("\nAll prescription DB util tests passed successfully.")

    except Exception as e:
        print(f"Error during __main__ test run in {__file__}: {e}")
    finally:
        if conn: conn.close()
        if os.path.exists(db_file): os.remove(db_file)
        print(f"\nCleaned up test DB: {db_file}")


def get_prescriptions_for_user(conn: sqlite3.Connection, user_id: int, user_role: str,
                               start_date_filter: str = None, end_date_filter: str = None,
                               status_filter: str = None) -> list[dict]:
    """
    Fetches prescription summaries for a user based on their role (patient or provider).

    Allows optional filtering by `issue_date` range and `status`.
    Each summary includes key prescription information and patient/provider usernames.
    Medications are not included in this summary view; `get_prescription_by_id`
    should be used for full details including medications.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection.
        user_id (int): The ID of the user (patient or provider).
        user_role (str): Role of the user ('patient' or 'provider'). This determines
                         whether to query based on `patient_id` or `provider_id`.
        start_date_filter (str, optional): Start date for `issue_date` filtering ('YYYY-MM-DD').
        end_date_filter (str, optional): End date for `issue_date` filtering ('YYYY-MM-DD').
        status_filter (str, optional): Exact status to filter prescriptions by.

    Returns:
        list[dict]: A list of prescription summary dictionaries, ordered by `issue_date`
                    descending, then by `prescription_id` descending. Returns an empty
                    list if no matching prescriptions are found.

    Raises:
        ValueError: If `user_id` is not an integer, `user_role` is invalid, or if
                    date filter strings are provided in an invalid format.
        sqlite3.Error: For database operational errors during the query.
    """
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer.")
    if user_role not in ['patient', 'provider']:
        raise ValueError("user_role must be 'patient' or 'provider'.")

    prescriptions_list = []
    cursor = conn.cursor()

    params = {} # Using named parameters for better query readability

    # Base query selects key summary fields and joins for usernames
    query = """
    SELECT
        pr.prescription_id,
        pr.issue_date,
        pr.status,
        pt.username AS patient_username,
        pv.username AS provider_username,
        pr.appointment_id, -- Included as it's often useful context
        pr.notes_for_patient,
        pr.pharmacy_details
    FROM prescriptions pr
    JOIN users pt ON pr.patient_id = pt.user_id
    JOIN users pv ON pr.provider_id = pv.user_id
    WHERE
    """

    # Determine the primary filter based on user_role
    if user_role == 'patient':
        query += "pr.patient_id = :user_id"
    else: # user_role == 'provider'
        query += "pr.provider_id = :user_id"
    params['user_id'] = user_id

    # Add optional filters
    if start_date_filter:
        # Ensure date strings are valid before using in query
        try: datetime.strptime(start_date_filter, '%Y-%m-%d')
        except ValueError: raise ValueError("Invalid start_date_filter format. Use YYYY-MM-DD.")
        query += " AND DATE(pr.issue_date) >= DATE(:start_date_filter)"
        params['start_date_filter'] = start_date_filter

    if end_date_filter:
        try: datetime.strptime(end_date_filter, '%Y-%m-%d')
        except ValueError: raise ValueError("Invalid end_date_filter format. Use YYYY-MM-DD.")
        query += " AND DATE(pr.issue_date) <= DATE(:end_date_filter)"
        params['end_date_filter'] = end_date_filter

    if status_filter:
        query += " AND pr.status = :status_filter"
        params['status_filter'] = status_filter

    # Order results: most recent issue date first, then by ID for consistent tie-breaking
    query += " ORDER BY pr.issue_date DESC, pr.prescription_id DESC;"

    try:
        cursor.execute(query, params)
        for row in cursor.fetchall():
            prescriptions_list.append(dict(row))
        return prescriptions_list
    except sqlite3.Error as e:
        print(f"Error in get_prescriptions_for_user (user {user_id}, role {user_role}): {e}")
        raise

def update_prescription_status(conn: sqlite3.Connection, prescription_id: int, new_status: str,
                               current_provider_id: int, notes: str = None) -> bool:
    """
    Updates the status of a given prescription.

    Authorization is performed to ensure only the issuing provider can modify its status.
    Notes, if provided, are appended to the 'notes_for_pharmacist' field, prefixed with
    context about the update. The 'updated_at' field is handled by a database trigger.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection.
        prescription_id (int): The ID of the prescription to update.
        new_status (str): The new status to set (e.g., 'cancelled', 'superseded', 'expired').
        current_provider_id (int): The ID of the provider attempting the update. This is used
                                   for authorization to ensure they are the issuing provider.
        notes (str, optional): Optional notes regarding the status change (e.g., reason
                               for cancellation). These are appended to existing pharmacist notes.

    Returns:
        bool: `True` if the update was successful (one row affected and authorized),
              `False` otherwise (e.g., prescription not found, authorization failed).

    Raises:
        ValueError: For invalid input types (e.g., IDs not int, empty new_status).
        sqlite3.Error: For database errors during fetch or update operations.
    """
    if not isinstance(prescription_id, int) or not isinstance(current_provider_id, int):
        raise ValueError("prescription_id and current_provider_id must be integers.")
    if not isinstance(new_status, str) or not new_status.strip():
        raise ValueError("new_status must be a non-empty string.")

    cursor = conn.cursor()
    try:
        # Step 1: Fetch the prescription to verify ownership by the current_provider_id
        cursor.execute("SELECT provider_id, notes_for_pharmacist FROM prescriptions WHERE prescription_id = ?",
                       (prescription_id,))
        prescription = cursor.fetchone()

        if not prescription:
            print(f"Update failed: Prescription ID {prescription_id} not found.")
            return False # Prescription does not exist

        if prescription['provider_id'] != current_provider_id:
            # Authorization check: Only the original provider can change the status.
            print(f"Authorization failed: Provider {current_provider_id} cannot update "
                  f"prescription {prescription_id} owned by provider {prescription['provider_id']}.")
            return False # Current provider is not the issuing provider

        # Step 2: Prepare fields for update
        fields_to_update = {"status": new_status}
        current_pharmacist_notes = prescription['notes_for_pharmacist'] if prescription['notes_for_pharmacist'] else ""

        if notes and notes.strip(): # Add notes only if provided and not just whitespace
            # Append new notes with context (who, when, what status change, and the note itself)
            note_prefix = f"[{new_status.upper()} by Provider {current_provider_id} on {date.today().isoformat()}]:"
            updated_pharmacist_notes = f"{current_pharmacist_notes}\n{note_prefix} {notes}".strip()
            fields_to_update["notes_for_pharmacist"] = updated_pharmacist_notes

        # Build the SET part of the SQL query dynamically using named placeholders
        set_clauses = [f"{field} = :{field}" for field in fields_to_update.keys()]

        params_for_update = fields_to_update.copy() # Use a copy for params
        params_for_update['prescription_id'] = prescription_id # For the WHERE clause

        # The 'updated_at' field is automatically handled by the database trigger upon UPDATE.
        update_query = f"UPDATE prescriptions SET {', '.join(set_clauses)} WHERE prescription_id = :prescription_id"

        cursor.execute(update_query, params_for_update)
        conn.commit()

        return cursor.rowcount > 0 # True if exactly one row was affected

    except sqlite3.Error as e:
        print(f"Error in update_prescription_status for prescription {prescription_id}: {e}")
        conn.rollback() # Rollback on any error during the transaction
        raise


if __name__ == '__main__':
    import os
    db_file = 'test_prescription_utils_refined.db'
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = get_db_connection(db_file)
    print(f"\nInitializing prescription schema in {db_file}...")
    initialize_prescription_schema(conn)
    try:
        print("\n--- Testing Prescription DB Utils (Refined with All Functions) ---")
        cursor = conn.cursor()
        user_ids_map = {}
        users_data = {
            'doc_prescriber': ("prescriber@clinic.com", "777-111-0000"),
            'doc_other': ("otherdoc@clinic.com", "777-111-0011"),
            'patient_rx': ("rxpatient@mail.com", "777-222-0000"),
            'patient_rx2': ("rxpatient2@mail.com", "777-222-0011")
        }
        print("Creating users with email/phone...")
        for username, details in users_data.items():
            email, phone = details
            # Using INSERT OR IGNORE for idempotency
            cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?, ?, ?)", (username, email, phone))
            if cursor.lastrowid == 0: # User might have existed if OR IGNORE was used
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                user_id_val = cursor.fetchone()['user_id']
                user_ids_map[username] = user_id_val
                # Ensure email/phone are updated if user existed (for test consistency)
                cursor.execute("UPDATE users SET email = ?, phone = ? WHERE user_id = ?", (email, phone, user_id_val))
            else:
                user_ids_map[username] = cursor.lastrowid
        conn.commit()

        provider_id = user_ids_map['doc_prescriber']
        other_provider_id = user_ids_map['doc_other']
        patient_id = user_ids_map['patient_rx']
        patient2_id = user_ids_map['patient_rx2']
        print(f"Provider IDs: Prescriber={provider_id}, Other={other_provider_id}. Patient IDs: Rx={patient_id}, Rx2={patient2_id}")

        # Create a dummy Appointment for FK
        cursor.execute("INSERT INTO appointments (patient_id, provider_id, appointment_start_time) VALUES (?, ?, ?)",
                       (patient_id, provider_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        appt_id = cursor.lastrowid
        conn.commit()
        print(f"Dummy Appointment ID: {appt_id}")

        print("\nCreating prescriptions...")
        meds1 = [{"medication_name": "Lisinopril 10mg", "dosage": "1 tab", "frequency": "Once daily", "quantity": "30"}]
        meds2 = [{"medication_name": "Metformin 500mg", "dosage": "1 tab", "frequency": "Twice daily", "quantity": "60"}]
        meds3 = [{"medication_name": "Atorvastatin 20mg", "dosage": "1 tab", "frequency": "Once daily", "quantity": "30"}]

        rx1_id = create_prescription(conn, patient_id, provider_id, "2024-01-15", meds1, appt_id, "For BP")
        rx2_id = create_prescription(conn, patient_id, provider_id, "2024-01-20", meds2, appt_id, "For Diabetes", status="active")
        rx3_id = create_prescription(conn, patient2_id, provider_id, "2024-02-01", meds3, status="expired")
        print(f"Created prescriptions: RX1_ID={rx1_id}, RX2_ID={rx2_id}, RX3_ID(Patient2)={rx3_id}")
        assert all([rx1_id, rx2_id, rx3_id])

        print("\nTesting get_prescriptions_for_user...")
        # For patient1
        rx_list_p1 = get_prescriptions_for_user(conn, patient_id, 'patient')
        print(f"Patient {patient_id} has {len(rx_list_p1)} prescriptions.")
        assert len(rx_list_p1) == 2
        assert rx_list_p1[0]['prescription_id'] == rx2_id # Ordered by issue_date DESC
        assert rx_list_p1[1]['prescription_id'] == rx1_id
        assert rx_list_p1[0]['patient_username'] == 'patient_rx'
        assert 'medications' not in rx_list_p1[0] # Should be summary

        # For provider1
        rx_list_prov1 = get_prescriptions_for_user(conn, provider_id, 'provider')
        print(f"Provider {provider_id} has {len(rx_list_prov1)} prescriptions.")
        assert len(rx_list_prov1) == 3
        assert rx_list_prov1[0]['prescription_id'] == rx3_id # Ordered by issue_date DESC

        # Test filters for provider1
        rx_list_prov1_active = get_prescriptions_for_user(conn, provider_id, 'provider', status_filter='active')
        print(f"Provider {provider_id} has {len(rx_list_prov1_active)} active prescriptions.")
        assert len(rx_list_prov1_active) == 2 # rx1 and rx2 are active (default)

        rx_list_prov1_jan = get_prescriptions_for_user(conn, provider_id, 'provider', start_date_filter="2024-01-01", end_date_filter="2024-01-31")
        print(f"Provider {provider_id} has {len(rx_list_prov1_jan)} prescriptions in Jan 2024.")
        assert len(rx_list_prov1_jan) == 2

        print("\nTesting update_prescription_status...")
        # Provider1 cancels rx1
        cancel_notes = "Patient reported allergy."
        update_success = update_prescription_status(conn, rx1_id, "cancelled", provider_id, cancel_notes)
        assert update_success, "Failed to update rx1 status by owner provider."
        rx1_details_cancelled = get_prescription_by_id(conn, rx1_id)
        assert rx1_details_cancelled['status'] == 'cancelled'
        assert cancel_notes in rx1_details_cancelled['notes_for_pharmacist']
        print(f"RX1 cancelled successfully. Status: {rx1_details_cancelled['status']}, Notes: '{rx1_details_cancelled['notes_for_pharmacist']}'")

        # Other_provider tries to cancel rx2 (should fail)
        update_fail_auth = update_prescription_status(conn, rx2_id, "cancelled", other_provider_id, "Attempt by wrong provider.")
        assert not update_fail_auth, "Should not allow other provider to update status."
        rx2_details_active = get_prescription_by_id(conn, rx2_id)
        assert rx2_details_active['status'] == 'active', "RX2 status should remain active."
        print(f"RX2 status update by wrong provider correctly prevented. Status: {rx2_details_active['status']}")

        # Test update for non-existent prescription
        update_fail_notfound = update_prescription_status(conn, 9999, "cancelled", provider_id)
        assert not update_fail_notfound, "Update should fail for non-existent prescription."
        print("Update for non-existent prescription correctly failed.")

        print("\nAll DB utils tested in __main__ (including new prescription functions).")

    except Exception as e:
        print(f"Error during __main__ test run in {__file__}: {e}")
    finally:
        if conn: conn.close()
        if os.path.exists(db_file): os.remove(db_file)
        print(f"Cleaned up test DB: {db_file}")