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
    request_appointment as db_request_appointment, # Aliased
    get_appointment_by_id,
    get_appointments_for_user,
    update_appointment_status
)

app = Flask(__name__)
# Configure DB_NAME using an environment variable with a default
DB_NAME = os.getenv('APPOINTMENT_DB_NAME', 'appointment_app.db')

# --- Helper Functions ---
def validate_datetime_string_format(datetime_str: str, format_str: str ='%Y-%m-%d %H:%M:%S') -> bool:
    """
    Validates if a string matches the specified datetime format.

    Args:
        datetime_str (str): The string to validate.
        format_str (str): The expected datetime format.

    Returns:
        bool: True if the string matches the format, False otherwise.
    """
    if not isinstance(datetime_str, str): # Ensure it's a string before trying strptime
        return False
    try:
        datetime.strptime(datetime_str, format_str)
        return True
    except ValueError: # Handles incorrect format
        return False

# --- Provider Availability Endpoints ---

@app.route('/api/providers/<int:provider_id>/availability', methods=['POST'])
def add_availability_api(provider_id: int):
    """
    Provider: Add a new availability block.

    Allows a provider to specify a time block during which they are available.
    An optional recurrence rule can be provided. The provider_id in the path
    is used to associate the availability. In a real system, this provider_id
    should match the authenticated provider user.

    Path Parameters:
        provider_id (int): The ID of the provider for whom availability is being added.

    Request Body JSON:
    {
        "start_datetime": "YYYY-MM-DD HH:MM:SS",  // Required
        "end_datetime": "YYYY-MM-DD HH:MM:SS",    // Required
        "recurring_rule": "RRULE_STRING"          // Optional (e.g., "FREQ=WEEKLY;BYDAY=MO")
    }

    Responses:
    - 201 Created: Availability added successfully.
      JSON: {
          "status": "success",
          "message": "Availability added successfully.",
          "availability_id": int,
          "provider_id": int
      }
    - 400 Bad Request: Missing required fields, invalid datetime format,
                       end time not after start time (DB check), or provider ID not found (FK error).
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error or other unexpected server issues.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    # Auth Placeholder: In a production application, the `provider_id` from the path
    # should be verified against the authenticated user's ID or administrative privileges.
    # Example: if not (current_user.is_provider and current_user.id == provider_id or current_user.is_admin()):
    #              return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    start_datetime_str = data.get('start_datetime')
    end_datetime_str = data.get('end_datetime')
    recurring_rule = data.get('recurring_rule')

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
            return jsonify({
                "status": "success",
                "message": "Availability added successfully.",
                "availability_id": new_availability_id,
                "provider_id": provider_id
            }), 201
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.IntegrityError as ie:
            print(f"DB IntegrityError in add_availability_api for provider {provider_id}: {ie}")
            if "FOREIGN KEY constraint failed" in str(ie):
                 return jsonify({"status": "error", "message": f"Provider with ID {provider_id} not found."}), 400
            if "CHECK constraint failed" in str(ie):
                 return jsonify({"status": "error", "message": "End datetime must be after start datetime or other check failed."}), 400
            return jsonify({"status": "error", "message": f"Database integrity error: {str(ie)}"}), 400
        except sqlite3.Error as e:
            print(f"DB Error in add_availability_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while adding availability."}), 500
        except Exception as e_gen: # Catch any other unexpected errors
            print(f"Unexpected error in add_availability_api for provider {provider_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/providers/<int:provider_id>/availability', methods=['GET'])
def get_availability_api(provider_id: int):
    """
    Get all availability blocks for a provider.

    Retrieves a list of availability blocks for the specified provider.
    This endpoint is typically public or accessible to authenticated users (e.g., patients)
    looking for available slots. It can be filtered by a time window using
    `start_filter` and `end_filter` query parameters.

    Path Parameters:
        provider_id (int): The ID of the provider whose availability is being fetched.

    Query Parameters:
        start_filter (str, optional): Start of the filter window (YYYY-MM-DD HH:MM:SS).
                                      If provided, `end_filter` is also required.
        end_filter (str, optional): End of the filter window (YYYY-MM-DD HH:MM:SS).
                                    If provided, `start_filter` is also required.
    Responses:
    - 200 OK: Successfully retrieved availability.
      JSON: {
          "status": "success",
          "provider_id": int,
          "availability": [
              {
                  "availability_id": int,
                  "provider_id": int,
                  "start_datetime": "YYYY-MM-DD HH:MM:SS",
                  "end_datetime": "YYYY-MM-DD HH:MM:SS",
                  "recurring_rule": "RRULE_STRING | null"
              }, ...
          ]
      }
    - 400 Bad Request: Invalid filter format or missing one of start/end filter if the other is present.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    start_filter = request.args.get('start_filter')
    end_filter = request.args.get('end_filter')

    # Validate filter parameters
    if (start_filter and not end_filter) or (not start_filter and end_filter):
        return jsonify({"status": "error", "message": "Both start_filter and end_filter must be provided if one is used."}), 400
    if start_filter and not validate_datetime_string_format(start_filter):
        return jsonify({"status": "error", "message": "Invalid start_filter format. Use YYYY-MM-DD HH:MM:SS"}), 400
    if end_filter and not validate_datetime_string_format(end_filter):
        return jsonify({"status": "error", "message": "Invalid end_filter format. Use YYYY-MM-DD HH:MM:SS"}), 400

    with get_db_connection(DB_NAME) as conn:
        try:
            # The db_utils function handles cases where provider_id might not exist by returning an empty list.
            availability_blocks = get_provider_availability(conn, provider_id, start_filter, end_filter)
            return jsonify({"status": "success", "provider_id": provider_id, "availability": availability_blocks}), 200
        except ValueError as ve:
             return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_availability_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching availability."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_availability_api for provider {provider_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

@app.route('/api/providers/availability/<int:availability_id>', methods=['DELETE'])
def delete_availability_api(availability_id: int):
    """
    Provider: Delete an availability slot.

    Allows an authenticated provider to delete one of their specific availability slots.
    The `provider_id` from the authenticated context (simulated via request body here)
    must match the provider associated with the availability slot.

    Path Parameters:
        availability_id (int): The ID of the availability slot to delete.

    Request Body JSON (for simulated auth context):
    {
        "provider_id": int  // ID of the provider making the request
    }

    Responses:
    - 200 OK: Availability slot deleted successfully.
      JSON: { "status": "success", "message": "Availability slot deleted successfully." }
    - 400 Bad Request: Missing `provider_id` in payload or invalid format.
      JSON: { "status": "error", "message": "Error description" }
    - 404 Not Found: Availability slot not found or not owned by the requesting provider.
      JSON: { "status": "error", "message": "Availability slot not found or you are not authorized to delete it." }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    data = request.get_json()
    if not data or 'provider_id' not in data:
        return jsonify({"status": "error", "message": "Missing provider_id in request body for authorization."}), 400

    provider_id_from_auth = data.get('provider_id') # In real app, from session/token
    if not isinstance(provider_id_from_auth, int):
        return jsonify({"status": "error", "message": "provider_id in body must be an integer."}), 400

    # Auth Placeholder: Verify current_user.id == provider_id_from_auth and current_user.is_provider

    with get_db_connection(DB_NAME) as conn:
        try:
            deleted = delete_provider_availability(conn, availability_id, provider_id_from_auth)
            if deleted:
                return jsonify({"status": "success", "message": "Availability slot deleted successfully."}), 200
            else:
                # This covers "not found" for this specific availability_id under this provider,
                # or if availability_id exists but belongs to another provider.
                return jsonify({"status": "error", "message": "Availability slot not found or you are not authorized to delete it."}), 404
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in delete_availability_api for availability ID {availability_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in delete_availability_api for availability ID {availability_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

# --- Appointment Endpoints ---

@app.route('/api/appointments/request', methods=['POST'])
def request_appointment_api():
    """
    Patient: Request a new appointment with a provider.

    The appointment is created with a status of 'pending_provider_confirmation'.
    Validation of times against provider availability is not performed at this stage
    but would be a critical addition in a full system.

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
    - 400 Bad Request: Missing fields, invalid data types, invalid time range (DB check),
                       or patient/provider ID not found (FK constraint).
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
    reason_for_visit = data.get('reason_for_visit')
    notes_by_patient = data.get('notes_by_patient')

    # Auth Placeholder: In a real app, patient_id should ideally match the
    # authenticated user ID making the request.
    # if not current_user.is_patient or current_user.id != patient_id: return jsonify({"status": "error", "message": "Unauthorized"}), 403

    required_fields = ['patient_id', 'provider_id', 'appointment_start_time', 'appointment_end_time']
    missing = [field for field in required_fields if data.get(field) is None]
    if missing:
        return jsonify({"status": "error", "message": f"Missing required fields: {', '.join(missing)}"}), 400

    if not isinstance(patient_id, int) or not isinstance(provider_id, int):
        return jsonify({"status": "error", "message": "patient_id and provider_id must be integers"}), 400
    if not validate_datetime_string_format(start_time) or not validate_datetime_string_format(end_time):
        return jsonify({"status": "error", "message": "Invalid datetime format for appointment times. Use YYYY-MM-DD HH:MM:SS"}), 400

    # Business Logic Placeholder: A crucial step in a real system would be to check
    # if the requested slot [start_time, end_time] is actually available for the provider
    # by checking against `provider_availability` and existing `appointments`.
    # This logic is complex and would typically reside in a service layer or within this API.
    # For now, we proceed directly to attempting to book.

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
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.IntegrityError as ie:
            print(f"DB IntegrityError in request_appointment_api: {ie}")
            if "FOREIGN KEY constraint failed" in str(ie):
                 return jsonify({"status": "error", "message": "Invalid patient_id or provider_id (user does not exist)."}), 400
            if "CHECK constraint failed" in str(ie):
                 return jsonify({"status": "error", "message": "Appointment time range is invalid or other check failed."}), 400
            return jsonify({"status": "error", "message": f"Database integrity error: {str(ie)}"}), 400
        except sqlite3.Error as e:
            print(f"DB Error in request_appointment_api: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while requesting the appointment."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in request_appointment_api: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/providers/<int:provider_id>/appointments', methods=['GET'])
def get_provider_appointments_api(provider_id: int):
    """
    Provider: Get their appointments, with optional filters.

    Retrieves a list of appointments associated with the specified provider_id.
    Allows filtering by status and a date range (YYYY-MM-DD) for `appointment_start_time`.

    Path Parameters:
        provider_id (int): The ID of the provider. (Auth: should match logged-in provider)

    Query Parameters:
        status (str, optional): Filter appointments by this status (e.g., 'confirmed', 'pending_provider_confirmation').
        date_from (str, optional): Start date for filtering appointments (YYYY-MM-DD).
        date_to (str, optional): End date for filtering appointments (YYYY-MM-DD).

    Responses:
    - 200 OK: Successfully retrieved appointments.
      JSON: { "status": "success", "provider_id": int, "appointments": list[dict] }
            Each dict in 'appointments' contains full appointment details including usernames.
    - 400 Bad Request: Invalid date format for filters.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: If the authenticated user is not the specified provider or an admin. (Conceptual)
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    # Auth Placeholder: Verify authenticated user IS this provider_id or has admin rights.
    # user_making_request = get_current_user_from_session_or_token()
    # if not ((user_making_request.id == provider_id and user_making_request.role == 'provider') or user_making_request.is_admin):
    #    return jsonify({"status": "error", "message": "Forbidden to access this provider's appointments."}), 403

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
                conn, user_id=provider_id, user_role='provider',
                status_filter=status_filter, start_date_filter=date_from_filter, end_date_filter=date_to_filter
            )
            return jsonify({"status": "success", "provider_id": provider_id, "appointments": appointments_list}), 200
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_provider_appointments_api for provider {provider_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching provider appointments."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_provider_appointments_api for provider {provider_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/patients/<int:patient_id>/appointments', methods=['GET'])
def get_patient_appointments_api(patient_id: int):
    """
    Patient: Get their appointments, with optional filters.

    Retrieves a list of appointments associated with the specified patient_id.
    Allows filtering by status and a date range (YYYY-MM-DD) for `appointment_start_time`.

    Path Parameters:
        patient_id (int): The ID of the patient. (Auth: should match logged-in patient, or provider with access)

    Query Parameters:
        status (str, optional): Filter appointments by this status.
        date_from (str, optional): Start date for filtering (YYYY-MM-DD).
        date_to (str, optional): End date for filtering (YYYY-MM-DD).

    Responses:
    - 200 OK: Successfully retrieved appointments.
      JSON: { "status": "success", "patient_id": int, "appointments": list[dict] }
    - 400 Bad Request: Invalid date format for filters.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: If trying to access another patient's appointments without authorization.
    - 500 Internal Server Error: Database error.
    """
    # Auth Placeholder: Verify authenticated user IS this patient_id or an authorized provider for this patient.
    # user_making_request = get_current_user_from_session_or_token()
    # if not ( (user_making_request.id == patient_id and user_making_request.role == 'patient') or
    #          (user_making_request.role == 'provider' and user_is_linked_to_patient(user_making_request.id, patient_id)) or
    #          user_making_request.is_admin ):
    #    return jsonify({"status": "error", "message": "Forbidden to access this patient's appointments."}), 403

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
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_patient_appointments_api for patient {patient_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching patient appointments."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_patient_appointments_api for patient {patient_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


@app.route('/api/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment_details_api(appointment_id: int):
    """
    User (Patient/Provider): Get specific details for an appointment.

    Retrieves full details for a single appointment, including patient and provider usernames.
    Requires `user_id` query parameter for simulated authorization to ensure
    the requester is a participant in the appointment.

    Path Parameters:
        appointment_id (int): The ID of the appointment.

    Query Parameters (for simulated auth):
        user_id (int): ID of the user making the request.

    Responses:
    - 200 OK: Successfully retrieved appointment details.
      JSON: { "status": "success", "appointment": dict } (full appointment details)
    - 400 Bad Request: Missing or invalid `user_id` query parameter.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: User (from `user_id` query param) not authorized to view this appointment.
      JSON: { "status": "error", "message": "User not authorized to view this appointment." }
    - 404 Not Found: Appointment with the given `appointment_id` not found.
      JSON: { "status": "error", "message": "Appointment not found." }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    user_id_str = request.args.get('user_id') # Simulating auth context via query parameter
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

            # Auth Check: Verify requesting_user_id is part of this appointment.
            # In a real app, this would be based on the authenticated user's session/token.
            if not (appointment_details['patient_id'] == requesting_user_id or \
                    appointment_details['provider_id'] == requesting_user_id):
                print(f"Authorization failed: User {requesting_user_id} attempted to access appointment {appointment_id}.")
                return jsonify({"status": "error", "message": "User not authorized to view this appointment."}), 403

            return jsonify({"status": "success", "appointment": appointment_details}), 200
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in get_appointment_details_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while fetching appointment details."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in get_appointment_details_api for appointment {appointment_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

@app.route('/api/appointments/<int:appointment_id>/confirm', methods=['PUT'])
def confirm_appointment_api(appointment_id: int):
    """
    Provider: Confirm a pending appointment.

    Updates the appointment's status to 'confirmed' and typically generates a video room name.
    Requires `provider_id` in the payload for simulated authorization, representing
    the ID of the authenticated provider performing the action.

    Path Parameters:
        appointment_id (int): The ID of the appointment to confirm.

    Request Body JSON:
    {
        "provider_id": int  // ID of the provider confirming (for auth simulation)
    }

    Responses:
    - 200 OK: Appointment confirmed successfully.
      JSON: { "status": "success", "appointment": dict } (updated appointment details, including video_room_name)
    - 400 Bad Request: Missing `provider_id` in payload or invalid format.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden: Authenticated provider is not authorized to confirm this appointment,
                     or appointment is not in a confirmable state.
      JSON: { "status": "error", "message": "Error description" }
    - 404 Not Found: If the appointment to be confirmed does not exist.
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

    # Auth Placeholder: In a real application, the actual provider_id would be derived
    # from the authenticated user's session or token.

    with get_db_connection(DB_NAME) as conn:
        try:
            success = update_appointment_status(
                conn,
                appointment_id=appointment_id,
                new_status='confirmed',
                current_user_id=provider_id_from_payload,
                user_role='provider'
                # Optional: notes=data.get('notes_by_provider') could be added
            )
            if success:
                updated_appointment = get_appointment_by_id(conn, appointment_id)
                if updated_appointment:
                    # Notification Placeholder: Consider sending a notification to the patient.
                    print(f"Conceptual: Notify patient for confirmed appointment {appointment_id}")
                    return jsonify({"status": "success", "appointment": updated_appointment}), 200
                else:
                    print(f"Error: Appointment {appointment_id} status updated to confirmed, but failed to retrieve updated details.")
                    return jsonify({"status": "error", "message": "Appointment confirmed but failed to retrieve updated details."}), 500
            else:
                # update_appointment_status returns False for "not found" or "auth failed".
                # API returns a generic message; db_util logs specifics.
                return jsonify({"status": "error", "message": "Failed to confirm appointment. It may not exist, not be in a confirmable state, or you are not authorized."}), 403
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in confirm_appointment_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while confirming the appointment."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in confirm_appointment_api for appointment {appointment_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

@app.route('/api/appointments/<int:appointment_id>/cancel', methods=['PUT'])
def cancel_appointment_api(appointment_id: int):
    """
    User (Patient/Provider): Cancel an appointment.

    Allows an authenticated patient or provider to cancel an appointment.
    The role of the canceller determines the new status (e.g., 'cancelled_by_patient')
    and where any provided notes (reason for cancellation) are stored.

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
    - 400 Bad Request: Missing fields in payload or invalid role/user_id.
      JSON: { "status": "error", "message": "Error description" }
    - 403 Forbidden/404 Not Found: Failed to cancel (e.g., user not authorized, appointment not found,
                                   or appointment not in a cancellable state).
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error.
      JSON: { "status": "error", "message": "A database error occurred." }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    user_id_from_payload = data.get('user_id')
    role_from_payload = data.get('cancelled_by_role')
    reason_from_payload = data.get('reason')

    if user_id_from_payload is None or not role_from_payload:
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
                current_user_id=user_id_from_payload,
                user_role=role_from_payload,
                notes=reason_from_payload
            )
            if success:
                # Notification Placeholder: Notify the other party about the cancellation.
                print(f"Conceptual: Notify other party for cancelled appointment {appointment_id}")
                return jsonify({
                    "status": "success",
                    "message": "Appointment cancelled successfully.",
                    "appointment_id": appointment_id,
                    "new_appointment_status": new_status
                }), 200
            else:
                return jsonify({"status": "error", "message": "Failed to cancel appointment. It may not exist, already be in a final state, or you are not authorized."}), 403
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        except sqlite3.Error as e:
            print(f"DB Error in cancel_appointment_api for appointment {appointment_id}: {e}")
            return jsonify({"status": "error", "message": "A database error occurred while cancelling the appointment."}), 500
        except Exception as e_gen:
            print(f"Unexpected error in cancel_appointment_api for appointment {appointment_id}: {e_gen}")
            return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500

if __name__ == '__main__':
    # This section is for development and direct execution of the Flask app.
    # In a production environment, a WSGI server like Gunicorn or uWSGI should be used.
    print(f"Attempting to initialize database '{DB_NAME}' for appointments API...")
    try:
        # Ensure the database and schema are set up when running directly.
        with get_db_connection(DB_NAME) as conn:
            initialize_appointment_schema(conn) # This also creates the users table.
            # Optionally, seed some basic users if the users table is empty,
            # to make the API immediately testable for development.
            # The db_utils_appointment.py __main__ block has more extensive seeding if run directly.
            try:
                cursor = conn.cursor()
                # Using INSERT OR IGNORE to prevent errors if users already exist from other setup scripts.
                # These specific user IDs might be useful for manual API testing.
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username, email, phone) VALUES (?, ?, ?, ?)",
                             (1, 'api_doc_alice', 'alice.api@example.com', '111-222-0000'))
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username, email, phone) VALUES (?, ?, ?, ?)",
                             (101, 'api_pat_bob', 'bob.api@example.com', '444-555-0000'))
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username, email, phone) VALUES (?, ?, ?, ?)",
                             (102, 'api_pat_claire', 'claire.api@example.com', '777-888-0000'))
                conn.commit()
                print("Default users (api_doc_alice, api_pat_bob, api_pat_claire) ensured for development.")
            except sqlite3.Error as e_user_seed:
                # This might happen if table structure changed or other integrity issues.
                print(f"Notice: Error during optional user seeding: {e_user_seed} (Users might already exist or schema issue).")
    except sqlite3.Error as e_main_setup:
        print(f"FATAL: Could not initialize appointment database '{DB_NAME}': {e_main_setup}")
        # Depending on severity, might want to sys.exit(1) here if DB is critical for app start
    except Exception as e_gen_setup:
        print(f"An unexpected error occurred during initial API setup: {e_gen_setup}")

    app.run(debug=True, port=5002)
