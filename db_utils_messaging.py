import sqlite3
import datetime
import os # For potential future use, like managing DB file paths

# --- Database Schema (Adapted for SQLite) ---
MESSAGING_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant1_id INTEGER NOT NULL,
    participant2_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    updated_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    FOREIGN KEY (participant1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (participant2_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (participant1_id, participant2_id),
    CHECK (participant1_id < participant2_id) -- Ensures consistent ordering for UNIQUE constraint
);

CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now')) NOT NULL,
    content TEXT NOT NULL,
    is_read INTEGER DEFAULT 0 NOT NULL, -- SQLite uses 0 for False, 1 for True
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_participant1 ON conversations(participant1_id);
CREATE INDEX IF NOT EXISTS idx_conversations_participant2 ON conversations(participant2_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
"""

# --- Database Utility Functions ---

def get_db_connection(db_name='messaging_app.db'):
    """
    Establishes and returns an SQLite3 connection object.

    The connection is configured to:
    - Use `sqlite3.Row` as the row_factory for accessing columns by name.
    - Enable foreign key constraint enforcement (`PRAGMA foreign_keys = ON`).

    Args:
        db_name (str): The name of the SQLite database file.
                       Defaults to 'messaging_app.db'.

    Returns:
        sqlite3.Connection: The SQLite3 connection object.

    Raises:
        sqlite3.Error: If any error occurs during database connection.
    """
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraint enforcement
        return conn
    except sqlite3.Error as e:
        # Log or handle more gracefully if this were a library for others
        print(f"Database connection error to '{db_name}': {e}")
        raise # Re-raise the exception to be handled by the caller

def initialize_schema(conn: sqlite3.Connection):
    """
    Initializes the database schema using the MESSAGING_SCHEMA constant.

    This function creates the `users`, `conversations`, and `messages` tables
    if they do not already exist. It's intended for setting up the database
    for development or testing.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.

    Raises:
        sqlite3.Error: If any error occurs during schema execution, and rolls back changes.
    """
    try:
        cursor = conn.cursor()
        cursor.executescript(MESSAGING_SCHEMA)
        conn.commit()
        print("Database schema initialized successfully.")
    except sqlite3.Error as e:
        print(f"Schema initialization error: {e}")
        conn.rollback() # Rollback changes if any error occurs
        raise

def find_or_create_conversation(conn: sqlite3.Connection, participant1_id: int, participant2_id: int) -> int:
    """
    Finds an existing conversation between two participants or creates a new one.

    To ensure uniqueness and consistent lookup, the participant IDs are always
    stored in a specific order (smaller ID first) due to the CHECK constraint
    `participant1_id < participant2_id` and `UNIQUE (participant1_id, participant2_id)`
    in the `conversations` table schema.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.
        participant1_id (int): The user ID of the first participant.
        participant2_id (int): The user ID of the second participant.

    Returns:
        int: The conversation_id of the found or newly created conversation.

    Raises:
        ValueError: If participant IDs are not integers or are the same.
        sqlite3.Error: If a database error occurs (e.g., IntegrityError if CHECK constraint fails,
                       or other operational errors), or if a new conversation ID cannot be retrieved.
    """
    if not isinstance(participant1_id, int) or not isinstance(participant2_id, int):
        raise ValueError("Participant IDs must be integers.")
    if participant1_id == participant2_id:
        raise ValueError("Participants cannot be the same user.")

    # Ensure consistent order of participants for unique constraint and lookup
    p1 = min(participant1_id, participant2_id)
    p2 = max(participant1_id, participant2_id)

    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()

    try:
        # Check if conversation already exists
        cursor.execute(
            "SELECT conversation_id FROM conversations WHERE participant1_id = ? AND participant2_id = ?",
            (p1, p2)
        )
        row = cursor.fetchone()

        if row:
            conversation_id = row['conversation_id']
            # print(f"Found existing conversation: {conversation_id}") # For debugging
            return conversation_id
        else:
            # Create new conversation if it doesn't exist
            # The CHECK constraint (p1 < p2) is handled by ordering p1 and p2 above.
            cursor.execute(
                """
                INSERT INTO conversations (participant1_id, participant2_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (p1, p2, current_timestamp, current_timestamp)
            )
            conn.commit() # Commit the new conversation
            new_conversation_id = cursor.lastrowid
            # print(f"Created new conversation: {new_conversation_id}") # For debugging
            if new_conversation_id is None: # Should not happen with AUTOINCREMENT if insert was successful
                 raise sqlite3.Error("Failed to retrieve lastrowid for new conversation after insert.")
            return new_conversation_id
    except sqlite3.Error as e: # Catches IntegrityError (like CHECK fail) and other DB errors
        print(f"Error in find_or_create_conversation for participants {p1}, {p2}: {e}")
        conn.rollback() # Rollback on error
        raise

def create_message(conn: sqlite3.Connection, conversation_id: int, sender_id: int, content: str) -> int:
    """
    Inserts a new message into the messages table and updates the conversation's timestamp.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.
        conversation_id (int): The ID of the conversation this message belongs to.
        sender_id (int): The user ID of the message sender.
        content (str): The text content of the message.

    Returns:
        int: The message_id of the newly created message.

    Raises:
        ValueError: If conversation_id or sender_id are not integers, or if content is empty/whitespace.
        sqlite3.Error: If a database error occurs (e.g., IntegrityError for foreign keys),
                       or if a new message ID cannot be retrieved.
    """
    if not isinstance(conversation_id, int) or not isinstance(sender_id, int):
        raise ValueError("conversation_id and sender_id must be integers.")
    if not isinstance(content, str) or not content.strip(): # Check if content is empty or just whitespace
        raise ValueError("Content must be a non-empty string.")

    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    try:
        # Insert the new message
        cursor.execute(
            """
            INSERT INTO messages (conversation_id, sender_id, content, timestamp, is_read)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, sender_id, content, current_timestamp, 0) # is_read defaults to 0 (False)
        )
        new_message_id = cursor.lastrowid # Get the ID of the inserted message
        if new_message_id is None:
            # This case should ideally not be reached if the insert was successful due to AUTOINCREMENT.
            # However, good to have a check.
            raise sqlite3.Error("Failed to retrieve lastrowid for new message after insert.")

        # After successfully inserting a message, update the conversation's updated_at timestamp.
        # This also handles committing the transaction for both the message insert and conversation update.
        update_conversation_timestamp(conn, conversation_id)

        # print(f"Created new message: {new_message_id} in conversation {conversation_id}") # For debugging
        return new_message_id
    except sqlite3.Error as e: # Catches IntegrityError (FK violations) and other DB errors
        print(f"Error in create_message for conversation {conversation_id}: {e}")
        conn.rollback() # Rollback on error
        raise

def update_conversation_timestamp(conn: sqlite3.Connection, conversation_id: int):
    """
    Updates the 'updated_at' field of the specified conversation to the current timestamp.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.
        conversation_id (int): The ID of the conversation to update.

    Raises:
        ValueError: If conversation_id is not an integer.
        sqlite3.Error: If a database error occurs during the update.
    """
    if not isinstance(conversation_id, int):
        raise ValueError("conversation_id must be an integer.")

    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (current_timestamp, conversation_id)
        )
        conn.commit() # Commit the timestamp update
        # print(f"Updated conversation {conversation_id} timestamp to {current_timestamp}") # For debugging
    except sqlite3.Error as e:
        print(f"Error in update_conversation_timestamp for conversation {conversation_id}: {e}")
        conn.rollback() # Rollback on error
        raise

# --- Read Operations ---

def get_messages_by_conversation_id(conn: sqlite3.Connection, conversation_id: int) -> list[dict]:
    """
    Retrieves all messages for a given conversation_id, ordered by timestamp (oldest first).

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.
        conversation_id (int): The ID of the conversation whose messages are to be fetched.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a message
                    (containing 'message_id', 'conversation_id', 'sender_id', 'content',
                    'timestamp', 'is_read'). Returns an empty list if no messages are found
                    or if a database error occurs.

    Raises:
        ValueError: If conversation_id is not an integer.
    """
    if not isinstance(conversation_id, int):
        raise ValueError("conversation_id must be an integer.")

    messages = []
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT message_id, conversation_id, sender_id, content, timestamp, is_read
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
            """,
            (conversation_id,)
        )
        # Convert each row (which is a sqlite3.Row object due to row_factory) to a dictionary
        for row in cursor.fetchall():
            messages.append(dict(row))
        return messages
    except sqlite3.Error as e:
        print(f"Error in get_messages_by_conversation_id for conversation {conversation_id}: {e}")
        return [] # Return empty list on error, consistent with previous behavior

def get_conversations_by_user_id(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    """
    Retrieves all conversations for a given user_id, enriched with details of the
    other participant and the last message exchanged.

    Conversations are ordered by their last update time (most recent first).

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.
        user_id (int): The ID of the user whose conversations are to be fetched.

    Returns:
        list[dict]: A list of dictionaries, each representing a conversation summary.
                    Each summary includes: 'conversation_id', 'participant1_id', 'participant2_id',
                    'other_participant_id', 'other_participant_username', 'last_message_content',
                    'last_message_timestamp', 'conversation_updated_at'.
                    Returns an empty list if the user has no conversations or on database error.

    Raises:
        ValueError: If user_id is not an integer.
    """
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer.")

    conversations_data = []
    cursor = conn.cursor()
    try:
        # This SQL query uses a Common Table Expression (CTE) `LastMessagePerConversation`
        # to efficiently find the last message for each conversation using ROW_NUMBER().
        # It then joins this with conversation and user details to construct the summary.
        # SQLite versions 3.25.0 and newer support window functions.
        query = """
        WITH LastMessagePerConversation AS (
            SELECT
                m.conversation_id,
                m.content AS last_message_content,
                m.timestamp AS last_message_timestamp,
                -- Assign a row number to each message within its conversation, ordered by time (newest is 1)
                ROW_NUMBER() OVER(PARTITION BY m.conversation_id ORDER BY m.timestamp DESC) as rn
            FROM messages m
        )
        SELECT
            c.conversation_id,
            c.participant1_id,
            c.participant2_id,
            -- Determine the other participant's ID relative to the current user_id
            CASE
                WHEN c.participant1_id = :user_id THEN c.participant2_id
                ELSE c.participant1_id
            END AS other_participant_id,
            -- Get the other participant's username by joining with the users table
            u_other.username AS other_participant_username,
            lmpc.last_message_content,
            lmpc.last_message_timestamp,
            c.updated_at AS conversation_updated_at -- This is the primary sort key for conversations
        FROM conversations c
        -- Join with users table to get the username of the other participant
        JOIN users u_other ON u_other.user_id = (
            CASE
                WHEN c.participant1_id = :user_id THEN c.participant2_id
                ELSE c.participant1_id
            END
        )
        -- Left join to get the last message details; only keep the one ranked as newest (rn=1)
        LEFT JOIN LastMessagePerConversation lmpc ON c.conversation_id = lmpc.conversation_id AND lmpc.rn = 1
        -- Filter conversations to include only those where the given user_id is a participant
        WHERE c.participant1_id = :user_id OR c.participant2_id = :user_id
        -- Order conversations by their last update time (most recent first)
        ORDER BY c.updated_at DESC;
        """
        # Using named placeholders for clarity with multiple uses of user_id
        cursor.execute(query, {"user_id": user_id})

        for row in cursor.fetchall():
            conversations_data.append(dict(row))
        return conversations_data
    except sqlite3.Error as e:
        print(f"Error in get_conversations_by_user_id for user {user_id}: {e}")
        return [] # Return empty list on error

def get_conversation_by_id(conn: sqlite3.Connection, conversation_id: int) -> dict | None:
    """
    Retrieves a specific conversation by its ID.

    Args:
        conn (sqlite3.Connection): An active SQLite3 connection object.
        conversation_id (int): The ID of the conversation to retrieve.

    Returns:
        dict | None: A dictionary representing the conversation (including 'conversation_id',
                      'participant1_id', 'participant2_id', 'created_at', 'updated_at')
                      if found, otherwise None. Returns None on database error as well.

    Raises:
        ValueError: If conversation_id is not an integer.
    """
    if not isinstance(conversation_id, int):
        raise ValueError("conversation_id must be an integer.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT conversation_id, participant1_id, participant2_id, created_at, updated_at FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error in get_conversation_by_id for conversation {conversation_id}: {e}")
        return None # Return None on error


if __name__ == '__main__':
    # This section provides an example of how to use the utility functions.
    # It's useful for direct testing of this module.
    # For integration tests with the API, see test_integration_messaging.py.

    db_file = 'test_messaging_utils.db' # Use a dedicated test DB file for this example

    # Clean slate for example run: remove DB if it exists
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = get_db_connection(db_file)

    print(f"\nInitializing schema in {db_file}...")
    initialize_schema(conn)

    try:
        print("\n--- Example Usage ---")
        print("Creating dummy users...")
        cursor = conn.cursor()
        user_ids = {}
        # Using INSERT OR IGNORE to make the example runnable multiple times without error if users exist
        for username_val in ['util_user1', 'util_user2', 'util_user3', 'util_user4_no_conv']:
            try:
                cursor.execute("INSERT INTO users (username) VALUES (?)", (username_val,))
                user_ids[username_val] = cursor.lastrowid
            except sqlite3.IntegrityError: # If user already exists from a previous partial run
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username_val,))
                user_ids[username_val] = cursor.fetchone()['user_id']
        conn.commit()

        u1_id, u2_id, u3_id, u4_id = user_ids['util_user1'], user_ids['util_user2'], user_ids['util_user3'], user_ids['util_user4_no_conv']
        print(f"User IDs: util_user1={u1_id}, util_user2={u2_id}, util_user3={u3_id}, util_user4_no_conv={u4_id}")

        if not all([u1_id, u2_id, u3_id, u4_id]): # Basic check
            raise Exception("Failed to create or fetch user IDs for testing example.")

        print("\nFinding/Creating conversations...")
        c1_id = find_or_create_conversation(conn, u1_id, u2_id)
        print(f"Conversation between User1 & User2: ID {c1_id}")
        c1_again_id = find_or_create_conversation(conn, u2_id, u1_id) # Should be the same
        assert c1_id == c1_again_id, "Error: Same participants should yield same conversation ID."

        c2_id = find_or_create_conversation(conn, u1_id, u3_id)
        print(f"Conversation between User1 & User3: ID {c2_id}")
        assert c1_id != c2_id, "Error: Different participant pairs should have different conversation IDs."

        print("\nCreating messages...")
        msg1_c1_id = create_message(conn, c1_id, u1_id, "Hello from User1 to User2 (Conv1)")
        print(f"Message ID {msg1_c1_id} in Conv1 from User1.")

        # Adding a small delay to ensure timestamps are different for ordering tests
        if hasattr(time, 'sleep'): time.sleep(0.01)
        else: import time; time.sleep(0.01)

        msg2_c1_id = create_message(conn, c1_id, u2_id, "Reply from User2 to User1 (Conv1)")
        print(f"Message ID {msg2_c1_id} in Conv1 from User2.")

        if hasattr(time, 'sleep'): time.sleep(0.01)
        else: import time; time.sleep(0.01)

        msg3_c2_id = create_message(conn, c2_id, u1_id, "Hello from User1 to User3 (Conv2)")
        print(f"Message ID {msg3_c2_id} in Conv2 from User1.")

        print(f"\nGetting messages for Conversation ID {c1_id}:")
        messages_in_c1 = get_messages_by_conversation_id(conn, c1_id)
        for msg in messages_in_c1:
            print(f"  MsgID: {msg['message_id']}, Sender: {msg['sender_id']}, Content: '{msg['content']}', Time: {msg['timestamp']}")
        assert len(messages_in_c1) == 2, "Error: Expected 2 messages in Conversation 1."

        print(f"\nGetting conversations for User ID {u1_id} (util_user1):")
        convos_for_u1 = get_conversations_by_user_id(conn, u1_id)
        for convo in convos_for_u1:
            print(f"  ConvID: {convo['conversation_id']}, Other User: {convo['other_participant_username']} (ID: {convo['other_participant_id']}), Last Msg: '{convo.get('last_message_content', 'N/A')}' at {convo.get('last_message_timestamp', 'N/A')}, Updated: {convo['conversation_updated_at']}")
        assert len(convos_for_u1) == 2, "Error: Expected 2 conversations for User 1."
        # Check if convos are ordered by updated_at (c1 should be more recent due to msg2_c1_id)
        assert convos_for_u1[0]['conversation_id'] == c1_id, "Error: Conversations not ordered by updated_at correctly."
        assert convos_for_u1[0]['last_message_content'] == "Reply from User2 to User1 (Conv1)"

        print(f"\nGetting specific conversation by ID {c2_id}:")
        convo_c2_details = get_conversation_by_id(conn, c2_id)
        print(f"  Details for ConvID {c2_id}: {dict(convo_c2_details) if convo_c2_details else 'Not Found'}")
        assert convo_c2_details and convo_c2_details['conversation_id'] == c2_id

        print(f"\nGetting conversations for User ID {u4_id} (util_user4_no_conv) - expecting none:")
        convos_for_u4 = get_conversations_by_user_id(conn, u4_id)
        print(f"  Conversations for User4: {convos_for_u4}")
        assert len(convos_for_u4) == 0, "Error: Expected 0 conversations for User 4."

        print("\nExample usage completed successfully.")

    except ValueError as ve:
        print(f"ValueError in example usage: {ve}")
    except sqlite3.Error as e:
        print(f"An SQLite error occurred in example usage: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred in example usage: {ex}")
    finally:
        if conn:
            conn.close()
            print(f"\nClosed connection to {db_file}.")
            # Clean up the test database file after example run
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"Removed test database {db_file}.")
