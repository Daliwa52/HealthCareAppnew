import unittest
import json
import os
import sqlite3
import time # To add slight delays if needed for timestamp differentiation

# Import the Flask app and db utils from the main application files
from messaging_api import app, DB_NAME as APP_DB_NAME # Import app and its original DB_NAME
import messaging_api # To allow modifying DB_NAME used by the app
from db_utils_messaging import get_db_connection, initialize_schema # For setup

TEST_DB_NAME = 'test_messaging_integration.db'

class TestIntegrationMessaging(unittest.TestCase):
    original_db_name = None # To store the app's original DB_NAME

    @classmethod
    def setUpClass(cls):
        """
        Set up a test database once before all tests in the class.
        - Modifies the app's DB_NAME to use the test database.
        - Initializes the schema.
        - Creates test users.
        """
        cls.original_db_name = messaging_api.DB_NAME # Save original
        messaging_api.DB_NAME = TEST_DB_NAME      # Point app to test DB

        # Ensure no old test DB exists
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)

        conn = None
        try:
            conn = get_db_connection(TEST_DB_NAME)
            initialize_schema(conn) # Creates users, conversations, messages tables

            # Create test users
            cursor = conn.cursor()
            users_to_create = [('integ_user1',), ('integ_user2',), ('integ_user3',)]
            cursor.executemany("INSERT INTO users (username) VALUES (?)", users_to_create)
            conn.commit()

            cursor.execute("SELECT user_id FROM users WHERE username = 'integ_user1'")
            cls.user1_id = cursor.fetchone()['user_id']
            cursor.execute("SELECT user_id FROM users WHERE username = 'integ_user2'")
            cls.user2_id = cursor.fetchone()['user_id']
            cursor.execute("SELECT user_id FROM users WHERE username = 'integ_user3'")
            cls.user3_id = cursor.fetchone()['user_id']

            print(f"setUpClass: Test users created. user1_id={cls.user1_id}, user2_id={cls.user2_id}, user3_id={cls.user3_id}")

        except sqlite3.Error as e:
            print(f"setUpClass DB error: {e}")
            if conn: conn.rollback()
            raise # Fail fast if setup fails
        except Exception as e:
            print(f"setUpClass general error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test database once after all tests in the class.
        - Restores the app's original DB_NAME.
        - Removes the test database file.
        """
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
            print(f"tearDownClass: Removed test database {TEST_DB_NAME}")

        if cls.original_db_name:
            messaging_api.DB_NAME = cls.original_db_name # Restore original

    def setUp(self):
        """Set up the Flask test client before each test."""
        app.testing = True # Ensure app is in testing mode
        self.client = app.test_client()
        # For tests that modify data, consider cleaning specific tables or
        # re-initializing parts of the schema if tests are not independent.
        # For now, we assume tests are mostly additive or test specific error paths.

    def _post_message(self, sender_id, receiver_id, content):
        """Helper to post a message and return the JSON response."""
        response = self.client.post('/api/messages', json={
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content
        })
        return response

    def test_send_message_and_retrieve_conversation_flow(self):
        """
        Tests the full flow:
        1. User1 sends a message to User2.
        2. User2 replies to User1.
        3. Retrieve conversations for User1, check details.
        4. Retrieve messages for the conversation, check details.
        """
        # 1. User1 sends a message to User2
        response1 = self._post_message(self.user1_id, self.user2_id, 'Hello User2!')
        self.assertEqual(response1.status_code, 201)
        data1 = json.loads(response1.data.decode())
        self.assertIn('message_id', data1)
        self.assertIn('conversation_id', data1)
        message1_id = data1['message_id']
        conversation_id = data1['conversation_id']
        self.assertIsNotNone(conversation_id)

        time.sleep(0.01) # Ensure timestamps are distinct if system is very fast

        # 2. User2 replies to User1
        response2 = self._post_message(self.user2_id, self.user1_id, 'Hi User1!')
        self.assertEqual(response2.status_code, 201)
        data2 = json.loads(response2.data.decode())
        self.assertIn('message_id', data2)
        message2_id = data2['message_id']
        # Conversation ID should be the same
        self.assertEqual(data2['conversation_id'], conversation_id)

        # 3. Retrieve conversations for User1
        response_convos_user1 = self.client.get(f'/api/conversations?user_id={self.user1_id}')
        self.assertEqual(response_convos_user1.status_code, 200)
        data_convos_user1 = json.loads(response_convos_user1.data.decode())

        self.assertEqual(data_convos_user1['status'], 'success')
        self.assertEqual(len(data_convos_user1['conversations']), 1)
        convo_summary = data_convos_user1['conversations'][0]

        self.assertEqual(convo_summary['conversation_id'], conversation_id)
        self.assertEqual(convo_summary['other_participant_id'], self.user2_id)
        self.assertEqual(convo_summary['other_participant_username'], 'integ_user2')
        self.assertEqual(convo_summary['last_message_content'], 'Hi User1!')
        self.assertIsNotNone(convo_summary['last_message_timestamp'])
        self.assertIsNotNone(convo_summary['conversation_updated_at'])

        # 4. Retrieve messages for the conversation (as user1)
        response_messages = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={self.user1_id}')
        self.assertEqual(response_messages.status_code, 200)
        data_messages = json.loads(response_messages.data.decode())

        self.assertEqual(data_messages['status'], 'success')
        self.assertEqual(len(data_messages['messages']), 2)

        msg_list = data_messages['messages']
        self.assertEqual(msg_list[0]['message_id'], message1_id)
        self.assertEqual(msg_list[0]['sender_id'], self.user1_id)
        self.assertEqual(msg_list[0]['content'], 'Hello User2!')

        self.assertEqual(msg_list[1]['message_id'], message2_id)
        self.assertEqual(msg_list[1]['sender_id'], self.user2_id)
        self.assertEqual(msg_list[1]['content'], 'Hi User1!')

    def test_send_message_non_existent_sender(self):
        """Test sending a message from a non-existent sender_id."""
        response = self._post_message(99999, self.user1_id, 'Ghost message')
        # This should cause an IntegrityError due to foreign key constraint on sender_id
        # The API handles IntegrityError as a 400.
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['status'], 'error')
        self.assertIn("Invalid sender_id or receiver_id", response_data['message'])

    def test_send_message_non_existent_receiver(self):
        """Test sending a message to a non-existent receiver_id."""
        response = self._post_message(self.user1_id, 99999, 'Message to ghost')
        self.assertEqual(response.status_code, 400) # FK constraint on receiver_id
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['status'], 'error')
        self.assertIn("Invalid sender_id or receiver_id", response_data['message'])

    def test_get_messages_unauthorized(self):
        """Test fetching messages for a conversation by a user not part of it."""
        # 1. Create a conversation between user1 and user2
        response_post = self._post_message(self.user1_id, self.user2_id, 'A private message')
        self.assertEqual(response_post.status_code, 201)
        conversation_id = json.loads(response_post.data.decode())['conversation_id']

        # 2. User3 (not part of the conversation) tries to fetch messages
        response_get = self.client.get(f'/api/conversations/{conversation_id}/messages?user_id={self.user3_id}')
        self.assertEqual(response_get.status_code, 403) # Forbidden
        response_data = json.loads(response_get.data.decode())
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'User not authorized for this conversation')

    def test_get_messages_conversation_not_found(self):
        """Test fetching messages for a non-existent conversation_id."""
        non_existent_conversation_id = 99999
        response = self.client.get(f'/api/conversations/{non_existent_conversation_id}/messages?user_id={self.user1_id}')
        self.assertEqual(response.status_code, 404) # Not Found
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Conversation not found')

    def test_get_conversations_for_user_with_no_conversations(self):
        """Test fetching conversations for a user who has none."""
        # Assuming user3_id was created but hasn't participated in any convos in this test context yet
        # (or create a dedicated user for this test if needed and ensure they have no convos)
        response = self.client.get(f'/api/conversations?user_id={self.user3_id}') # User3 may have a convo from other test if not careful
        # Let's use a freshly made user for this to be sure.
        conn = get_db_connection(TEST_DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES (?)", ('isolated_user',))
        isolated_user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        response = self.client.get(f'/api/conversations?user_id={isolated_user_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['conversations']), 0)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
