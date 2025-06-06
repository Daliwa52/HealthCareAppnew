from flask import Flask, request, jsonify
import sqlite3 # For handling database specific errors
import os # For environment variable access
from db_utils_messaging import (
    get_db_connection,
    initialize_schema,
    find_or_create_conversation,
    create_message,
    get_conversations_by_user_id,
    get_messages_by_conversation_id,
    get_conversation_by_id # For authorization check
)

app = Flask(__name__)
# Define DB name, configurable via environment variable
DB_NAME = os.getenv('MESSAGING_DB_NAME', 'messaging_app.db')


@app.route('/api/messages', methods=['POST'])
def send_message():
    """
    Send a new message from one user to another.

    This endpoint expects a JSON payload specifying the sender, receiver, and
    the message content. It will find or create a conversation between the
    two users and then add the new message to that conversation.

    Request Body JSON:
    {
        "sender_id": int,    // ID of the user sending the message
        "receiver_id": int,  // ID of the user receiving the message
        "content": str       // The text content of the message
    }

    Responses:
    - 201 Created: Message sent successfully.
      JSON: {
          "status": "success",
          "message_id": int,
          "conversation_id": int,
          "sender_id": int,
          "content": str
      }
    - 400 Bad Request: Missing required fields, invalid data types,
                       sender and receiver are the same, or other validation errors.
      JSON: { "status": "error", "message": "Error description" }
    - 500 Internal Server Error: Database error or other unexpected server issues.
      JSON: { "status": "error", "message": "Error description" }
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    # Basic validation
    if not all([sender_id, receiver_id, content]):
        missing_fields = []
        if not sender_id: missing_fields.append("sender_id")
        if not receiver_id: missing_fields.append("receiver_id")
        if not content: missing_fields.append("content")
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    if not isinstance(sender_id, int) or not isinstance(receiver_id, int):
        return jsonify({"status": "error", "message": "sender_id and receiver_id must be integers"}), 400

    if not isinstance(content, str) or not content.strip():
        return jsonify({"status": "error", "message": "Content must be a non-empty string"}), 400

    conn = None
    try:
        conn = get_db_connection(DB_NAME)
        # Ensure users exist (FK constraint will catch this if they don't, but good to check)
        # For now, we rely on FK constraints or assume users are pre-validated/exist.

        conversation_id = find_or_create_conversation(conn, sender_id, receiver_id)
        new_message_id = create_message(conn, conversation_id, sender_id, content)
        # Note: create_message in db_utils now handles updating conversation_timestamp and committing.

        # --- Placeholder for Real-Time Notification Logic ---
        # This part remains conceptual for now.
        print(f"Conceptual: Identifying active connection for recipient_id {receiver_id} for real-time notification.")
        print(f"Conceptual: Sending real-time notification to recipient_id {receiver_id} if connected.")
        # --- End of Placeholder for Real-Time Notification Logic ---

        return jsonify({
            "status": "success",
            "message_id": new_message_id,
            "conversation_id": conversation_id,
            "sender_id": sender_id, # Echo back for clarity
            "content": content      # Echo back for clarity
        }), 201

    except ValueError as ve: # Catch custom ValueErrors from db_utils
        return jsonify({"status": "error", "message": str(ve)}), 400
    except sqlite3.IntegrityError as ie: # E.g., Foreign key constraint failed (user_id does not exist)
        # This error message might expose too much, refine in production.
        print(f"Database IntegrityError: {ie}")
        return jsonify({"status": "error", "message": "Invalid sender_id or receiver_id (user does not exist) or database integrity issue."}), 400
    except sqlite3.Error as e:
        print(f"Database error in send_message: {e}")
        return jsonify({"status": "error", "message": "A database error occurred."}), 500
    except Exception as e:
        print(f"Unexpected error in send_message: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """
    API endpoint to get all conversations for a user.
    Expects a 'user_id' query parameter to identify the user.
    """
    user_id_str = request.args.get('user_id')
    if not user_id_str:
        return jsonify({"status": "error", "message": "user_id query parameter is required"}), 400

    try:
        user_id = int(user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id must be an integer"}), 400

    conn = None
    try:
        conn = get_db_connection(DB_NAME)
        # The db_utils function `get_conversations_by_user_id` will return an empty list
        # if the user has no conversations or if the user_id does not exist,
        # which is acceptable for this endpoint (shows no conversations).
        # A specific check for user existence could be added if a 404 is preferred for unknown users.

        conversations_list = get_conversations_by_user_id(conn, user_id)

        return jsonify({"status": "success", "user_id": user_id, "conversations": conversations_list}), 200

    except sqlite3.Error as e:
        # Log the error for server-side diagnostics
        print(f"Database error in get_conversations for user_id {user_id}: {e}")
        return jsonify({"status": "error", "message": "A database error occurred while retrieving conversations."}), 500
    except Exception as e:
        # Log the error for server-side diagnostics
        print(f"Unexpected error in get_conversations for user_id {user_id}: {e}")
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_messages_for_conversation(conversation_id):
    """
    API endpoint to get all messages for a specific conversation.
    Accepts 'conversation_id' as a path parameter.
    Requires 'user_id' query parameter for authorization.
    """
    requesting_user_id_str = request.args.get('user_id')
    if not requesting_user_id_str:
        return jsonify({"status": "error", "message": "user_id query parameter is required for authorization"}), 400

    try:
        requesting_user_id = int(requesting_user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id query parameter for authorization must be an integer"}), 400

    conn = None
    try:
        conn = get_db_connection(DB_NAME)

        # Authorization Step 1: Verify conversation exists
        conversation = get_conversation_by_id(conn, conversation_id)
        if not conversation:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404

        # Authorization Step 2: Check if the requesting_user_id is part of this conversation
        if not (conversation['participant1_id'] == requesting_user_id or \
                conversation['participant2_id'] == requesting_user_id):
            # Log this attempt for security auditing if necessary
            print(f"Authorization failed: User {requesting_user_id} attempted to access conversation {conversation_id}.")
            return jsonify({"status": "error", "message": "User not authorized for this conversation"}), 403

        # If authorized, fetch messages
        messages_list = get_messages_by_conversation_id(conn, conversation_id)

        return jsonify({"status": "success", "conversation_id": conversation_id, "messages": messages_list}), 200

    except sqlite3.Error as e:
        print(f"Database error in get_messages_for_conversation (conv_id {conversation_id}): {e}")
        return jsonify({"status": "error", "message": "A database error occurred while retrieving messages."}), 500
    except Exception as e:
        print(f"Unexpected error in get_messages_for_conversation (conv_id {conversation_id}): {e}")
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Initialize the database schema when running the app directly.
    # This is suitable for development and testing.
    # In a production environment, database schema migrations should be handled
    # by a dedicated migration tool (e.g., Alembic for SQLAlchemy, or custom scripts).
    print(f"Attempting to initialize database '{DB_NAME}'...")
    try:
        conn = get_db_connection(DB_NAME)
        initialize_schema(conn)
        # Optionally, add some default users for testing if they don't exist
        # This helps in making the API immediately testable for development.
        cursor = conn.cursor()
        default_users = [('devuser1',), ('devuser2',), ('devuser3',)]
        try:
            # Using INSERT OR IGNORE to avoid errors if users already exist from previous runs
            cursor.executemany("INSERT OR IGNORE INTO users (username) VALUES (?)", default_users)
            conn.commit()
            print("Default users ensured in database for development/testing.")
        except sqlite3.Error as e:
            print(f"Error ensuring default users: {e}")
        finally:
            # Close the connection used for schema/user setup
            if conn:
                conn.close()
    except sqlite3.Error as e:
        print(f"FATAL: Could not initialize database schema for '{DB_NAME}': {e}")
        # Potentially exit if DB is critical for app start, or let Flask try to run
    except Exception as e:
        print(f"An unexpected error occurred during initial setup: {e}")

    app.run(debug=True, port=5000)
