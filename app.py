from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

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

# VAPI webhook endpoint
@app.route('/vapi-webhook', methods=['POST'])
def vapi_webhook():
    try:
        # Parse incoming JSON data
        data = request.json
        print("Received data:", data)  # Debug log

        # Insert data into `webhooks` collection
        result = db['webhooks'].insert_one(data)
        print("Inserted ID:", result.inserted_id)  # Debug log

        # Return success response
        return jsonify({"message": "Data stored successfully", "id": str(result.inserted_id)}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Failed to store data"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
