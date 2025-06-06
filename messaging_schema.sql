-- Assuming a users table exists with a primary key user_id
-- CREATE TABLE users (
-- user_id INT AUTO_INCREMENT PRIMARY KEY,
-- username VARCHAR(255) NOT NULL UNIQUE,
-- email VARCHAR(255) NOT NULL UNIQUE,
-- created_at DATETIME DEFAULT CURRENT_TIMESTAMP
-- );

-- Table definition for conversations
CREATE TABLE conversations (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    participant1_id INT NOT NULL,
    participant2_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (participant1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (participant2_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for conversations table
CREATE INDEX idx_conversations_participant1 ON conversations(participant1_id);
CREATE INDEX idx_conversations_participant2 ON conversations(participant2_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);

-- Table definition for messages
CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for messages table
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_is_read ON messages(is_read);

-- Note: The updated_at column in the conversations table would typically be
-- updated using a trigger when a new message is inserted, or by application logic.
-- Example Trigger for MySQL:
--
-- DELIMITER $$
-- CREATE TRIGGER trg_update_conversation_timestamp
-- AFTER INSERT ON messages
-- FOR EACH ROW
-- BEGIN
--    UPDATE conversations
--    SET updated_at = CURRENT_TIMESTAMP
--    WHERE conversation_id = NEW.conversation_id;
-- END$$
-- DELIMITER ;
--
-- For other SQL databases, the trigger syntax might vary.
-- Alternatively, the application inserting the message should also update the
-- corresponding conversation's updated_at field.
