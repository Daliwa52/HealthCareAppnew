from flask import Flask, request, jsonify
from datetime import datetime # For basic datetime parsing/validation if needed

app = Flask(__name__)

# In a real application, you would configure your database connection here
# For example, using Flask-SQLAlchemy or another ORM/DB connector
# from flask_sqlalchemy import SQLAlchemy
# app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri_for_appointments'
# db = SQLAlchemy(app)

# --- Helper Functions (Placeholders) ---
def validate_datetime_format(datetime_str):
    """Basic validation for YYYY-MM-DD HH:MM:SS format."""
    try:
        datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False

# --- Provider Availability Endpoints ---

@app.route('/api/providers/<int:provider_id>/availability', methods=['POST'])
def add_provider_availability(provider_id):
    """
    Provider: Add a new availability block.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    start_datetime_str = data.get('start_datetime')
    end_datetime_str = data.get('end_datetime')
    recurring_rule = data.get('recurring_rule') # Optional

    # Basic Validation
    if not start_datetime_str or not end_datetime_str:
        return jsonify({"status": "error", "message": "Missing required fields: start_datetime, end_datetime"}), 400
    if not validate_datetime_format(start_datetime_str) or not validate_datetime_format(end_datetime_str):
        return jsonify({"status": "error", "message": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS"}), 400

    # Further validation: Ensure end_datetime > start_datetime (also handled by DB constraint)
    # dt_start = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M:%S')
    # dt_end = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M:%S')
    # if dt_end <= dt_start:
    #     return jsonify({"status": "error", "message": "end_datetime must be after start_datetime"}), 400

    # --- Placeholder for Database Logic ---
    # 1. Verify provider_id exists (if not handled by FK constraint implicitly or session management)
    #    print(f"Placeholder: Verifying provider_id {provider_id} exists.")
    # 2. Save the availability to the 'provider_availability' table.
    #    - Columns: provider_id, start_datetime, end_datetime, recurring_rule
    #    - This would involve database INSERT operation.
    print(f"Placeholder: Saving availability for provider {provider_id} from {start_datetime_str} to {end_datetime_str}, recurring: {recurring_rule}")
    # Example: new_availability_id = db_insert_availability(provider_id, start_datetime_str, end_datetime_str, recurring_rule)
    new_availability_id = 123 # Dummy ID

    # --- End of Placeholder for Database Logic ---

    return jsonify({
        "status": "success",
        "message": "Availability added successfully.",
        "availability_id": new_availability_id,
        "provider_id": provider_id
    }), 201

@app.route('/api/providers/<int:provider_id>/availability', methods=['GET'])
def get_provider_availability(provider_id):
    """
    Provider/Patient: Get all availability blocks for a provider.
    Could add query parameters for date ranges, e.g., ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    # --- Placeholder for Database Logic ---
    # 1. Verify provider_id exists (optional, could return empty list if not found or 404)
    #    print(f"Placeholder: Verifying provider_id {provider_id} exists.")
    # 2. Fetch availability from 'provider_availability' table for the given provider_id.
    #    - This would involve database SELECT operation.
    #    - May need to expand recurring rules if the query range is provided.
    print(f"Placeholder: Fetching availability for provider {provider_id}")
    # Example: availability_blocks = db_fetch_availability(provider_id, request.args.get('start_date'), request.args.get('end_date'))
    availability_blocks = [
        {"availability_id": 123, "provider_id": provider_id, "start_datetime": "2024-03-10 09:00:00", "end_datetime": "2024-03-10 12:00:00", "recurring_rule": None},
        {"availability_id": 124, "provider_id": provider_id, "start_datetime": "2024-03-10 14:00:00", "end_datetime": "2024-03-10 17:00:00", "recurring_rule": "FREQ=WEEKLY;BYDAY=MO"},
    ]
    # --- End of Placeholder for Database Logic ---

    if not availability_blocks: # Example: if DB query returned no results
        return jsonify({"status": "success", "provider_id": provider_id, "availability": []}), 200

    return jsonify({"status": "success", "provider_id": provider_id, "availability": availability_blocks}), 200

# --- Appointment Request Endpoint ---

@app.route('/api/appointments/request', methods=['POST'])
def request_appointment():
    """
    Patient: Request a new appointment.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    patient_id = data.get('patient_id')
    provider_id = data.get('provider_id')
    appointment_start_time_str = data.get('appointment_start_time')
    appointment_end_time_str = data.get('appointment_end_time')
    reason_for_visit = data.get('reason_for_visit') # Optional
    notes_by_patient = data.get('notes_by_patient') # Optional

    # Basic Validation
    required_fields = ['patient_id', 'provider_id', 'appointment_start_time', 'appointment_end_time']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    if not isinstance(patient_id, int) or not isinstance(provider_id, int):
        return jsonify({"status": "error", "message": "patient_id and provider_id must be integers"}), 400

    if not validate_datetime_format(appointment_start_time_str) or not validate_datetime_format(appointment_end_time_str):
        return jsonify({"status": "error", "message": "Invalid datetime format for appointment times. Use YYYY-MM-DD HH:MM:SS"}), 400

    # Further validation: end_time > start_time (also handled by DB)
    # dt_start = datetime.strptime(appointment_start_time_str, '%Y-%m-%d %H:%M:%S')
    # dt_end = datetime.strptime(appointment_end_time_str, '%Y-%m-%d %H:%M:%S')
    # if dt_end <= dt_start:
    #     return jsonify({"status": "error", "message": "appointment_end_time must be after appointment_start_time"}), 400


    # --- Placeholder for Database & Business Logic ---
    # 1. Verify patient_id and provider_id exist.
    #    print(f"Placeholder: Verifying patient {patient_id} and provider {provider_id} exist.")

    # 2. **Crucial Business Logic: Check Availability**
    #    - Fetch provider's availability blocks from `provider_availability` for the given period.
    #    - Fetch provider's existing confirmed/pending appointments from `appointments` for the given period.
    #    - Determine if the requested `appointment_start_time` to `appointment_end_time` slot is valid:
    #        a. Falls within one or more general availability blocks (considering recurring rules).
    #        b. Does not overlap with any existing confirmed/pending appointments for that provider.
    #        c. Adheres to any other business rules (e.g., minimum booking notice, appointment duration limits).
    #    - This is complex and would involve significant date/time manipulation and database querying.
    print(f"Placeholder: COMPLEX LOGIC - Checking provider {provider_id}'s availability for slot {appointment_start_time_str} - {appointment_end_time_str}")
    is_slot_available = True # Assume true for placeholder

    if not is_slot_available:
        return jsonify({"status": "error", "message": "Requested time slot is not available."}), 409 # 409 Conflict

    # 3. Save the appointment to the 'appointments' table.
    #    - Columns: patient_id, provider_id, appointment_start_time, appointment_end_time,
    #               reason_for_visit, notes_by_patient, status ('pending_provider_confirmation').
    #    - video_room_name could be generated here or later upon confirmation.
    print(f"Placeholder: Saving appointment request from patient {patient_id} to provider {provider_id} for {appointment_start_time_str}")
    # Example: new_appointment_id = db_create_appointment_request(...)
    new_appointment_id = 789 # Dummy ID
    initial_status = 'pending_provider_confirmation'
    # --- End of Placeholder for Database & Business Logic ---

    return jsonify({
        "status": "success",
        "message": "Appointment requested successfully. Awaiting provider confirmation.",
        "appointment_id": new_appointment_id,
        "patient_id": patient_id,
        "provider_id": provider_id,
        "appointment_start_time": appointment_start_time_str,
        "appointment_end_time": appointment_end_time_str,
        "current_status": initial_status
    }), 201


if __name__ == '__main__':
    # For development only. Use a WSGI server in production.
    app.run(debug=True, port=5002) # Using a different port to avoid conflicts


# --- Additional Appointment Management Endpoints ---

@app.route('/api/providers/<int:provider_id>/appointments', methods=['GET'])
def get_provider_appointments(provider_id):
    """
    Provider: Get their appointments, with optional filters.
    Query Params: status, date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)
    """
    status_filter = request.args.get('status')
    date_from_filter = request.args.get('date_from')
    date_to_filter = request.args.get('date_to')

    # --- Placeholder for Database Logic ---
    # 1. Verify provider_id exists (if not handled by session/auth).
    #    print(f"Placeholder: Verifying provider {provider_id} for fetching appointments.")
    # 2. Fetch appointments from 'appointments' table:
    #    - Filter by `provider_id`.
    #    - If `status_filter` is provided, filter by `status`.
    #    - If `date_from_filter` and/or `date_to_filter` are provided, filter by `appointment_start_time`.
    #      (Remember to parse date strings to datetime objects for comparison).
    print(f"Placeholder: Fetching appointments for provider {provider_id} with filters: status='{status_filter}', from='{date_from_filter}', to='{date_to_filter}'")
    # Example: provider_appointments = db_fetch_provider_appointments(provider_id, status_filter, date_from_filter, date_to_filter)
    provider_appointments = [
        {"appointment_id": 789, "patient_id": 1, "provider_id": provider_id, "appointment_start_time": "2024-03-15 10:00:00", "appointment_end_time": "2024-03-15 10:30:00", "status": "pending_provider_confirmation", "reason_for_visit": "Checkup"},
        {"appointment_id": 790, "patient_id": 2, "provider_id": provider_id, "appointment_start_time": "2024-03-16 11:00:00", "appointment_end_time": "2024-03-16 11:30:00", "status": "confirmed", "reason_for_visit": "Follow-up", "video_room_name": "RoomXYZ123"},
    ]
    # --- End of Placeholder for Database Logic ---

    return jsonify({"status": "success", "provider_id": provider_id, "appointments": provider_appointments}), 200


@app.route('/api/appointments/<int:appointment_id>/confirm', methods=['PUT'])
def confirm_appointment(appointment_id):
    """
    Provider: Confirm an appointment.
    Could also require provider_id in URL or payload for authorization.
    e.g., PUT /api/providers/<int:provider_id>/appointments/<int:appointment_id>/confirm
    """
    # In a real app, provider_id would come from auth token or session.
    # For placeholder, let's assume it might be in payload or we just trust the route for now.
    # acting_provider_id = request.get_json().get('acting_provider_id') if request.is_json else None


    # --- Placeholder for Database & Business Logic ---
    # 1. Fetch the appointment by `appointment_id`.
    #    print(f"Placeholder: Fetching appointment {appointment_id} for confirmation.")
    #    appointment = db_get_appointment(appointment_id)
    #    if not appointment:
    #        return jsonify({"status": "error", "message": "Appointment not found"}), 404

    # 2. Authorization: Verify the `acting_provider_id` (from auth/session) matches `appointment.provider_id`.
    #    print(f"Placeholder: Verifying provider is authorized to confirm appointment {appointment_id}.")
    #    # if appointment.provider_id != acting_provider_id:
    #    #     return jsonify({"status": "error", "message": "Forbidden"}), 403

    # 3. Validate appointment status (e.g., must be 'pending_provider_confirmation').
    #    print(f"Placeholder: Validating current status of appointment {appointment_id}.")
    #    # if appointment.status != 'pending_provider_confirmation':
    #    #     return jsonify({"status": "error", "message": f"Appointment cannot be confirmed. Current status: {appointment.status}"}), 409

    # 4. Generate a unique video_room_name.
    #    - Could be a UUID, or based on appointment_id, etc.
    video_room_name = f"VideoRoom_{appointment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"Placeholder: Generated video room name: {video_room_name} for appointment {appointment_id}.")

    # 5. Update appointment in 'appointments' table:
    #    - Set `status` to 'confirmed'.
    #    - Set `video_room_name` to the generated name.
    #    - Update `updated_at`.
    print(f"Placeholder: Updating appointment {appointment_id} status to 'confirmed' and setting video room.")
    #    db_confirm_appointment(appointment_id, video_room_name)

    # 6. Notification Logic:
    #    - Send a notification (email, SMS, push) to the patient about the confirmation.
    print(f"Placeholder: Sending confirmation notification for appointment {appointment_id} to patient.")
    # --- End of Placeholder for Database & Business Logic ---

    return jsonify({
        "status": "success",
        "message": "Appointment confirmed successfully.",
        "appointment_id": appointment_id,
        "new_status": "confirmed",
        "video_room_name": video_room_name
    }), 200


@app.route('/api/appointments/<int:appointment_id>/cancel', methods=['PUT'])
def cancel_appointment(appointment_id):
    """
    User (Patient/Provider): Cancel an appointment.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    cancelled_by_role = data.get('cancelled_by_role') # "patient" or "provider"
    reason = data.get('reason') # Optional

    if not cancelled_by_role or cancelled_by_role not in ['patient', 'provider']:
        return jsonify({"status": "error", "message": "Missing or invalid 'cancelled_by_role' (must be 'patient' or 'provider')"}), 400

    # --- Placeholder for Database & Business Logic ---
    # 1. Fetch the appointment by `appointment_id`.
    #    print(f"Placeholder: Fetching appointment {appointment_id} for cancellation.")
    #    appointment = db_get_appointment(appointment_id)
    #    if not appointment:
    //        return jsonify({"status": "error", "message": "Appointment not found"}), 404

    # 2. Authorization:
    #    - Get current user's ID and role from auth/session.
    #    - If `cancelled_by_role` is 'patient', verify current user ID matches `appointment.patient_id`.
    //    - If `cancelled_by_role` is 'provider', verify current user ID matches `appointment.provider_id`.
    #    print(f"Placeholder: Verifying user (role: {cancelled_by_role}) is authorized to cancel appointment {appointment_id}.")
    #    # if (cancelled_by_role == 'patient' and current_user_id != appointment.patient_id) or \
    #    #    (cancelled_by_role == 'provider' and current_user_id != appointment.provider_id):
    #    #     return jsonify({"status": "error", "message": "Forbidden"}), 403

    # 3. Validate if appointment can be cancelled (e.g., not already 'completed' or 'cancelled').
    #    print(f"Placeholder: Validating current status of appointment {appointment_id} for cancellation eligibility.")
    #    # if appointment.status in ['completed', 'cancelled_by_patient', 'cancelled_by_provider']:
    #    #     return jsonify({"status": "error", "message": f"Appointment cannot be cancelled. Current status: {appointment.status}"}), 409

    new_status = f"cancelled_by_{cancelled_by_role}"
    notes_field_to_update = 'notes_by_patient' if cancelled_by_role == 'patient' else 'notes_by_provider'

    # 4. Update appointment in 'appointments' table:
    #    - Set `status` to `new_status`.
    #    - If `reason` is provided, update `notes_by_patient` or `notes_by_provider`.
    #    - Update `updated_at`.
    print(f"Placeholder: Updating appointment {appointment_id} status to '{new_status}'. Reason: '{reason}' stored in {notes_field_to_update}.")
    #    db_cancel_appointment(appointment_id, new_status, reason, notes_field_to_update)

    # 5. Notification Logic:
    #    - Send a notification to the other party (patient or provider) about the cancellation.
    print(f"Placeholder: Sending cancellation notification for appointment {appointment_id}.")
    # --- End of Placeholder for Database & Business Logic ---

    return jsonify({
        "status": "success",
        "message": "Appointment cancelled successfully.",
        "appointment_id": appointment_id,
        "new_status": new_status
    }), 200


@app.route('/api/patients/<int:patient_id>/appointments', methods=['GET'])
def get_patient_appointments(patient_id):
    """
    Patient: Get their appointments, with optional filters.
    Query Params: status, date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)
    """
    status_filter = request.args.get('status')
    date_from_filter = request.args.get('date_from')
    date_to_filter = request.args.get('date_to')

    # --- Placeholder for Database Logic ---
    # 1. Verify patient_id matches authenticated user (from session/auth).
    #    print(f"Placeholder: Verifying patient {patient_id} for fetching their appointments.")
    # 2. Fetch appointments from 'appointments' table:
    #    - Filter by `patient_id`.
    #    - If `status_filter` is provided, filter by `status`.
    #    - If `date_from_filter` and/or `date_to_filter` are provided, filter by `appointment_start_time`.
    print(f"Placeholder: Fetching appointments for patient {patient_id} with filters: status='{status_filter}', from='{date_from_filter}', to='{date_to_filter}'")
    # Example: patient_appointments = db_fetch_patient_appointments(patient_id, status_filter, date_from_filter, date_to_filter)
    patient_appointments = [
        {"appointment_id": 789, "patient_id": patient_id, "provider_id": 10, "appointment_start_time": "2024-03-15 10:00:00", "appointment_end_time": "2024-03-15 10:30:00", "status": "pending_provider_confirmation", "reason_for_visit": "Checkup"},
        {"appointment_id": 791, "patient_id": patient_id, "provider_id": 12, "appointment_start_time": "2024-03-17 14:00:00", "appointment_end_time": "2024-03-17 14:30:00", "status": "confirmed", "reason_for_visit": "Consultation", "video_room_name": "RoomABC789"},
    ]
    # --- End of Placeholder for Database Logic ---

    return jsonify({"status": "success", "patient_id": patient_id, "appointments": patient_appointments}), 200
