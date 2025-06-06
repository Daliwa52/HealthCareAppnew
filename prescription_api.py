from flask import Flask, request, jsonify
from datetime import date, datetime # For handling dates and validating datetime strings
import sqlite3
import os

from db_utils_prescription import (
    get_db_connection,
    initialize_prescription_schema,
    create_prescription as db_create_prescription,
    get_prescription_by_id as db_get_prescription_by_id,
    get_prescriptions_for_user as db_get_prescriptions_for_user,
    update_prescription_status as db_update_prescription_status
)

app = Flask(__name__)
# Configure DB_NAME using an environment variable with a default
DB_NAME = os.getenv('PRESCRIPTION_DB_NAME', 'prescription_app.db')

# --- Helper ---
def _validate_date_string(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """
    Validates if a string matches the specified date format.

    Args:
        date_str (str): The string to validate.
        format_str (str): The expected date format.

    Returns:
        bool: True if the string matches the format, False otherwise.
    """
    if not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

# --- Prescription API Endpoints ---

@app.route('/api/prescriptions', methods=['POST'])
def create_prescription_api():
    """
    Provider: Create a new prescription with its associated medications.

    This endpoint allows an authenticated provider (simulated by `provider_id` in
    the payload) to issue a new prescription for a patient. The prescription
    includes one or more medication items. The operation is transactional: if any
    part fails (e.g., invalid medication data), the entire prescription is rolled back.

    Request Body JSON Example:
    {
        "patient_id": 101,
        "provider_id": 1,
        "issue_date": "2024-07-29",
        "medications": [
            {
                "medication_name": "Amoxicillin 250mg",
                "dosage": "1 tablet",
                "frequency": "Every 8 hours",
                "quantity": "21 tablets",
                "duration": "7 days",
                "refills_available": 0,
                "instructions": "Take with food.",
                "is_prn": false
            },
            {
                "medication_name": "Ibuprofen 200mg",
                "dosage": "1-2 tablets",
                "frequency": "Every 4-6 hours as needed for pain",
                "quantity": "30 tablets",
                "is_prn": true
            }
        ],
        "appointment_id": 501,
        "notes_for_patient": "Finish all antibiotics. Take ibuprofen only if needed.",
        "notes_for_pharmacist": "Check for penicillin allergy.",
        "pharmacy_details": "Central Pharmacy, 123 Main St.",
        "status": "active"
    }

    Responses:
    - 201 Created: Prescription created successfully.
      JSON: {
          "status": "success",
          "message": "Prescription created successfully.",
          "prescription_id": int
      }
    - 400 Bad Request: Invalid JSON payload, missing required fields (e.g., `patient_id`,
                       `provider_id`, `medications_list`, or essential fields within a
                       medication item), malformed `issue_date`, or if a referenced
                       patient/provider/appointment ID does not exist (IntegrityError).
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error or other unexpected server issues.
      JSON: { "status": "error", "message": "A database error occurred..." }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

    # API-level validation for presence of essential top-level fields
    patient_id = data.get('patient_id')
    provider_id = data.get('provider_id') # In a real app, this would come from auth context
    issue_date_str = data.get('issue_date', date.today().isoformat()) # Default if not provided
    medications_list = data.get('medications')

    if not all(val is not None for val in [patient_id, provider_id, medications_list]): # Check for None, not just falsy
        return jsonify({"status": "error", "message": "Missing required fields: patient_id, provider_id, and medications list are required."}), 400
    if not isinstance(patient_id, int) or not isinstance(provider_id, int):
         return jsonify({"status": "error", "message": "patient_id and provider_id must be integers."}), 400
    if not _validate_date_string(issue_date_str): # Validates format
        return jsonify({"status": "error", "message": "Invalid issue_date format. Use YYYY-MM-DD."}), 400
    if not isinstance(medications_list, list) or not medications_list: # Must be a non-empty list
        return jsonify({"status": "error", "message": "medications_list must be a non-empty list of medication objects."}), 400
    for i, med_item in enumerate(medications_list): # Basic check that items are dicts
        if not isinstance(med_item, dict):
            return jsonify({"status": "error", "message": f"Item at index {i} in medications_list is not a valid medication object."}), 400

    # Optional fields from payload
    appointment_id = data.get('appointment_id')
    notes_for_patient = data.get('notes_for_patient')
    notes_for_pharmacist = data.get('notes_for_pharmacist')
    pharmacy_details = data.get('pharmacy_details')
    status = data.get('status', 'active') # Default handled by db_util if not passed

    # Auth Placeholder: In a real application, the `provider_id` would be derived from the
    # authenticated user's session or token, not taken from the payload for this action.
    # Further authorization checks might include verifying if the provider is active,
    # allowed to prescribe, and if the patient is under their care.

    with get_db_connection(DB_NAME) as conn:
        try:
            # The db_create_prescription function handles detailed validation of medication items
            # and transactional integrity.
            new_prescription_id = db_create_prescription(
                conn, patient_id, provider_id, issue_date_str, medications_list,
                appointment_id, notes_for_patient, notes_for_pharmacist,
                pharmacy_details, status
            )
            return jsonify({
                "status": "success",
                "message": "Prescription created successfully.",
                "prescription_id": new_prescription_id
            }), 201
        except ValueError as ve: # Raised by db_create_prescription for invalid data
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.IntegrityError as ie:
            print(f"Database IntegrityError in create_prescription_api: {ie}")
            # Provide a more user-friendly message for common FK violations
            if "FOREIGN KEY constraint failed" in str(ie):
                return jsonify({"status": "error", "message": "Invalid patient_id, provider_id, or appointment_id provided (referenced user or appointment does not exist)."}), 400
            return jsonify({"status": "error", "message": f"Database integrity error: {str(ie)}"}), 400
        except sqlite3.Error as e: # Other database errors
            print(f"Database error in create_prescription_api: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while creating the prescription."}), 500
        except Exception as e_gen: # Catch-all for any other unexpected errors
            print(f"Unexpected error in create_prescription_api: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/prescriptions/<int:prescription_id>', methods=['GET'])
def get_prescription_details_api(prescription_id: int):
    """
    User (Patient/Provider): Get specific prescription details.

    Retrieves the full details for a single prescription, including all associated
    medication items and the usernames of the patient and provider.
    Authorization is simulated: requires a `user_id` query parameter, and this user
    must be either the patient or the provider associated with the prescription.

    Path Parameters:
        prescription_id (int): The unique ID of the prescription to retrieve.

    Query Parameters (for simulated auth):
        user_id (int): Required. The ID of the user making the request.

    Responses:
    - 200 OK: Prescription details retrieved successfully.
      JSON: { "status": "success", "prescription": <PrescriptionObject> }
            (where <PrescriptionObject> includes 'medications' list)
    - 400 Bad Request: `user_id` query parameter is missing or invalid.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: The `user_id` provided is not authorized to view this prescription.
      JSON: { "status": "error", "message": "User not authorized to view this prescription." }
    - 404 Not Found: No prescription found for the given `prescription_id`.
      JSON: { "status": "error", "message": "Prescription not found." }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    requesting_user_id_str = request.args.get('user_id') # Simulating auth context
    if not requesting_user_id_str:
        return jsonify({"status": "error", "message": "user_id query parameter is required for authorization."}), 400
    try:
        requesting_user_id = int(requesting_user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id must be an integer."}), 400

    # Auth Placeholder: In a real system, `requesting_user_id` and their role would be
    # determined from a session cookie or authorization token (e.g., JWT).

    with get_db_connection(DB_NAME) as conn:
        try:
            prescription = db_get_prescription_by_id(conn, prescription_id)
            if not prescription:
                return jsonify({"status": "error", "message": "Prescription not found."}), 404

            # Authorization Check: Verify requesting_user_id is the patient or provider.
            if not (prescription['patient_id'] == requesting_user_id or \
                    prescription['provider_id'] == requesting_user_id):
                # Log unauthorized access attempt for security auditing
                print(f"Authorization failed: User {requesting_user_id} attempted to access prescription {prescription_id}.")
                return jsonify({"status": "error", "message": "User not authorized to view this prescription."}), 403

            return jsonify({"status": "success", "prescription": prescription}), 200
        except ValueError as ve: # Should be caught by Flask for path param, but good for direct db_util call issues
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"Database error in get_prescription_details_api for prescription {prescription_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while retrieving prescription details."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_prescription_details_api for prescription {prescription_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/patients/<int:patient_id>/prescriptions', methods=['GET'])
def get_patient_prescriptions_api(patient_id: int):
    """
    Patient: Get a list of their prescriptions (summary view).

    Retrieves a list of prescription summaries for the specified patient.
    Authorization is simulated: requires a `user_id` query parameter that must
    match the `patient_id` in the path.
    Optional query parameters allow filtering by issue date range and status.

    Path Parameters:
        patient_id (int): The ID of the patient whose prescriptions are to be fetched.

    Query Parameters:
        user_id (int): Required for simulated auth. Must match `patient_id`.
        start_date_filter (str, optional): Filter by issue_date on or after (YYYY-MM-DD).
        end_date_filter (str, optional): Filter by issue_date on or before (YYYY-MM-DD).
        status_filter (str, optional): Filter by exact prescription status.

    Responses:
    - 200 OK: Successfully retrieved prescriptions.
      JSON: { "status": "success", "patient_id": int, "prescriptions": list[dict] }
            (list contains prescription summaries, not full medication details)
    - 400 Bad Request: Missing/invalid `user_id` or invalid filter formats.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: `user_id` does not match `patient_id`.
      JSON: { "status": "error", "message": "User not authorized..." }
    - 500 Internal Server Error: Database error.
    """
    requesting_user_id_str = request.args.get('user_id') # Simulating auth context
    if not requesting_user_id_str:
        return jsonify({"status": "error", "message": "user_id query parameter is required for authorization."}), 400
    try:
        requesting_user_id = int(requesting_user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id for authorization must be an integer."}), 400

    # Auth Check: Ensure the requesting user is the patient whose prescriptions are being requested.
    # A more complex system might allow providers linked to the patient to also access this.
    if patient_id != requesting_user_id:
        print(f"Authorization failed: User {requesting_user_id} attempted to access prescriptions for patient {patient_id}.")
        return jsonify({"status": "error", "message": "User not authorized to view these prescriptions."}), 403

    start_date = request.args.get('start_date_filter')
    end_date = request.args.get('end_date_filter')
    status = request.args.get('status_filter')

    # Validate date filter formats
    if start_date and not _validate_date_string(start_date):
        return jsonify({"status": "error", "message": "Invalid start_date_filter format. Use YYYY-MM-DD."}), 400
    if end_date and not _validate_date_string(end_date):
        return jsonify({"status": "error", "message": "Invalid end_date_filter format. Use YYYY-MM-DD."}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            prescriptions_list = db_get_prescriptions_for_user(
                conn, user_id=patient_id, user_role='patient',
                start_date_filter=start_date, end_date_filter=end_date, status_filter=status
            )
            return jsonify({"status": "success", "patient_id": patient_id, "prescriptions": prescriptions_list}), 200
        except ValueError as ve: # From db_util if date format validation fails there
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"Database error in get_patient_prescriptions_api for patient {patient_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while retrieving prescriptions."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_patient_prescriptions_api for patient {patient_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/providers/<int:provider_id>/prescriptions', methods=['GET'])
def get_provider_prescriptions_api(provider_id: int):
    """
    Provider: Get a list of prescriptions they issued.

    Retrieves a list of prescription summaries issued by the specified provider.
    Authorization is simulated: requires a `user_id` query parameter that must
    match the `provider_id` in the path.
    Optional query parameters allow filtering by issue date range and status.

    Path Parameters:
        provider_id (int): The ID of the provider whose prescriptions are to be fetched.

    Query Parameters:
        user_id (int): Required for simulated auth. Must match `provider_id`.
        start_date_filter (str, optional): Filter by issue_date on or after (YYYY-MM-DD).
        end_date_filter (str, optional): Filter by issue_date on or before (YYYY-MM-DD).
        status_filter (str, optional): Filter by exact prescription status.

    Responses:
    - 200 OK: Successfully retrieved prescriptions.
      JSON: { "status": "success", "provider_id": int, "prescriptions": list[dict] }
            (list contains prescription summaries)
    - 400 Bad Request: Missing/invalid `user_id` or invalid filter formats.
    - 403 Forbidden: `user_id` does not match `provider_id`.
    - 500 Internal Server Error: Database error.
    """
    requesting_user_id_str = request.args.get('user_id') # Simulating auth context
    if not requesting_user_id_str:
        return jsonify({"status": "error", "message": "user_id query parameter is required for authorization."}), 400
    try:
        requesting_user_id = int(requesting_user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id for authorization must be an integer."}), 400

    # Auth Check: Ensure the requesting user is the provider.
    if provider_id != requesting_user_id:
        print(f"Authorization failed: User {requesting_user_id} attempted to access prescriptions for provider {provider_id}.")
        return jsonify({"status": "error", "message": "User not authorized to view these prescriptions."}), 403

    start_date = request.args.get('start_date_filter')
    end_date = request.args.get('end_date_filter')
    status = request.args.get('status_filter')

    if start_date and not _validate_date_string(start_date):
        return jsonify({"status": "error", "message": "Invalid start_date_filter format. Use YYYY-MM-DD."}), 400
    if end_date and not _validate_date_string(end_date):
        return jsonify({"status": "error", "message": "Invalid end_date_filter format. Use YYYY-MM-DD."}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            prescriptions_list = db_get_prescriptions_for_user(
                conn, user_id=provider_id, user_role='provider',
                start_date_filter=start_date, end_date_filter=end_date, status_filter=status
            )
            return jsonify({"status": "success", "provider_id": provider_id, "prescriptions": prescriptions_list}), 200
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"Database error in get_provider_prescriptions_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_provider_prescriptions_api for provider {provider_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/prescriptions/<int:prescription_id>/cancel', methods=['PUT'])
def cancel_prescription_api(prescription_id: int):
    """
    Provider: Cancel a prescription.

    Allows an authenticated provider to cancel a prescription they issued.
    The `provider_id` from the authenticated context (simulated via request body)
    must match the provider who originally issued the prescription.

    Path Parameters:
        prescription_id (int): The ID of the prescription to cancel.

    Request Body JSON:
    {
        "provider_id": int,         // ID of the provider cancelling (for auth simulation)
        "reason": "str"             // Optional reason for cancellation
    }

    Responses:
    - 200 OK: Prescription cancelled successfully.
      JSON: { "status": "success", "message": "Prescription cancelled successfully.",
              "prescription_id": int, "new_status": "cancelled" }
    - 400 Bad Request: Missing `provider_id` in payload or invalid format.
    - 403 Forbidden/404 Not Found: Failed to cancel (e.g., provider not authorized,
                                   prescription not found, or already in a final state).
    - 500 Internal Server Error: Database error.
    """
    data = request.get_json()
    if not data or 'provider_id' not in data: # provider_id simulates authenticated user context
        return jsonify({"status": "error", "message": "Missing provider_id in request body for authorization."}), 400

    provider_id_from_auth = data.get('provider_id') # In real app, from session/token
    reason = data.get('reason') # Optional

    if not isinstance(provider_id_from_auth, int):
        return jsonify({"status": "error", "message": "provider_id must be an integer."}), 400

    # Auth Placeholder: Verify current_user.id == provider_id_from_auth and current_user.is_provider

    with get_db_connection(DB_NAME) as conn:
        try:
            success = db_update_prescription_status(
                conn,
                prescription_id=prescription_id,
                new_status='cancelled',
                current_provider_id=provider_id_from_auth, # This is the acting provider
                notes=reason
            )
            if success:
                # Notification Placeholder: Consider notifying the patient and/or pharmacy.
                print(f"Conceptual: Notify relevant parties about cancellation of prescription {prescription_id}")
                return jsonify({
                    "status": "success",
                    "message": "Prescription cancelled successfully.",
                    "prescription_id": prescription_id,
                    "new_status": "cancelled" # Echo the new status
                }), 200
            else:
                # db_update_prescription_status returns False if not found or auth failed.
                return jsonify({"status": "error", "message": "Failed to cancel prescription. It may not exist, or you are not authorized."}), 403 # Or 404
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"Database error in cancel_prescription_api for prescription {prescription_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while cancelling the prescription."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in cancel_prescription_api for prescription {prescription_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


if __name__ == '__main__':
    # This section is for development and direct execution of the Flask app.
    # In a production environment, a WSGI server like Gunicorn or uWSGI should be used.
    print(f"Attempting to initialize database '{DB_NAME}' for prescriptions API...")
    try:
        # Ensure the database and schema are set up when running directly.
        with get_db_connection(DB_NAME) as conn:
            initialize_prescription_schema(conn) # This also creates users and a minimal appointments table.

            # Optionally, seed some basic users and a dummy appointment if they don't exist,
            # as FK constraints rely on them. The db_utils_prescription.py __main__ block
            # has more extensive seeding if run directly.
            # This helps make the API immediately testable for development.
            try:
                cursor = conn.cursor()
                # Using INSERT OR IGNORE to prevent errors if users/appts already exist
                # These IDs are arbitrary and just for local dev convenience.
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username, email, phone) VALUES (?, ?, ?, ?)",
                             (701, 'api_presc_doc', 'doc.presc@clinic.com', '555100701'))
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username, email, phone) VALUES (?, ?, ?, ?)",
                             (801, 'api_presc_pat', 'pat.presc@example.com', '555100801'))
                cursor.execute("INSERT OR IGNORE INTO appointments (appointment_id, patient_id, provider_id, appointment_start_time) VALUES (?, ?, ?, ?)",
                             (901, 801, 701, '2024-01-01 10:00:00'))
                conn.commit()
                print("Default/test users and appointment ensured for prescription_api development.")
            except sqlite3.Error as e_seed:
                print(f"Notice: Error during optional data seeding for prescription_api: {e_seed} (Data might already exist).")
    except sqlite3.Error as e_main_setup:
        print(f"FATAL: Could not initialize prescription database '{DB_NAME}': {e_main_setup}")
    except Exception as e_gen_main:
        print(f"An unexpected error occurred during initial API setup: {e_gen_main}")

    app.run(debug=True, port=5003) # Using a different port from other APIs
