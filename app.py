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

        # Extract meeting time (e.g., "4 PM", "10:30 AM")
        meeting_time = None
        for msg in messages:
            text = msg.get("message", "")
            if any(t in text for t in ["AM", "PM"]):
                meeting_time = text
                break

        extracted_data = {
            "summary": analysis.get("summary"),
            "success_evaluation": analysis.get("success_evaluation"),
            "meeting_time": meeting_time,
            "requested_to": message.get("requested_to", "Rahul8906"),  # Dynamic or default
            "context": "Vapi Webhook Data Processing"
        }

        print("📌 Extracted Data:", extracted_data)

        # Insert data into MongoDB
        result = db.webhooks.insert_one(extracted_data)
        print("✅ Data Stored Successfully, ID:", result.inserted_id)

        return jsonify({"message": "Data stored successfully", "id": str(result.inserted_id)}), 200

    except Exception as e:
        print("❌ Error Processing Webhook:", str(e))
        print(traceback.format_exc())  # Logs full traceback for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
