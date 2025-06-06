from flask import Flask, request, jsonify
from datetime import datetime # For parsing/validation if not handled by DB utils
import sqlite3
import os # For os.getenv

from db_utils_appointment import (
    get_db_connection,
    initialize_appointment_schema,
    add_provider_availability,
    get_provider_availability,
    delete_provider_availability,
    request_appointment as db_request_appointment, # Alias to avoid name clash
    get_appointment_by_id,
    get_appointments_for_user,
    update_appointment_status
)

app = Flask(__name__)
# Configure DB_NAME using an environment variable with a default
DB_NAME = os.getenv('APPOINTMENT_DB_NAME', 'appointment_app.db')

# --- Helper Functions ---
def validate_datetime_string_format(datetime_str, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Validates if a string matches the specified datetime format.

    Args:
        datetime_str (str): The string to validate.
        format_str (str): The expected datetime format.

    Returns:
        bool: True if the string matches the format, False otherwise.
    """
    try:
        datetime.strptime(datetime_str, format_str)
        return True
    except (ValueError, TypeError): # Handles incorrect format or non-string input
        return False

# --- Provider Availability Endpoints ---

@app.route('/api/providers/<int:provider_id>/availability', methods=['POST'])
def add_availability_api(provider_id):
    """
    Provider: Add a new availability block.

    Allows a provider to specify a time block during which they are available.
    An optional recurrence rule can be provided.

    Path Parameters:
        provider_id (int): The ID of the provider.

    Request Body JSON:
    {
        "start_datetime": "YYYY-MM-DD HH:MM:SS",  // Required
        "end_datetime": "YYYY-MM-DD HH:MM:SS",    // Required
        "recurring_rule": "RRULE_STRING"          // Optional (e.g., "FREQ=WEEKLY;BYDAY=MO")
    }

    Responses:
    - 201 Created: Availability added successfully.
      JSON: { "status": "success", "message": "Availability added successfully.",
              "availability_id": int, "provider_id": int }
    - 400 Bad Request: Missing fields, invalid datetime format, end time not after start time,
                       or provider ID not found.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    # Auth Placeholder: In a real application, verify that the authenticated user
    # is the provider_id specified in the URL or has administrative rights.
    # For now, we proceed assuming the provider_id is authorized.

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    start_datetime_str = data.get('start_datetime')
    end_datetime_str = data.get('end_datetime')
    recurring_rule = data.get('recurring_rule') # Optional

    if not start_datetime_str or not end_datetime_str:
        return jsonify({"status": "error", "message": "Missing required fields: start_datetime, end_datetime"}), 400

    if not validate_datetime_string_format(start_datetime_str) or \
       not validate_datetime_string_format(end_datetime_str):
        return jsonify({"status": "error", "message": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS"}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            new_availability_id = add_provider_availability(
                conn, provider_id, start_datetime_str, end_datetime_str, recurring_rule
            )
            # add_provider_availability raises error on failure, so if we get here, it's likely success.
            return jsonify({
                "status": "success",
                "message": "Availability added successfully.",
                "availability_id": new_availability_id,
                "provider_id": provider_id
            }), 201
        except ValueError as ve: # From input validation in db_utils or here
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.IntegrityError as ie:
            # This can be due to provider_id not existing (FK constraint) or start/end time issue (CHECK constraint)
            print(f"DB IntegrityError in add_availability_api for provider {provider_id}: {ie}")
            if "FOREIGN KEY constraint failed" in str(ie):
                 return jsonify({"status": "error", "message": f"Provider with ID {provider_id} not found."}), 400
            if "CHECK constraint failed" in str(ie): # General check constraint message
                 return jsonify({"status": "error", "message": "End datetime must be after start datetime or other check failed."}), 400
            return jsonify({"status": "error", "message": f"Database integrity error: {str(ie)}"}), 400 # Generic for other integrity issues
        except sqlite3.Error as e:
            print(f"DB Error in add_availability_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while adding availability."}), 500
        except Exception as e:
            print(f"Unexpected error in add_availability_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/providers/<int:provider_id>/availability', methods=['GET'])
def get_availability_api(provider_id):
    """
    Provider/Patient: Get all availability blocks for a provider.

    Retrieves a list of availability blocks for the specified provider.
    Can be filtered by a time window using `start_filter` and `end_filter`
    query parameters.

    Path Parameters:
        provider_id (int): The ID of the provider.

    Query Parameters:
        start_filter (str, optional): Start of the filter window (YYYY-MM-DD HH:MM:SS).
        end_filter (str, optional): End of the filter window (YYYY-MM-DD HH:MM:SS).
                                    Both must be provided if one is used.
    Responses:
    - 200 OK: Successfully retrieved availability.
      JSON: { "status": "success", "provider_id": int, "availability": list[dict] }
            Each dict in 'availability' contains: availability_id, provider_id,
            start_datetime, end_datetime, recurring_rule.
    - 400 Bad Request: Invalid filter format or missing one of start/end filter.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    start_filter = request.args.get('start_filter')
    end_filter = request.args.get('end_filter')

    if (start_filter and not end_filter) or (not start_filter and end_filter):
        return jsonify({"status": "error", "message": "Both start_filter and end_filter must be provided if one is used."}), 400
    if start_filter and not validate_datetime_string_format(start_filter):
        return jsonify({"status": "error", "message": "Invalid start_filter format. Use YYYY-MM-DD HH:MM:SS"}), 400
    if end_filter and not validate_datetime_string_format(end_filter):
        return jsonify({"status": "error", "message": "Invalid end_filter format. Use YYYY-MM-DD HH:MM:SS"}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            # The db_utils function returns an empty list if provider_id not found or no availability,
            # which is an acceptable response for a GET request.
            availability_blocks = get_provider_availability(conn, provider_id, start_filter, end_filter)
            return jsonify({"status": "success", "provider_id": provider_id, "availability": availability_blocks}), 200
        except ValueError as ve: # Should ideally be caught by Flask's int converter for provider_id
             return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_availability_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching availability."}), 500
        except Exception as e:
            print(f"Unexpected error in get_availability_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

@app.route('/api/providers/availability/<int:availability_id>', methods=['DELETE'])
def delete_availability_api(availability_id):
    """
    Provider: Delete an availability slot.

    Allows a provider to delete one of their existing availability blocks.
    Requires provider_id in the payload for authorization simulation.

    Path Parameters:
        availability_id (int): The ID of the availability slot to delete.

    Request Body JSON:
    {
        "provider_id": int  // ID of the provider making the request (for auth simulation)
    }

    Responses:
    - 200 OK: Availability slot deleted successfully.
      JSON: { "status": "success", "message": "Availability slot deleted successfully." }
    - 400 Bad Request: Missing provider_id in payload or invalid format.
      JSON: { "status": "error", "message": "Error description" }
    - 404 Not Found: Availability slot not found or not owned by the provider.
      JSON: { "status": "error", "message": "Availability slot not found or you are not authorized to delete it." }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    data = request.get_json()
    if not data or 'provider_id' not in data:
        return jsonify({"status": "error", "message": "Missing provider_id in request body"}), 400

    provider_id_from_payload = data.get('provider_id')
    if not isinstance(provider_id_from_payload, int):
        return jsonify({"status": "error", "message": "provider_id must be an integer"}), 400

    # Auth Placeholder: In a real app, the provider_id would come from the authenticated session/token,
    # and it would be compared against the owner of the availability_id.

    with get_db_connection(DB_NAME) as conn:
        try:
            deleted = delete_provider_availability(conn, availability_id, provider_id_from_payload)
            if deleted:
                return jsonify({"status": "success", "message": "Availability slot deleted successfully."}), 200
            else:
                # This covers both "not found" and "not owned by this provider"
                return jsonify({"status": "error", "message": "Availability slot not found or you are not authorized to delete it."}), 404
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in delete_availability_api for availability {availability_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred."}), 500
        except Exception as e:
            print(f"Unexpected error in delete_availability_api for availability {availability_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

# --- Appointment Request Endpoint ---

@app.route('/api/appointments/request', methods=['POST'])
def request_appointment_api():
    """
    Patient: Request a new appointment with a provider.

    The appointment is created with a status of 'pending_provider_confirmation'.
    Further actions (e.g., provider confirming, checking availability conflicts)
    are handled by other endpoints or backend logic.

    Request Body JSON:
    {
        "patient_id": int,     // Required. In a real app, this might come from auth.
        "provider_id": int,    // Required
        "appointment_start_time": "YYYY-MM-DD HH:MM:SS", // Required
        "appointment_end_time": "YYYY-MM-DD HH:MM:SS",   // Required
        "reason_for_visit": "str",                       // Optional
        "notes_by_patient": "str"                        // Optional
    }

    Responses:
    - 201 Created: Appointment requested successfully.
      JSON: { "status": "success", "message": "...", "appointment_id": int }
    - 400 Bad Request: Missing fields, invalid data types, invalid time range,
                       or patient/provider ID not found.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    patient_id = data.get('patient_id')
    provider_id = data.get('provider_id')
    start_time = data.get('appointment_start_time')
    end_time = data.get('appointment_end_time')
    reason_for_visit = data.get('reason_for_visit') # Optional
    notes_by_patient = data.get('notes_by_patient') # Optional

    # Auth Placeholder: In a real app, patient_id should ideally match the
    # authenticated user making the request. For now, it's taken from payload.

    required_fields = ['patient_id', 'provider_id', 'appointment_start_time', 'appointment_end_time']
    missing = [field for field in required_fields if data.get(field) is None] # Check for None explicitly for int
    if missing:
        return jsonify({"status": "error", "message": f"Missing required fields: {', '.join(missing)}"}), 400

    if not isinstance(patient_id, int) or not isinstance(provider_id, int):
        return jsonify({"status": "error", "message": "patient_id and provider_id must be integers"}), 400
    if not validate_datetime_string_format(start_time) or not validate_datetime_string_format(end_time):
        return jsonify({"status": "error", "message": "Invalid datetime format for appointment times. Use YYYY-MM-DD HH:MM:SS"}), 400

    # Business Logic Placeholder: A real system would check for provider availability,
    # existing appointment conflicts, and other business rules here BEFORE attempting to save.
    # For this example, we proceed directly to the database request.

    with get_db_connection(DB_NAME) as conn:
        try:
            new_appointment_id = db_request_appointment(
                conn, patient_id, provider_id, start_time, end_time,
                reason_for_visit, notes_by_patient
            )
            return jsonify({
                "status": "success",
                "message": "Appointment requested successfully. Awaiting provider confirmation.",
                "appointment_id": new_appointment_id
            }), 201
        except ValueError as ve: # From db_utils validation
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.IntegrityError as ie:
            print(f"DB IntegrityError in request_appointment_api: {ie}")
            if "FOREIGN KEY constraint failed" in str(ie):
                 return jsonify({"status": "error", "message": "Invalid patient_id or provider_id (user does not exist)."}), 400
            if "CHECK constraint failed" in str(ie): # General check for time or other constraints
                 return jsonify({"status": "error", "message": "Appointment time range is invalid or other check failed."}), 400
            return jsonify({"status": "error", "message": f"Database integrity error: {str(ie)}"}), 400
        except sqlite3.Error as e:
            print(f"DB Error in request_appointment_api: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while requesting the appointment."}), 500
        except Exception as e:
            print(f"Unexpected error in request_appointment_api: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

# --- Appointment Retrieval and Management Endpoints ---

@app.route('/api/providers/<int:provider_id>/appointments', methods=['GET'])
def get_provider_appointments_api(provider_id):
    """
    Provider: Get their appointments, with optional filters.

    Retrieves a list of appointments associated with the specified provider_id.
    Allows filtering by status and a date range for `appointment_start_time`.

    Path Parameters:
        provider_id (int): The ID of the provider.

    Query Parameters:
        status (str, optional): Filter appointments by this status.
        date_from (str, optional): Start date for filtering (YYYY-MM-DD).
        date_to (str, optional): End date for filtering (YYYY-MM-DD).

    Responses:
    - 200 OK: Successfully retrieved appointments.
      JSON: { "status": "success", "provider_id": int, "appointments": list[dict] }
            Each dict in 'appointments' contains full appointment details including usernames.
    - 400 Bad Request: Invalid date format for filters.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    # Auth Placeholder: In a real app, verify the authenticated user IS this provider_id
    # or has rights to view these appointments.

    status_filter = request.args.get('status')
    date_from_filter = request.args.get('date_from') # Expected format: YYYY-MM-DD
    date_to_filter = request.args.get('date_to')     # Expected format: YYYY-MM-DD

    if date_from_filter and not validate_datetime_string_format(date_from_filter, '%Y-%m-%d'):
        return jsonify({"status": "error", "message": "Invalid date_from format. Use YYYY-MM-DD"}), 400
    if date_to_filter and not validate_datetime_string_format(date_to_filter, '%Y-%m-%d'):
        return jsonify({"status": "error", "message": "Invalid date_to format. Use YYYY-MM-DD"}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            appointments_list = get_appointments_for_user(
                conn, user_id=provider_id, user_role='provider',
                status_filter=status_filter, start_date_filter=date_from_filter, end_date_filter=date_to_filter
            )
            return jsonify({"status": "success", "provider_id": provider_id, "appointments": appointments_list}), 200
        except ValueError as ve: # From get_appointments_for_user if role is invalid (should not happen here)
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_provider_appointments_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching provider appointments."}), 500
        except Exception as e:
            print(f"Unexpected error in get_provider_appointments_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/patients/<int:patient_id>/appointments', methods=['GET'])
def get_patient_appointments_api(patient_id):
    """
    Patient: Get their appointments, with optional filters.

    Retrieves a list of appointments associated with the specified patient_id.
    Allows filtering by status and a date range for `appointment_start_time`.

    Path Parameters:
        patient_id (int): The ID of the patient.

    Query Parameters:
        status (str, optional): Filter appointments by this status.
        date_from (str, optional): Start date for filtering (YYYY-MM-DD).
        date_to (str, optional): End date for filtering (YYYY-MM-DD).

    Responses:
    - 200 OK: Successfully retrieved appointments.
      JSON: { "status": "success", "patient_id": int, "appointments": list[dict] }
    - 400 Bad Request: Invalid date format for filters.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    # Auth Placeholder: In a real app, verify the authenticated user IS this patient_id
    # or has delegated access (e.g., a provider viewing their patient's appointments).

    status_filter = request.args.get('status')
    date_from_filter = request.args.get('date_from')
    date_to_filter = request.args.get('date_to')

    if date_from_filter and not validate_datetime_string_format(date_from_filter, '%Y-%m-%d'):
        return jsonify({"status": "error", "message": "Invalid date_from format. Use YYYY-MM-DD"}), 400
    if date_to_filter and not validate_datetime_string_format(date_to_filter, '%Y-%m-%d'):
        return jsonify({"status": "error", "message": "Invalid date_to format. Use YYYY-MM-DD"}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            appointments_list = get_appointments_for_user(
                conn, user_id=patient_id, user_role='patient',
                status_filter=status_filter, start_date_filter=date_from_filter, end_date_filter=date_to_filter
            )
            return jsonify({"status": "success", "patient_id": patient_id, "appointments": appointments_list}), 200
        except ValueError as ve: # Should not happen here due to fixed role
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_patient_appointments_api for patient {patient_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching patient appointments."}), 500
        except Exception as e:
            print(f"Unexpected error in get_patient_appointments_api for patient {patient_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment_details_api(appointment_id):
    """
    User (Patient/Provider): Get specific details for an appointment.

    Retrieves full details for a single appointment.
    Requires `user_id` query parameter for simulated authorization to ensure
    the requester is a participant in the appointment.

    Path Parameters:
        appointment_id (int): The ID of the appointment.

    Query Parameters:
        user_id (int): ID of the user making the request (for authorization simulation).

    Responses:
    - 200 OK: Successfully retrieved appointment details.
      JSON: { "status": "success", "appointment": dict } (full appointment details)
    - 400 Bad Request: Missing or invalid `user_id` query parameter.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: User not authorized to view this appointment.
      JSON: { "status": "error", "message": "User not authorized to view this appointment." }
    - 404 Not Found: Appointment not found.
      JSON: { "status": "error", "message": "Appointment not found." }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    user_id_str = request.args.get('user_id')
    if not user_id_str:
        return jsonify({"status": "error", "message": "user_id query parameter is required for authorization."}), 400
    try:
        requesting_user_id = int(user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id must be an integer."}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            appointment_details = get_appointment_by_id(conn, appointment_id)
            if not appointment_details:
                return jsonify({"status": "error", "message": "Appointment not found."}), 404

            # Auth Check: Verify requesting_user_id is part of this appointment
            # In a real app, this user_id would come from an authenticated session/token.
            if not (appointment_details['patient_id'] == requesting_user_id or \
                    appointment_details['provider_id'] == requesting_user_id):
                # Log this attempt for security auditing if necessary
                print(f"Authorization failed: User {requesting_user_id} attempted to access appointment {appointment_id}.")
                return jsonify({"status": "error", "message": "User not authorized to view this appointment."}), 403

            return jsonify({"status": "success", "appointment": appointment_details}), 200
        except ValueError as ve: # Should not happen due to Flask's int converter for path param
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_appointment_details_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching appointment details."}), 500
        except Exception as e:
            print(f"Unexpected error in get_appointment_details_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

@app.route('/api/appointments/<int:appointment_id>/confirm', methods=['PUT'])
def confirm_appointment_api(appointment_id):
    """
    Provider: Confirm a pending appointment.

    Updates the appointment's status to 'confirmed' and generates a video room name.
    Requires `provider_id` in the payload for simulated authorization.

    Path Parameters:
        appointment_id (int): The ID of the appointment to confirm.

    Request Body JSON:
    {
        "provider_id": int  // ID of the provider confirming (for auth simulation)
    }

    Responses:
    - 200 OK: Appointment confirmed successfully.
      JSON: { "status": "success", "appointment": dict } (updated appointment details)
    - 400 Bad Request: Missing `provider_id` or invalid format.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden/404 Not Found: Failed to confirm (e.g., not authorized, appointment not found,
                                   or not in a confirmable state).
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    data = request.get_json()
    if not data or 'provider_id' not in data:
        return jsonify({"status": "error", "message": "Missing provider_id in request body"}), 400

    provider_id_from_payload = data.get('provider_id')
    if not isinstance(provider_id_from_payload, int):
        return jsonify({"status": "error", "message": "provider_id must be an integer"}), 400

    # Auth Placeholder: In a real app, the actual provider_id would come from an authenticated session/token.
    # The one from payload is used here to simulate which provider is making the call for the DB util's auth check.

    with get_db_connection(DB_NAME) as conn:
        try:
            # Attempt to update the status to 'confirmed'
            success = update_appointment_status(
                conn,
                appointment_id=appointment_id,
                new_status='confirmed',
                current_user_id=provider_id_from_payload, # This is the acting user
                user_role='provider'
                # 'notes' could be added here if the endpoint supported it, e.g., data.get('notes')
            )
            if success:
                # Fetch the updated appointment details to include in the response
                updated_appointment = get_appointment_by_id(conn, appointment_id)
                if updated_appointment:
                    # Notification Placeholder: Notify patient about confirmation.
                    print(f"Conceptual: Notify patient for confirmed appointment {appointment_id}")
                    return jsonify({"status": "success", "appointment": updated_appointment}), 200
                else:
                    # This case is unlikely if update_appointment_status succeeded, but good to handle.
                    print(f"Error: Appointment {appointment_id} status updated, but failed to retrieve updated details.")
                    return jsonify({"status": "error", "message": "Appointment status updated but failed to retrieve details."}), 500
            else:
                # update_appointment_status returns False if:
                # 1. Appointment not found.
                # 2. Authorization failed (e.g., provider_id_from_payload doesn't match appointment's provider).
                # 3. Status transition is not allowed by its internal logic (though not explicitly checked here).
                # For the API, it's often better to not reveal if an ID exists if unauthorized.
                # A 403 or 404 response is appropriate. The db_util prints more specific logs.
                return jsonify({"status": "error", "message": "Failed to confirm appointment. It may not exist, not be in a confirmable state, or you are not authorized."}), 403
        except ValueError as ve: # From input validation in this function or db_utils
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e: # General database error
            print(f"DB Error in confirm_appointment_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while confirming the appointment."}), 500
        except Exception as e:
            print(f"Unexpected error in confirm_appointment_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

@app.route('/api/appointments/<int:appointment_id>/cancel', methods=['PUT'])
def cancel_appointment_api(appointment_id):
    """
    User (Patient/Provider): Cancel an appointment.

    Allows a patient or provider to cancel an appointment.
    The role of the canceller determines the new status and where notes are stored.

    Path Parameters:
        appointment_id (int): The ID of the appointment to cancel.

    Request Body JSON:
    {
        "user_id": int,                             // ID of the user making the cancellation (for auth simulation)
        "cancelled_by_role": "patient" | "provider", // Role of the canceller
        "reason": "str"                             // Optional reason for cancellation
    }

    Responses:
    - 200 OK: Appointment cancelled successfully.
      JSON: { "status": "success", "message": "Appointment cancelled successfully.",
              "appointment_id": int, "new_appointment_status": str }
    - 400 Bad Request: Missing fields in payload or invalid role.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden/404 Not Found: Failed to cancel (e.g., not authorized, appointment not found,
                                   or not in a cancellable state).
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    user_id_from_payload = data.get('user_id')
    role_from_payload = data.get('cancelled_by_role')
    reason_from_payload = data.get('reason') # Optional

    # Validate required payload fields for this action
    if user_id_from_payload is None or not role_from_payload: # Check for None for int, not empty for role
        return jsonify({"status": "error", "message": "Missing user_id or cancelled_by_role in request body"}), 400
    if not isinstance(user_id_from_payload, int):
        return jsonify({"status": "error", "message": "user_id must be an integer"}), 400
    if role_from_payload not in ['patient', 'provider']:
        return jsonify({"status": "error", "message": "cancelled_by_role must be 'patient' or 'provider'"}), 400

    new_status = f"cancelled_by_{role_from_payload}"

    with get_db_connection(DB_NAME) as conn:
        try:
            success = update_appointment_status(
                conn,
                appointment_id=appointment_id,
                new_status=new_status,
                current_user_id=user_id_from_payload, # User performing the action
                user_role=role_from_payload,          # Role they are acting in
                notes=reason_from_payload
            )
            if success:
                # Notification Placeholder: Notify the other party about the cancellation.
                # E.g., if patient cancelled, notify provider, and vice-versa.
                print(f"Conceptual: Notify other party for cancelled appointment {appointment_id}")
                return jsonify({
                    "status": "success",
                    "message": "Appointment cancelled successfully.",
                    "appointment_id": appointment_id,
                    "new_appointment_status": new_status
                }), 200
            else:
                # Similar to /confirm, db_util's update_appointment_status returns False
                # for "not found" or "auth failed".
                return jsonify({"status": "error", "message": "Failed to cancel appointment. It may not exist, already be in a final state, or you are not authorized."}), 403 # Or 404
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in cancel_appointment_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while cancelling the appointment."}), 500
        except Exception as e:
            print(f"Unexpected error in cancel_appointment_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

if __name__ == '__main__':
    # Initialize the database schema when running the app directly.
    # This is suitable for development and testing.
    # In a production environment, database schema migrations should be handled
    # by a dedicated migration tool (e.g., Alembic for SQLAlchemy, or custom scripts).
    print(f"Attempting to initialize database '{DB_NAME}' for appointments...")
    try:
        with get_db_connection(DB_NAME) as conn:
            initialize_appointment_schema(conn)
            # Optionally, add a couple of test users like in db_utils_appointment for dev
            try:
                cursor = conn.cursor() # Use the connection from the 'with' block
                # Using INSERT OR IGNORE to prevent errors if users already exist
                cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?,?,?)", ('doc_alice','alice@example.com','111-222-3333'))
                cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?,?,?)", ('patient_bob','bob@example.com','444-555-6666'))
                cursor.execute("INSERT OR IGNORE INTO users (username, email, phone) VALUES (?,?,?)", ('patient_claire','claire@example.com','777-888-9999'))
                conn.commit()
                print("Default users (doc_alice, patient_bob, patient_claire) ensured for development.")
            except sqlite3.Error as e_user: # Catch error specifically for user insert
                print(f"Error ensuring default users: {e_user}")
    except sqlite3.Error as e_main:
        print(f"FATAL: Could not initialize appointment database: {e_main}")
    except Exception as e_gen:
        print(f"An unexpected error occurred during initial setup: {e_gen}")

    app.run(debug=True, port=5002)
