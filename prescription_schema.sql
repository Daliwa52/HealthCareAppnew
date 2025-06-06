-- Assuming a users table exists with a primary key user_id (INT)
-- Example:
-- CREATE TABLE users (
--     user_id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(255) NOT NULL UNIQUE,
--     email VARCHAR(255) NOT NULL UNIQUE,
--     user_type VARCHAR(50) DEFAULT 'patient', -- e.g., 'patient', 'provider'
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- Assuming an appointments table exists with a primary key appointment_id (INT)
-- Example from previous schema:
-- CREATE TABLE appointments (
--     appointment_id INT AUTO_INCREMENT PRIMARY KEY,
--     patient_id INT NOT NULL,
--     provider_id INT NOT NULL,
--     appointment_start_time DATETIME NOT NULL,
--     appointment_end_time DATETIME NOT NULL,
--     status VARCHAR(50) NOT NULL DEFAULT 'pending_provider_confirmation',
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
--     FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
--     FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE,
--     CONSTRAINT chk_start_end_appointment CHECK (appointment_end_time > appointment_start_time)
-- );

-- Table definition for prescriptions
CREATE TABLE prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NULL, -- Can be NULL if prescription is not tied to a specific appointment
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    issue_date DATE NOT NULL DEFAULT (CURRENT_DATE), -- Or CURDATE() for MySQL
    notes_for_patient TEXT NULL,
    notes_for_pharmacist TEXT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- e.g., 'active', 'expired', 'cancelled', 'superseded', 'filled_once', 'filled_complete'
    pharmacy_details TEXT NULL, -- Could be JSON or plain text for simplicity
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    -- For PostgreSQL and some other SQL databases, ON UPDATE CURRENT_TIMESTAMP is not directly supported for DATETIME.
    -- You would typically use a trigger for `updated_at` as shown in previous examples.

    CONSTRAINT fk_prescription_appointment
        FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL, -- Set to NULL if appointment is deleted
    CONSTRAINT fk_prescription_patient
        FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_prescription_provider
        FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE -- Or ON DELETE SET NULL if provider can be deleted but prescriptions remain
);

-- Indexes for prescriptions table
CREATE INDEX idx_presc_patient_id ON prescriptions(patient_id);
CREATE INDEX idx_presc_provider_id ON prescriptions(provider_id);
CREATE INDEX idx_presc_appointment_id ON prescriptions(appointment_id);
CREATE INDEX idx_presc_issue_date ON prescriptions(issue_date);
CREATE INDEX idx_presc_status ON prescriptions(status);

-- Table definition for prescription_medications
CREATE TABLE prescription_medications (
    prescription_medication_id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medication_name VARCHAR(255) NOT NULL, -- In a more complex system, this might be a FK to a medications table
    dosage VARCHAR(100) NOT NULL, -- e.g., '1 tablet', '10mg', '5mL'
    frequency VARCHAR(100) NOT NULL, -- e.g., 'Once daily', 'Twice daily', 'Every 4-6 hours'
    duration VARCHAR(100) NULL, -- e.g., '7 days', '1 month', 'Until finished'
    quantity VARCHAR(100) NOT NULL, -- e.g., '30 tablets', '1 bottle (100mL)'
    refills_available INT NOT NULL DEFAULT 0,
    instructions TEXT NULL, -- Specific instructions for this medication, e.g., 'Take with food'
    is_prn BOOLEAN DEFAULT FALSE NOT NULL, -- "Pro Re Nata" or "as needed"

    CONSTRAINT fk_pm_prescription
        FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE -- If a prescription is deleted, its items are deleted
);

-- Indexes for prescription_medications table
CREATE INDEX idx_pm_prescription_id ON prescription_medications(prescription_id);
CREATE INDEX idx_pm_medication_name ON prescription_medications(medication_name); -- If frequently searching by medication name

-- Example statuses for prescriptions.status:
-- 'active': Currently valid and can be filled.
-- 'pending_provider_signature': Drafted, awaiting final sign-off (if e-signature workflow)
-- 'expired': Past its valid date or duration.
-- 'cancelled': Cancelled by provider or patient.
-- 'superseded': Replaced by a new prescription.
-- 'filled_once': Filled at least once (if tracking fills on the prescription itself)
-- 'filled_complete': All refills used or no refills and filled once.
-- 'on_hold_pharmacy': Pharmacy put a temporary hold.
-- 'on_hold_provider': Provider requested a temporary hold.
-- 'transferred_out': Prescription transferred to another pharmacy.
