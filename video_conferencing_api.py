import os
from flask import Flask, request, jsonify
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
# In a real application, you might use a .env file and python-dotenv
# from dotenv import load_dotenv
# load_dotenv()

app = Flask(__name__)

# --- Configuration for Twilio ---
# These credentials should be stored securely, typically as environment variables.
# Do NOT hardcode them in your application.
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_API_KEY_SID = os.environ.get('TWILIO_API_KEY_SID')
TWILIO_API_KEY_SECRET = os.environ.get('TWILIO_API_KEY_SECRET')

@app.route('/api/video/token', methods=['POST'])
def get_video_token():
    """
    API endpoint to generate an Access Token for Twilio Programmable Video.
    Expects a JSON payload with user_identity and room_name.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET]):
        # This check is important for the server operator, not typically for the client.
        # In a production app, you might log this error and return a generic server error.
        print("ERROR: Twilio credentials are not configured on the server.")
        return jsonify({"status": "error", "message": "Server configuration error for video services."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    user_identity = data.get('user_identity')
    room_name = data.get('room_name')

    # Basic validation
    if not user_identity:
        return jsonify({"status": "error", "message": "Missing required field: user_identity"}), 400
    if not room_name:
        return jsonify({"status": "error", "message": "Missing required field: room_name"}), 400

    try:
        # --- Placeholder for Twilio Logic ---

        # 1. Initialize the Twilio AccessToken object
        #    - Uses TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET
        #    - Sets the identity for the token.
        print(f"Placeholder: Creating AccessToken for identity: {user_identity}")
        token = AccessToken(TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, identity=user_identity)

        # 2. Create a Twilio Video Grant
        #    - This grant allows the user to connect to a specific video room.
        print(f"Placeholder: Creating VideoGrant for room: {room_name}")
        video_grant = VideoGrant(room=room_name)

        # 3. Add the Video Grant to the Access Token
        print("Placeholder: Adding VideoGrant to AccessToken")
        token.add_grant(video_grant)

        # 4. Serialize the token to a JWT string
        #    - This is the token that the client application will use to connect to Twilio.
        jwt_token = token.to_jwt()
        print(f"Placeholder: Token generated successfully for room '{room_name}' and identity '{user_identity}'.")
        # In a real scenario, you would return jwt_token directly.
        # For this placeholder, we'll simulate it.
        # simulated_jwt_token = f"simulated_jwt_for_{user_identity}_in_{room_name}"

        # --- End of Placeholder for Twilio Logic ---

        # return jsonify({"token": simulated_jwt_token}), 200 # Use this for testing without real credentials
        if isinstance(jwt_token, bytes): # to_jwt can return bytes in some versions
            jwt_token = jwt_token.decode('utf-8')
        return jsonify({"token": jwt_token}), 200

    except Exception as e:
        # Log the exception in a real application
        print(f"Error generating Twilio token: {e}") # For debugging
        # Avoid exposing detailed Twilio errors to the client directly for security.
        return jsonify({"status": "error", "message": "Failed to generate video access token."}), 500

if __name__ == '__main__':
    # Note: This is for development only.
    # Ensure TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET are set as environment variables
    # e.g., export TWILIO_ACCOUNT_SID='ACxxxxxxxxxxxxxxx'
    if not all([TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET]):
        print("WARNING: Twilio credentials are not set in environment variables.")
        print("Video token generation will fail with 'Server configuration error'.")
        print("Please set TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, and TWILIO_API_KEY_SECRET.")

    app.run(debug=True, port=5001) # Using a different port if messaging_api is also running
