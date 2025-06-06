from flask import Flask, request, jsonify

app = Flask(__name__)

# In a real application, you would configure your database connection here
# For example, using Flask-SQLAlchemy or another ORM/DB connector
# from flask_sqlalchemy import SQLAlchemy
# app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
# db = SQLAlchemy(app)

# Placeholder for user model or function to check user existence
def user_exists(user_id):
    # In a real app, query the database to check if user_id exists
    # For this placeholder, we'll assume users with ID > 0 exist
    return isinstance(user_id, int) and user_id > 0

@app.route('/api/messages', methods=['POST'])
def send_message():
    """
    API endpoint to send a new message.
    Expects a JSON payload with sender_id, receiver_id, and content.
    """
    try:
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

        if sender_id == receiver_id:
            return jsonify({"status": "error", "message": "Sender and receiver cannot be the same user"}), 400

        # Placeholder: Validate user existence (optional, depends on requirements)
        # if not user_exists(sender_id) or not user_exists(receiver_id):
        #     return jsonify({"status": "error", "message": "Sender or receiver does not exist"}), 404

        # --- Placeholder for Database Logic ---

        # 1. Find or create a conversation between sender_id and receiver_id
        #    - Query the 'conversations' table.
        #    - A conversation is typically unique for a pair of users, regardless of who is participant1 or participant2.
        #      So, you might search for (p1=sender_id AND p2=receiver_id) OR (p1=receiver_id AND p2=sender_id).
        #    - If no conversation exists, create a new one.
        #    - This would involve database interaction.
        conversation_id = None  # Replace with actual conversation ID from DB
        print(f"Placeholder: Finding/creating conversation for users {sender_id} and {receiver_id}")
        # Example:
        # conversation = find_or_create_conversation(sender_id, receiver_id)
        # conversation_id = conversation.id

        if conversation_id is None: # Simulating a step that should yield a conversation_id
            # This part is just for placeholder demonstration. In a real app,
            # find_or_create_conversation would return an ID or raise an error.
            print(f"Placeholder: Conversation created/found. Assigning a dummy ID 1 for now.")
            conversation_id = 1 # Dummy ID for now


        # 2. Save the new message to the database
        #    - Insert a new record into the 'messages' table.
        #    - Fields: conversation_id, sender_id, content, (timestamp and is_read will have defaults)
        #    - This would involve database interaction and return the new message's ID.
        new_message_id = None # Replace with actual new message ID from DB
        print(f"Placeholder: Saving message from {sender_id} to conversation {conversation_id} with content: '{content}'")
        # Example:
        # new_message = create_message(conversation_id=conversation_id, sender_id=sender_id, content=content)
        # new_message_id = new_message.id

        if new_message_id is None: # Simulating a step that should yield a message_id
            print(f"Placeholder: Message saved. Assigning a dummy ID 101 for now.")
            new_message_id = 101 # Dummy ID for now

        # --- Placeholder for Real-Time Notification Logic (e.g., WebSockets, SSE) ---
        # After successfully saving the message, you would typically notify the recipient in real-time.
        #
        # 1. Identify Recipient's Connection:
        #    - The `receiver_id` is known from the request payload.
        #    - Need to look up if the `receiver_id` has an active WebSocket session or SSE connection.
        #    - This might involve querying a data store (e.g., Redis, a dictionary in memory for simple cases)
        #      that maps user IDs to their WebSocket session IDs (e.g., `sid` in Flask-SocketIO) or other connection identifiers.
        #    - Example: `recipient_session_id = get_websocket_session_id_for_user(receiver_id)`
        print(f"Placeholder: Identifying active connection for recipient_id {receiver_id} for real-time notification.")

        # 2. Send Notification:
        #    - If an active connection is found, send a notification to the recipient.
        #    - The notification payload could be the full new message data, or just an event
        #      (e.g., "new_message_in_conversation_X") prompting the client to fetch new messages.
        #    - This would typically use a WebSocket library (e.g., Flask-SocketIO's `emit` function)
        #      or an SSE event stream.
        #    - Example (Flask-SocketIO):
        #      `if recipient_session_id:`
        #      `    socketio.emit('new_message',`
        #      `                  {'message_id': new_message_id, 'conversation_id': conversation_id, 'sender_id': sender_id, 'content': content, 'timestamp': '...'},`
        #      `                  room=recipient_session_id)`
        #      `else:`
        #      `    # User is not currently connected via WebSocket, might rely on push notifications or polling.`
        print(f"Placeholder: Sending real-time notification to recipient_id {receiver_id} if connected.")
        # --- End of Placeholder for Real-Time Notification Logic ---

        # 3. Update the 'conversations.updated_at' timestamp
        #    - Update the 'updated_at' field of the conversation record (identified by conversation_id).
        #    - This could be handled by a database trigger (as noted in messaging_schema.sql)
        #      or explicitly here.
        print(f"Placeholder: Updating 'updated_at' for conversation {conversation_id}")
        # Example:
        # update_conversation_timestamp(conversation_id)

        # --- End of Placeholder for Database Logic ---

        return jsonify({
            "status": "success",
            "message_id": new_message_id,
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content
        }), 201 # 201 Created

    except Exception as e:
        # Log the exception in a real application
        print(f"Error processing request: {e}") # For debugging
        return jsonify({"status": "error", "message": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    # Note: This is for development only.
    # In a production environment, use a WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, port=5000)


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """
    API endpoint to get all conversations for a user.
    Expects a 'user_id' query parameter to identify the user.
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({"status": "error", "message": "user_id query parameter is required and must be an integer"}), 400

    # Placeholder: Validate user existence (optional)
    # if not user_exists(user_id):
    #     return jsonify({"status": "error", "message": "User does not exist"}), 404

    # --- Placeholder for Database Logic ---
    # 1. Query the 'conversations' table for conversations where participant1_id = user_id OR participant2_id = user_id.
    #    - This would involve database interaction.
    #    - For each conversation, you might also want to fetch details of the other participant (username, profile picture).
    #    - Optionally, retrieve the last message for each conversation to display a snippet. This might involve
    #      a more complex query (e.g., using a subquery or a join with the 'messages' table, grouped by conversation_id,
    #      and ordered by timestamp descending).
    print(f"Placeholder: Fetching conversations for user_id {user_id}")
    # Example structure for conversations list:
    conversations_list = [
        {
            "conversation_id": 1,
            "participant1_id": user_id,
            "participant2_id": 2, # Other user
            "other_participant_username": "UserTwo", # Fetched from users table
            "last_message_snippet": "Hello there!",
            "last_message_timestamp": "2023-10-26T10:00:00Z",
            "updated_at": "2023-10-26T10:00:00Z"
        },
        {
            "conversation_id": 3,
            "participant1_id": 5, # Other user
            "participant2_id": user_id,
            "other_participant_username": "UserFive", # Fetched from users table
            "last_message_snippet": "See you soon.",
            "last_message_timestamp": "2023-10-25T15:30:00Z",
            "updated_at": "2023-10-25T15:30:00Z"
        }
    ]
    # In a real implementation, if no conversations are found, this list would be empty.
    # --- End of Placeholder for Database Logic ---

    if not conversations_list: # Example: if DB query returned no results
        # Depending on preference, either return an empty list or a 404
        # For now, returning an empty list for "no conversations found" is common.
        return jsonify({"status": "success", "conversations": []}), 200

    return jsonify({"status": "success", "conversations": conversations_list}), 200


@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_messages_for_conversation(conversation_id):
    """
    API endpoint to get all messages for a specific conversation.
    Accepts 'conversation_id' as a path parameter.
    Optionally, could also check if the requesting user is part of this conversation.
    """
    # For now, we'll assume a user_id is also passed to check if they are part of the conversation
    # In a real app, this would come from session/token.
    requesting_user_id = request.args.get('user_id', type=int)
    if not requesting_user_id:
        return jsonify({"status": "error", "message": "user_id query parameter is required for authorization"}), 400


    # --- Placeholder for Database Logic ---
    # 1. Verify conversation existence:
    #    - Query 'conversations' table for the given conversation_id.
    #    - If not found, return a 404 error.
    print(f"Placeholder: Verifying existence of conversation_id {conversation_id}")
    # conversation_exists = check_conversation_exists(conversation_id)
    # if not conversation_exists:
    #    return jsonify({"status": "error", "message": "Conversation not found"}), 404

    # 2. Verify user is part of the conversation (Authorization):
    #    - Check if 'requesting_user_id' is either 'participant1_id' or 'participant2_id' in the conversation.
    #    - If not, return a 403 Forbidden error.
    print(f"Placeholder: Verifying user {requesting_user_id} is part of conversation {conversation_id}")
    # is_participant = check_user_in_conversation(requesting_user_id, conversation_id)
    # if not is_participant:
    #    return jsonify({"status": "error", "message": "User not authorized for this conversation"}), 403

    # 3. Query 'messages' table for all messages where 'conversation_id' matches.
    #    - Order messages by 'timestamp' (e.g., ascending for chronological order).
    #    - This would involve database interaction.
    print(f"Placeholder: Fetching messages for conversation_id {conversation_id}, ordered by timestamp.")
    # Example structure for messages list:
    messages_list = [
        {
            "message_id": 101,
            "conversation_id": conversation_id,
            "sender_id": 1, # Example sender
            "content": "Hello!",
            "timestamp": "2023-10-26T09:59:00Z",
            "is_read": True
        },
        {
            "message_id": 102,
            "conversation_id": conversation_id,
            "sender_id": 2, # Example sender
            "content": "Hi there!",
            "timestamp": "2023-10-26T10:00:00Z",
            "is_read": True
        }
    ]
    # If the conversation exists but has no messages, this list would be empty.
    # --- End of Placeholder for Database Logic ---

    # Simulating conversation not found or user not authorized for demonstration
    # based on some dummy logic. In real app, this would be based on DB query results.
    if conversation_id == 9999: # Simulate conversation not found
         return jsonify({"status": "error", "message": "Conversation not found"}), 404
    if requesting_user_id == 789 and conversation_id == 1 : # Simulate user not authorized
        return jsonify({"status": "error", "message": "User not authorized for this conversation"}), 403


    return jsonify({"status": "success", "messages": messages_list}), 200
