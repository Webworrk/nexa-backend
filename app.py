from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import traceback
import re
from datetime import datetime

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

        # Initialize variables
        meeting_date = None
        meeting_time = None

        for msg in messages:
            text = msg.get("message", "")

            # ✅ Extract Date and Time from Message
            date_time_match = re.search(
                r'(\b\d{1,2}\b)\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{4})\s*at\s*(\d{1,2}):(\d{2})\s*(AM|PM)',
                text, re.IGNORECASE
            )

            if date_time_match:
                day, month_name, year, hour, minute, am_pm = date_time_match.groups()
                
                # Convert to required formats
                month_number = datetime.strptime(month_name, "%B").month  # Convert month name to number
                meeting_date = f"{int(day):02d}-{int(month_number):02d}-{year}"  # Format: DD-MM-YYYY
                meeting_time = f"{hour}:{minute} {am_pm.upper()}"  # Format: HH:MM AM/PM

        # Store extracted data
        extracted_data = {
            "user_name": message.get("user_name", "Unknown"),
            "phone": message.get("phone", ""),
            "email": message.get("email", ""),
            "nexa_id": message.get("nexa_id", ""),
            "profession": message.get("profession", ""),
            "goal_context": analysis.get("summary", ""),
            "connection_type": message.get("connection_type", ""),
            "meeting_date": meeting_date if meeting_date else "Not Provided",
            "meeting_time": meeting_time if meeting_time else "Not Provided",
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

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        print("❌ Error Processing Webhook:", str(e))
        print(traceback.format_exc())  # Logs full traceback for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
