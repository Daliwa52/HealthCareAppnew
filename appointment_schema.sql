-- Assuming a users table exists with a primary key user_id (INT)
-- Example:
-- CREATE TABLE users (
--     user_id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(255) NOT NULL UNIQUE,
--     email VARCHAR(255) NOT NULL UNIQUE,
--     user_type VARCHAR(50) DEFAULT 'patient', -- e.g., 'patient', 'provider'
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- Table definition for provider_availability
CREATE TABLE provider_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    recurring_rule VARCHAR(255) NULL, -- For iCalendar RRULE string e.g., FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20241231T235959Z
    CONSTRAINT fk_provider_availability_provider
        FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_start_end_availability CHECK (end_datetime > start_datetime)
);

-- Indexes for provider_availability table
CREATE INDEX idx_pa_provider_id ON provider_availability(provider_id);
CREATE INDEX idx_pa_start_datetime ON provider_availability(start_datetime);
CREATE INDEX idx_pa_end_datetime ON provider_availability(end_datetime);

-- Table definition for appointments
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    appointment_start_time DATETIME NOT NULL,
    appointment_end_time DATETIME NOT NULL,
    reason_for_visit TEXT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_provider_confirmation', -- e.g., 'pending_provider_confirmation', 'confirmed', 'cancelled_by_patient', 'cancelled_by_provider', 'completed', 'rescheduled_by_provider', 'rescheduled_by_patient'
    video_room_name VARCHAR(255) NULL,
    notes_by_patient TEXT NULL,
    notes_by_provider TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    -- For PostgreSQL and some other SQL databases, ON UPDATE CURRENT_TIMESTAMP is not directly supported for DATETIME.
    -- You would typically use a trigger for `updated_at`:
    -- CREATE OR REPLACE FUNCTION update_updated_at_column()
    -- RETURNS TRIGGER AS $$
    -- BEGIN
    //    NEW.updated_at = NOW();
    --    RETURN NEW;
    -- END;
    -- $$ LANGUAGE plpgsql;
    -- CREATE TRIGGER trg_appointments_updated_at
    -- BEFORE UPDATE ON appointments
    -- FOR EACH ROW
    -- EXECUTE FUNCTION update_updated_at_column();

    CONSTRAINT fk_appointments_patient
        FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_appointments_provider
        FOREIGN KEY (provider_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_start_end_appointment CHECK (appointment_end_time > appointment_start_time)
    -- Consider adding a UNIQUE constraint if a provider cannot have overlapping confirmed appointments:
    -- CONSTRAINT uq_provider_time_confirmed UNIQUE (provider_id, appointment_start_time, status) WHERE status = 'confirmed'
    -- The exact syntax for partial unique constraints can vary by SQL dialect.
    -- For MySQL, you might need a more complex solution or handle this at the application layer or with triggers.
);

-- Indexes for appointments table
CREATE INDEX idx_appt_patient_id ON appointments(patient_id);
CREATE INDEX idx_appt_provider_id ON appointments(provider_id);
CREATE INDEX idx_appt_start_time ON appointments(appointment_start_time);
CREATE INDEX idx_appt_status ON appointments(status);
CREATE INDEX idx_appt_video_room_name ON appointments(video_room_name); -- If frequently queried
CREATE INDEX idx_appt_created_at ON appointments(created_at);
CREATE INDEX idx_appt_updated_at ON appointments(updated_at);

-- Possible statuses for appointments.status:
-- 'pending_provider_confirmation': Patient requested, provider needs to confirm.
-- 'confirmed': Provider confirmed.
-- 'cancelled_by_patient': Patient cancelled.
-- 'cancelled_by_provider': Provider cancelled.
-- 'completed': Appointment finished.
-- 'rescheduled_pending_patient': Provider proposed reschedule, patient needs to confirm.
-- 'rescheduled_pending_provider': Patient proposed reschedule, provider needs to confirm.
-- 'no_show_patient': Patient did not attend.
-- 'no_show_provider': Provider did not attend (less common, but possible).
