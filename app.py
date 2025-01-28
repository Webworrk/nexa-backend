from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import traceback

app = Flask(__name__)

# MongoDB connection
try:
    mongo_uri = os.environ.get("MONGO_URI")  # Ensure this environment variable is set
    client = MongoClient(mongo_uri)
    db = client['Nexa']
    print("Connected to MongoDB successfully!")
except Exception as e:
    print("Failed to connect to MongoDB:", str(e))

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Nexa Backend!"})

# Add a user
@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        data = request.json
        result = db['users'].insert_one(data)
        return jsonify({"message": "User added successfully!", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Failed to add user"}), 500

# Add a connection request
@app.route('/add_connection_request', methods=['POST'])
def add_connection_request():
    try:
        data = request.json
        result = db['connection_requests'].insert_one(data)
        return jsonify({"message": "Connection request added successfully!", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Failed to add connection request"}), 500

# Fetch all users
@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        users = list(db['users'].find({}, {'_id': 0}))  # Exclude MongoDB's `_id` field
        return jsonify(users), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Failed to fetch users"}), 500

# Find match from the database

def find_match(goal_context):
    """
    Searches the database for relevant connections based on user's networking goal.
    """
    if not goal_context:
        return "No specific networking goal found."

    print(f"🔍 Searching for relevant connections based on: {goal_context}")

    match = db.webhooks.find_one(
        {"goal_context": {"$regex": goal_context, "$options": "i"}},
        {"user_name": 1, "profession": 1, "email": 1, "_id": 0}
    )

    if match:
        return f"I found {match['user_name']}, a {match['profession']}. Would you like me to set up a meeting?"
    else:
        return "I don't have a direct connection for this right now, but I'll keep looking and notify you once I find someone."

# Webhook for VAPI
@app.route('/vapi-webhook', methods=['POST'])
def vapi_webhook():
    try:
        data = request.json  # Get the incoming JSON

        if not data:
            print("❌ No data received!")
            return jsonify({"error": "No data received"}), 400

        # Extract important fields from nested JSON
        message = data.get("message", {})
        analysis = message.get("analysis", {})
        artifact = message.get("artifact", {})
        messages = artifact.get("messages", [])

        # Extract meeting time and date
        meeting_time = None
        meeting_date = None
        for msg in messages:
            text = msg.get("message", "")
            if any(t in text for t in ["AM", "PM"]):
                meeting_time = text
            if "2025" in text:
                meeting_date = text

        # Format meeting date and time
        if meeting_date:
            meeting_date = "-".join(meeting_date.split("-"))  # Ensure DD-MM-YYYY format
        if meeting_time:
            meeting_time = meeting_time.replace(".", ":")  # Ensure HH:MM AM/PM format

        extracted_data = {
            "user_name": message.get("user_name", "Unknown"),
            "phone": message.get("phone", ""),
            "email": message.get("email", ""),
            "nexa_id": message.get("nexa_id", ""),
            "profession": message.get("profession", ""),
            "goal_context": analysis.get("summary", ""),
            "connection_type": message.get("connection_type", ""),
            "meeting_date": meeting_date,
            "meeting_time": meeting_time,
            "requested_to": message.get("requested_to", "Rahul8906"),
            "context": "Vapi Webhook Data Processing"
        }

        print("📌 Extracted Data:", extracted_data)

        # Check if user already exists
        existing_user = db.webhooks.find_one({"nexa_id": extracted_data["nexa_id"]})
        if existing_user:
            # Append new data instead of overwriting
            db.webhooks.update_one(
                {"nexa_id": extracted_data["nexa_id"]},
                {"$set": {"profession": extracted_data["profession"], "goal_context": extracted_data["goal_context"]},
                 "$push": {"meeting_history": {"date": extracted_data["meeting_date"], "time": extracted_data["meeting_time"]}}}
            )
            print("✅ User data updated!")
        else:
            # Insert new user profile
            extracted_data["meeting_history"] = [{"date": extracted_data["meeting_date"], "time": extracted_data["meeting_time"]}]
            result = db.webhooks.insert_one(extracted_data)
            print("✅ New user data stored, ID:", result.inserted_id)

        # Perform real-time search for relevant matches
        match_response = find_match(extracted_data["goal_context"])

        return jsonify({"message": "Data stored successfully", "match": match_response}), 200

    except Exception as e:
        print("❌ Error Processing Webhook:", str(e))
        print(traceback.format_exc())  # Logs full traceback for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
