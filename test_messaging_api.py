import unittest
import json
import sqlite3
from unittest.mock import patch, MagicMock, ANY # ANY is useful for connection objects

# Assuming messaging_api.py is in the same directory or accessible in PYTHONPATH
from messaging_api import app # Import the app object directly

class TestMessagingAPI(unittest.TestCase):

    def setUp(self):
        """Set up test client for each test."""
        app.testing = True
        self.client = app.test_client()
        # No global DB patch needed here as we patch functions from db_utils_messaging directly in each test.

    # --- Tests for POST /api/messages ---

    @patch('messaging_api.db_utils_messaging.create_message')
    @patch('messaging_api.db_utils_messaging.find_or_create_conversation')
    @patch('messaging_api.get_db_connection') # To control the connection object if needed or mock its behavior
    def test_send_message_success(self, mock_get_db_conn, mock_find_or_create_conv, mock_create_message):
        """Test successful message sending."""
        # Mock the database connection if specific checks on it are needed,
        # otherwise, it might not be strictly necessary if db_utils functions are fully mocked.
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn

        payload = {
            "sender_id": 1,
            "receiver_id": 2,
            "content": "Hello, this is a test message!"
        }

        mock_find_or_create_conv.return_value = 123  # conversation_id
        mock_create_message.return_value = 456      # message_id

        response = self.client.post('/api/messages', json=payload)
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['message_id'], 456)
        self.assertEqual(response_data['conversation_id'], 123)
        self.assertEqual(response_data['sender_id'], payload['sender_id'])
        self.assertEqual(response_data['content'], payload['content'])

        mock_get_db_conn.assert_called_once() # Check if get_db_connection was called
        mock_find_or_create_conv.assert_called_once_with(mock_conn, 1, 2)
        mock_create_message.assert_called_once_with(mock_conn, 123, 1, "Hello, this is a test message!")
        mock_conn.close.assert_called_once() # Ensure connection closed

    def test_send_message_missing_fields(self):
        """Test message sending with missing required fields. Does not need DB mocks."""
        payload_missing_content = {"sender_id": 1, "receiver_id": 2}
        response = self.client.post('/api/messages', json=payload_missing_content)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", json.loads(response.data.decode())['message'])

        payload_missing_sender = {"receiver_id": 2, "content": "Test"}
        response = self.client.post('/api/messages', json=payload_missing_sender)
        self.assertEqual(response.status_code, 400)
        self.assertIn("sender_id", json.loads(response.data.decode())['message'])

    def test_send_message_invalid_ids_type(self):
        """Test message sending with non-integer sender/receiver IDs."""
        payload = {"sender_id": "user1", "receiver_id": 2, "content": "Hello!"}
        response = self.client.post('/api/messages', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data.decode())['message'], 'sender_id and receiver_id must be integers')

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.find_or_create_conversation')
    def test_send_message_sender_equals_receiver(self, mock_find_or_create_conv, mock_get_db_conn):
        """Test sending message where sender_id is the same as receiver_id."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        payload = {"sender_id": 1, "receiver_id": 1, "content": "Talking to myself"}

        # Simulate ValueError from db_utils if it's raised there for this condition
        mock_find_or_create_conv.side_effect = ValueError("Participants cannot be the same user.")

        response = self.client.post('/api/messages', json=payload)
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['message'], "Participants cannot be the same user.")
        mock_find_or_create_conv.assert_called_once_with(mock_conn, 1, 1)
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.find_or_create_conversation')
    def test_send_message_db_error_on_find_or_create(self, mock_find_or_create_conv, mock_get_db_conn):
        """Test DB error when finding/creating conversation."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        mock_find_or_create_conv.side_effect = sqlite3.Error("DB down on find_or_create")
        payload = {"sender_id": 1, "receiver_id": 2, "content": "Test"}

        response = self.client.post('/api/messages', json=payload)
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_data['message'], "A database error occurred.")
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.find_or_create_conversation')
    @patch('messaging_api.db_utils_messaging.create_message')
    def test_send_message_db_integrity_error_on_create_message(self, mock_create_msg, mock_find_or_create_conv, mock_get_db_conn):
        """Test DB IntegrityError (e.g. user not found) when creating message."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        mock_find_or_create_conv.return_value = 123 # conversation_id
        mock_create_msg.side_effect = sqlite3.IntegrityError("User not found or other FK issue")
        payload = {"sender_id": 998, "receiver_id": 999, "content": "Test to non-existent users"}

        response = self.client.post('/api/messages', json=payload)
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 400) # As per current API error handling for IntegrityError
        self.assertIn("Invalid sender_id or receiver_id", response_data['message'])
        mock_conn.close.assert_called_once()

    # --- Tests for GET /api/conversations ---

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversations_by_user_id')
    def test_get_conversations_success(self, mock_get_convos, mock_get_db_conn):
        """Test successful retrieval of conversations for a user."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        user_id = 1
        expected_convos = [{'conversation_id': 1, 'other_participant_username': 'bob', 'last_message_content': 'Hi'}]
        mock_get_convos.return_value = expected_convos

        response = self.client.get(f'/api/conversations?user_id={user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['user_id'], user_id)
        self.assertEqual(response_data['conversations'], expected_convos)
        mock_get_convos.assert_called_once_with(mock_conn, user_id)
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversations_by_user_id')
    def test_get_conversations_empty(self, mock_get_convos, mock_get_db_conn):
        """Test retrieval of conversations when user has none."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        user_id = 2
        mock_get_convos.return_value = []

        response = self.client.get(f'/api/conversations?user_id={user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['conversations'], [])
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversations_by_user_id')
    def test_get_conversations_db_error(self, mock_get_convos, mock_get_db_conn):
        """Test DB error when retrieving conversations."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        user_id = 1
        mock_get_convos.side_effect = sqlite3.Error("DB down on get_conversations")

        response = self.client.get(f'/api/conversations?user_id={user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_data['message'], "A database error occurred.")
        mock_conn.close.assert_called_once()

    def test_get_conversations_missing_user_id_param(self):
        """Test GET /api/conversations without user_id query parameter."""
        response = self.client.get('/api/conversations')
        self.assertEqual(response.status_code, 400)
        self.assertIn("user_id query parameter is required", json.loads(response.data.decode())['message'])

    # --- Tests for GET /api/conversations/<int:conversation_id>/messages ---

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversation_by_id')
    @patch('messaging_api.db_utils_messaging.get_messages_by_conversation_id')
    def test_get_messages_success(self, mock_get_messages, mock_get_convo_by_id, mock_get_db_conn):
        """Test successful retrieval of messages for a conversation."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        conversation_id = 1
        requesting_user_id = 10

        mock_get_convo_by_id.return_value = {'conversation_id': conversation_id, 'participant1_id': 10, 'participant2_id': 20}
        expected_messages = [{'message_id': 1, 'content': 'Hello', 'sender_id': 10}]
        mock_get_messages.return_value = expected_messages

        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={requesting_user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['conversation_id'], conversation_id)
        self.assertEqual(response_data['messages'], expected_messages)
        mock_get_convo_by_id.assert_called_once_with(mock_conn, conversation_id)
        mock_get_messages.assert_called_once_with(mock_conn, conversation_id)
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversation_by_id')
    def test_get_messages_conversation_not_found(self, mock_get_convo_by_id, mock_get_db_conn):
        """Test getting messages when conversation is not found."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        conversation_id = 999
        requesting_user_id = 10
        mock_get_convo_by_id.return_value = None

        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={requesting_user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response_data['message'], "Conversation not found")
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversation_by_id')
    def test_get_messages_unauthorized_user(self, mock_get_convo_by_id, mock_get_db_conn):
        """Test getting messages when user is not part of the conversation."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        conversation_id = 1
        unauthorized_user_id = 30
        mock_get_convo_by_id.return_value = {'conversation_id': conversation_id, 'participant1_id': 10, 'participant2_id': 20}

        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={unauthorized_user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response_data['message'], "User not authorized for this conversation")
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversation_by_id')
    def test_get_messages_db_error_on_get_convo(self, mock_get_convo_by_id, mock_get_db_conn):
        """Test DB error when fetching conversation for auth check."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        conversation_id = 1
        requesting_user_id = 10
        mock_get_convo_by_id.side_effect = sqlite3.Error("DB error on get_conversation_by_id")

        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={requesting_user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_data['message'], "A database error occurred.")
        mock_conn.close.assert_called_once()

    @patch('messaging_api.get_db_connection')
    @patch('messaging_api.db_utils_messaging.get_conversation_by_id')
    @patch('messaging_api.db_utils_messaging.get_messages_by_conversation_id')
    def test_get_messages_db_error_on_get_messages(self, mock_get_messages, mock_get_convo_by_id, mock_get_db_conn):
        """Test DB error when fetching actual messages."""
        mock_conn = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        conversation_id = 1
        requesting_user_id = 10

        mock_get_convo_by_id.return_value = {'conversation_id': conversation_id, 'participant1_id': 10, 'participant2_id': 20}
        mock_get_messages.side_effect = sqlite3.Error("DB error on get_messages_by_conversation_id")

        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={requesting_user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_data['message'], "A database error occurred.")
        mock_conn.close.assert_called_once()

    def test_get_messages_missing_user_id_param(self):
        """Test GET /api/conversations/.../messages without user_id query parameter."""
        conversation_id = 1
        response = self.client.get(f'/api/conversations/{conversation_id}/messages')
        self.assertEqual(response.status_code, 400)
        self.assertIn("user_id query parameter is required", json.loads(response.data.decode())['message'])

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
