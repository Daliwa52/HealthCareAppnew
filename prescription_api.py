from flask import Flask, request, jsonify
from datetime import date # For handling dates

app = Flask(__name__)

# In a real application, you would configure your database connection here
# For example, using Flask-SQLAlchemy or another ORM/DB connector
# from flask_sqlalchemy import SQLAlchemy
# app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri_for_prescriptions'
# db = SQLAlchemy(app)

# --- Helper Functions (Placeholders) ---
def validate_medication_item(med_item):
    """Basic validation for a medication item in the request."""
    required_fields = ['medication_name', 'dosage', 'frequency', 'quantity']
    for field in required_fields:
        if not med_item.get(field):
            return False, f"Missing required field in medication: {field}"
    return True, ""

# --- Prescription Endpoints ---

@app.route('/api/prescriptions', methods=['POST'])
def create_prescription():
    """
    Provider: Create a new prescription with its medications.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    # Extract data for prescriptions table
    # In a real app, provider_id would come from the authenticated session/token.
    provider_id = data.get('provider_id') # Assuming this is passed for now, or derived from auth
    patient_id = data.get('patient_id')
    appointment_id = data.get('appointment_id') # Optional
    issue_date_str = data.get('issue_date', date.today().isoformat()) # Default to today if not provided
    notes_for_patient = data.get('notes_for_patient')
    notes_for_pharmacist = data.get('notes_for_pharmacist')
    status = data.get('status', 'active') # Default to 'active'
    pharmacy_details = data.get('pharmacy_details')
    medications_data = data.get('medications')

    # Basic Validation
    if not patient_id or not provider_id: # provider_id would be from auth
        return jsonify({"status": "error", "message": "Missing patient_id or provider_id"}), 400
    if not medications_data or not isinstance(medications_data, list) or not medications_data:
        return jsonify({"status": "error", "message": "Medications list is required and cannot be empty."}), 400

    for med_item in medications_data:
        is_valid, error_msg = validate_medication_item(med_item)
        if not is_valid:
            return jsonify({"status": "error", "message": error_msg}), 400

    try:
        issue_date = date.fromisoformat(issue_date_str)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid issue_date format. Use YYYY-MM-DD."}), 400


    # --- Placeholder for Database Logic (Transaction needed) ---
    # db_connection = db.session() # Example with SQLAlchemy
    try:
        print("Placeholder: Starting database transaction.")
        # 1. Authorization: Verify authenticated user is the provider_id and allowed to prescribe for patient_id.
        #    print(f"Placeholder: Authorizing provider {provider_id} for patient {patient_id}.")

        # 2. Save to `prescriptions` table
        #    prescription_record = { 'patient_id': patient_id, 'provider_id': provider_id, ... }
        #    new_prescription_id = db_insert_prescription(prescription_record) # Returns new ID
        new_prescription_id = 901 # Dummy ID
        print(f"Placeholder: Saved to prescriptions table. New prescription_id: {new_prescription_id}")

        # 3. Iterate through `medications` list and save each to `prescription_medications` table
        saved_medications_ids = []
        for med_item in medications_data:
            # medication_record = { 'prescription_id': new_prescription_id, ...med_item }
            # new_med_id = db_insert_prescription_medication(medication_record)
            # saved_medications_ids.append(new_med_id)
            saved_medications_ids.append( (med_item.get("medication_name"), len(saved_medications_ids) + 5000) ) # Dummy med IDs
            print(f"Placeholder: Saved medication '{med_item.get('medication_name')}' for prescription {new_prescription_id}.")

        # 4. Commit the transaction
        #    db_connection.commit()
        print("Placeholder: Database transaction committed.")

    except Exception as e:
        # db_connection.rollback()
        print(f"Placeholder: Database transaction rolled back due to error: {e}")
        return jsonify({"status": "error", "message": f"Failed to create prescription: {str(e)}"}), 500
    # finally:
    #    db_connection.close()
    # --- End of Placeholder for Database Logic ---

    return jsonify({
        "status": "success",
        "message": "Prescription created successfully.",
        "prescription_id": new_prescription_id,
        "medications_count": len(saved_medications_ids)
    }), 201


@app.route('/api/prescriptions/<int:prescription_id>', methods=['GET'])
def get_prescription_details(prescription_id):
    """
    User (Provider/Patient): Get specific prescription details including medications.
    """
    # --- Placeholder for Database & Authorization Logic ---
    # 1. Fetch the prescription from `prescriptions` table by `prescription_id`.
    #    print(f"Placeholder: Fetching prescription {prescription_id} from DB.")
    #    prescription = db_get_prescription(prescription_id)
    #    if not prescription:
    #        return jsonify({"status": "error", "message": "Prescription not found"}), 404
    prescription_details_from_db = { # Simulated DB result
        "prescription_id": prescription_id, "appointment_id": 789, "patient_id": 123, "provider_id": 456,
        "issue_date": "2024-03-01", "notes_for_patient": "Take with food.", "status": "active",
        "created_at": "2024-03-01 10:00:00", "updated_at": "2024-03-01 10:00:00"
    }
    if not prescription_details_from_db: # Simulate not found
         return jsonify({"status": "error", "message": "Prescription not found"}), 404


    # 2. Authorization:
    #    - Get current authenticated user's ID and role (e.g., from session/token).
    #    - Verify if current user is `prescription.patient_id` OR `prescription.provider_id`
    #      OR has other roles (e.g., pharmacist, admin) that grant access.
    #    current_user_id = ... # from auth
    #    current_user_role = ... # from auth
    #    if not (current_user_id == prescription_details_from_db['patient_id'] or \
    #            current_user_id == prescription_details_from_db['provider_id'] or \
    #            current_user_role == 'admin'):
    #        return jsonify({"status": "error", "message": "Forbidden"}), 403
    print(f"Placeholder: Authorizing user to view prescription {prescription_id}.")


    # 3. Fetch associated medications from `prescription_medications` table for this `prescription_id`.
    #    print(f"Placeholder: Fetching medications for prescription {prescription_id}.")
    #    medications_list = db_get_medications_for_prescription(prescription_id)
    medications_list_from_db = [ # Simulated DB result
        {"medication_name": "Amoxicillin", "dosage": "250mg", "frequency": "Every 8 hours", "quantity": "21 tablets"},
        {"medication_name": "Ibuprofen", "dosage": "200mg", "frequency": "As needed", "quantity": "30 tablets", "is_prn": True}
    ]

    # Combine into a single response object
    full_prescription_details = {**prescription_details_from_db, "medications": medications_list_from_db}
    # --- End of Placeholder for Database & Authorization Logic ---

    return jsonify({"status": "success", "prescription": full_prescription_details}), 200


@app.route('/api/patients/<int:patient_id>/prescriptions', methods=['GET'])
def get_patient_prescriptions(patient_id):
    """
    Patient: Get a list of their prescriptions.
    Could add query params for filtering by status, date range, etc.
    """
    # --- Placeholder for Database & Authorization Logic ---
    # 1. Authorization:
    #    - Get current authenticated user's ID and role.
    #    - Verify if current user ID matches `patient_id` OR if user is an authorized provider/admin for this patient.
    #    current_user_id = ... # from auth
    #    if not (current_user_id == patient_id or user_is_authorized_provider_for_patient(current_user_id, patient_id)):
    #        return jsonify({"status": "error", "message": "Forbidden"}), 403
    print(f"Placeholder: Authorizing user to view prescriptions for patient {patient_id}.")

    # 2. Fetch all prescriptions for the given `patient_id` from `prescriptions` table.
    #    - May include basic medication summary or just prescription-level details.
    #    - For full details of each, client might need to call /api/prescriptions/<id> per item if data is large.
    #    print(f"Placeholder: Fetching all prescriptions for patient {patient_id}.")
    #    patient_prescriptions_list = db_get_prescriptions_for_patient(patient_id, request.args) # request.args for filters
    patient_prescriptions_list_from_db = [ # Simulated DB result (summary view)
        {"prescription_id": 901, "provider_id": 456, "issue_date": "2024-03-01", "status": "active", "medication_summary": "Amoxicillin, Ibuprofen"},
        {"prescription_id": 875, "provider_id": 456, "issue_date": "2024-01-15", "status": "expired", "medication_summary": "Lisinopril"},
    ]
    # --- End of Placeholder for Database & Authorization Logic ---

    if not patient_prescriptions_list_from_db:
        return jsonify({"status": "success", "patient_id": patient_id, "prescriptions": []}), 200

    return jsonify({"status": "success", "patient_id": patient_id, "prescriptions": patient_prescriptions_list_from_db}), 200


if __name__ == '__main__':
    # For development only. Use a WSGI server in production.
    app.run(debug=True, port=5003) # Using a different port


@app.route('/api/prescriptions/<int:prescription_id>/cancel', methods=['PUT'])
def cancel_prescription(prescription_id):
    """
    Provider: Cancel a prescription.
    """
    data = request.get_json()
    reason = data.get('reason', '') if data else '' # Optional reason from payload

    # --- Placeholder for Database & Authorization Logic ---
    # 1. Fetch the prescription by `prescription_id`.
    #    print(f"Placeholder: Fetching prescription {prescription_id} for cancellation.")
    #    prescription = db_get_prescription(prescription_id) # Assume this returns a dict or an object
    #    if not prescription:
    #        return jsonify({"status": "error", "message": "Prescription not found"}), 404
    simulated_prescription = { # Simulate a fetched prescription
        "prescription_id": prescription_id,
        "provider_id": 456, # The ID of the provider who issued it
        "status": "active"
    }
    if not simulated_prescription: # Should be based on actual DB fetch
        return jsonify({"status": "error", "message": "Prescription not found"}), 404

    # 2. Authorization:
    #    - Get current authenticated provider's ID (e.g., from session/token).
    #    acting_provider_id = get_current_provider_id_from_auth() # Placeholder function
    acting_provider_id = 456 # Simulated for placeholder
    #    - Verify if `acting_provider_id` matches `prescription.provider_id` or if user has admin/supervisory rights.
    #    if acting_provider_id != simulated_prescription['provider_id'] and not user_has_cancel_override_rights(acting_provider_id):
    #        return jsonify({"status": "error", "message": "Forbidden: You do not have permission to cancel this prescription."}), 403
    print(f"Placeholder: Authorizing provider {acting_provider_id} to cancel prescription {prescription_id} issued by {simulated_prescription['provider_id']}.")


    # 3. Validate if the prescription can be cancelled.
    #    - E.g., cannot cancel if status is already 'filled_complete', 'expired', 'cancelled'.
    #    - This might be complex without real-time pharmacy integration. For now, a basic check.
    #    if simulated_prescription['status'] in ['cancelled', 'expired', 'filled_complete', 'superseded']:
    #        return jsonify({"status": "error", "message": f"Prescription cannot be cancelled. Current status: {simulated_prescription['status']}"}), 409
    print(f"Placeholder: Validating current status '{simulated_prescription['status']}' of prescription {prescription_id} for cancellation eligibility.")


    # 4. Update the prescription `status` to `cancelled`.
    #    - The reason could be stored in `notes_for_pharmacist` or a dedicated `cancellation_reason` field if added to schema.
    #    - Let's assume we add it to `notes_for_pharmacist` prefixed.
    #    updated_notes_for_pharmacist = f"Cancelled by provider. Reason: {reason}. (Original notes: {prescription.get('notes_for_pharmacist','')})"
    #    db_update_prescription_status(prescription_id, 'cancelled', notes_for_pharmacist=updated_notes_for_pharmacist)
    new_status = 'cancelled'
    print(f"Placeholder: Updating prescription {prescription_id} status to '{new_status}'. Reason: '{reason}'.")

    # 5. Notification Logic (Potentially):
    #    - Notify the patient.
    #    - Notify the pharmacy if `pharmacy_details` are present and a notification system exists.
    #    print(f"Placeholder: Sending cancellation notification for prescription {prescription_id} to patient and pharmacy (if applicable).")
    # --- End of Placeholder for Database & Authorization Logic ---

    return jsonify({
        "status": "success",
        "message": f"Prescription {prescription_id} cancelled successfully.",
        "prescription_id": prescription_id,
        "new_status": new_status
    }), 200
