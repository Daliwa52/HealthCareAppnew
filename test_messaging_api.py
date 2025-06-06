import unittest
import json
from unittest.mock import patch, MagicMock

# Assuming messaging_api.py is in the same directory or accessible in PYTHONPATH
import messaging_api

class TestMessagingAPI(unittest.TestCase):

    def setUp(self):
        """Set up test client for each test."""
        messaging_api.app.testing = True
        self.client = messaging_api.app.test_client()
        # If messaging_api.py had a global db object, we might patch it here.
        # For now, we'll patch specific functions or rely on the placeholder nature.

    # --- Tests for POST /api/messages ---

    @patch('messaging_api.print') # Patching print to suppress placeholder output during tests
    # In a real app, you'd patch the actual database functions like 'find_or_create_conversation', 'create_message'
    def test_send_message_success(self, mock_print):
        """Test successful message sending."""
        payload = {
            "sender_id": 1,
            "receiver_id": 2,
            "content": "Hello, this is a test message!"
        }
        # Simulate that the placeholder database logic "succeeds" and returns IDs
        # If actual DB functions were called, their mocks would return these.
        # messaging_api.py currently uses hardcoded IDs in its placeholders if None.
        # We are testing the API layer, so we assume the underlying logic (even if placeholder)
        # will eventually produce the IDs needed for the response.

        response = self.client.post('/api/messages', json=payload)
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('message_id', response_data)
        self.assertIn('conversation_id', response_data) # As per current messaging_api.py response
        self.assertEqual(response_data['sender_id'], payload['sender_id'])
        self.assertEqual(response_data['content'], payload['content'])
        # mock_print would have been called by the placeholder logic in messaging_api.py
        # Example: mock_print.assert_any_call("Placeholder: Saving message from 1 to conversation 1 with content: 'Hello, this is a test message!'")


    def test_send_message_missing_fields(self):
        """Test message sending with missing required fields."""
        payload_missing_content = {
            "sender_id": 1,
            "receiver_id": 2
            # "content" is missing
        }
        response = self.client.post('/api/messages', json=payload_missing_content)
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('Missing required fields', response_data['message'])
        self.assertIn('content', response_data['message'])

        payload_missing_sender = {
            "receiver_id": 2,
            "content": "Test message"
        }
        response = self.client.post('/api/messages', json=payload_missing_sender)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('sender_id', response_data['message'])

    def test_send_message_invalid_ids(self):
        """Test message sending with non-integer sender/receiver IDs."""
        payload = {
            "sender_id": "user1", # Invalid, should be int
            "receiver_id": 2,
            "content": "Hello!"
        }
        response = self.client.post('/api/messages', json=payload)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'sender_id and receiver_id must be integers')


    # --- Tests for GET /api/conversations ---

    @patch('messaging_api.print') # Patching print to suppress placeholder output
    # In a real app, you'd patch the database function like 'db_fetch_conversations'
    def test_get_conversations_success(self, mock_print):
        """Test successful retrieval of conversations for a user."""
        user_id = 1
        # The current messaging_api.py returns a hardcoded list for this endpoint.
        # A mock for a DB function would return a similar structure.
        expected_conversations_structure = [
            {
                "conversation_id": 1,
                "participant1_id": user_id,
                "participant2_id": 2,
                "other_participant_username": "UserTwo",
                "last_message_snippet": "Hello there!",
                "last_message_timestamp": "2023-10-26T10:00:00Z",
                "updated_at": "2023-10-26T10:00:00Z"
            }
            # ... more conversations
        ]

        response = self.client.get(f'/api/conversations?user_id={user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['status'], 'success')
        self.assertIsInstance(response_data['conversations'], list)
        # We can check if the structure of the first item matches, assuming the placeholder returns the example
        if response_data['conversations']: # If the placeholder actually returned something
            self.assertDictContainsSubset(expected_conversations_structure[0].keys(), response_data['conversations'][0].keys())

    def test_get_conversations_missing_user_id(self):
        """Test getting conversations without providing user_id query parameter."""
        response = self.client.get('/api/conversations') # No user_id
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 400) # As per current messaging_api.py logic
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'user_id query parameter is required and must be an integer')

    @patch('messaging_api.print')
    def test_get_messages_for_conversation_success(self, mock_print):
        """Test successful retrieval of messages for a conversation."""
        conversation_id = 1
        user_id = 1 # Assuming user_id is required for authorization
        # Placeholder in messaging_api.py returns a fixed list
        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={user_id}')
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['status'], 'success')
        self.assertIsInstance(response_data['messages'], list)
        if response_data['messages']:
            self.assertIn('message_id', response_data['messages'][0])
            self.assertEqual(response_data['messages'][0]['conversation_id'], conversation_id)

    def test_get_messages_for_conversation_missing_user_id(self, mock_print=None): # mock_print for consistency if other tests patch it
        """Test getting messages without user_id for authorization."""
        conversation_id = 1
        response = self.client.get(f'/api/conversations/{conversation_id}/messages') # Missing user_id
        response_data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'user_id query parameter is required for authorization')

    @patch('messaging_api.print')
    def test_get_messages_for_conversation_not_found(self, mock_print):
        """Test getting messages for a non-existent conversation."""
        conversation_id = 9999 # Simulated not found in messaging_api.py
        user_id = 1
        response = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={user_id}')
        response_data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Conversation not found')


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    # Note: Running unittest.main directly in a script can have issues with some test runners and configurations.
    # It's often better to run tests using `python -m unittest test_messaging_api.py`.
    # The `argv` and `exit=False` are common workarounds for simple script-based execution.
