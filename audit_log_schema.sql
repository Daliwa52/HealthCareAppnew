-- Assuming a users table exists with a primary key user_id (INT)
-- Example:
-- CREATE TABLE users (
--     user_id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(255) NOT NULL UNIQUE,
--     email VARCHAR(255) NOT NULL UNIQUE,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- Table definition for audit_log
CREATE TABLE audit_log (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), -- High precision timestamp
    user_id INT NULL, -- Nullable as some system events might not be tied to a specific user
    action VARCHAR(255) NOT NULL, -- e.g., 'LOGIN_SUCCESS', 'VIEW_PATIENT_RECORD', 'CREATE_APPOINTMENT'
    target_resource_type VARCHAR(100) NULL, -- e.g., 'PATIENT', 'APPOINTMENT', 'PRESCRIPTION', 'MESSAGE_CONVERSATION'
    target_resource_id VARCHAR(255) NULL, -- ID of the resource being affected/accessed (VARCHAR to accommodate various ID types like INT or UUID)
    ip_address VARCHAR(45) NULL, -- To store IPv4 or IPv6 addresses
    user_agent TEXT NULL, -- Information about the client (browser, mobile app)
    status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS', -- e.g., 'SUCCESS', 'FAILURE', 'ATTEMPT', 'PENDING'
    details JSON NULL, -- For storing additional contextual information. Use TEXT if JSON type is not supported.
                       -- Example for TEXT: Store as a JSON string '{"param1": "value1", "changed_fields": ["status", "notes"]}'

    CONSTRAINT fk_audit_log_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL -- If user is deleted, keep log but nullify user_id
);

-- Notes on JSON type:
-- - MySQL 5.7.8+ supports JSON type.
-- - PostgreSQL supports JSON and JSONB types.
-- - SQL Server 2016+ has JSON support using NVARCHAR(MAX) with JSON functions.
-- - SQLite does not have a native JSON type; TEXT would be used with JSON functions in the application.
-- If using TEXT, ensure your application serializes/deserializes the JSON string.

-- Indexes for audit_log table
CREATE INDEX idx_al_timestamp ON audit_log(timestamp);
CREATE INDEX idx_al_user_id ON audit_log(user_id);
CREATE INDEX idx_al_action ON audit_log(action);
CREATE INDEX idx_al_target_resource_type ON audit_log(target_resource_type);
CREATE INDEX idx_al_target_resource_id ON audit_log(target_resource_id);
CREATE INDEX idx_al_status ON audit_log(status); -- If filtering by status is common

-- Example actions:
-- 'USER_LOGIN_SUCCESS', 'USER_LOGIN_FAILURE', 'USER_LOGOUT'
-- 'VIEW_RESOURCE', 'CREATE_RESOURCE', 'UPDATE_RESOURCE', 'DELETE_RESOURCE' (where RESOURCE is replaced by entity like APPOINTMENT)
-- 'PATIENT_RECORD_ACCESSED', 'PRESCRIPTION_PRINTED', 'MESSAGE_SENT'
-- 'SECURITY_SETTINGS_CHANGED', 'USER_ROLE_UPDATED'
-- 'SYSTEM_HEALTH_CHECK_FAIL', 'BACKGROUND_JOB_COMPLETED'
