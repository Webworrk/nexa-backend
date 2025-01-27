from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB connection
client = MongoClient(os.environ.get("MONGO_URI"))  # Use an environment variable for MongoDB URI
db = client['Nexa']

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Nexa Backend!"})

# Add a user
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    db['users'].insert_one(data)
    return jsonify({"message": "User added successfully!"}), 201

# Add a connection request
@app.route('/add_connection_request', methods=['POST'])
def add_connection_request():
    data = request.json
    db['connection_requests'].insert_one(data)
    return jsonify({"message": "Connection request added successfully!"}), 201

# Fetch all users
@app.route('/get_users', methods=['GET'])
def get_users():
    users = list(db['users'].find({}, {'_id': 0}))  # Omit MongoDB's default `_id`
    return jsonify(users), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import request

@app.route('/vapi-webhook', methods=['POST'])
def vapi_webhook():
    data = request.json

    # Map and rename fields for MongoDB compatibility
    if 'user_name' in data:
        data['name'] = data.pop('user_name')  # Rename user_name to name
    
    if 'goal_context' in data:
        if 'networking_goals' not in data:
            data['networking_goals'] = []  # Ensure the field exists
        data['networking_goals'].append({"goal": data.pop('goal_context'), "date": "2025-01-27"})  # Map goal_context into networking_goals
    
    # Optional: Check and create other fields if not present
    if 'connection_type' not in data:
        data['connection_type'] = None  # Default value if missing

    if 'meeting_time' not in data:
        data['meeting_time'] = None  # Default value if missing
    
    if 'requested_to' not in data:
        data['requested_to'] = None  # Default value if missing

    if 'context' not in data:
        data['context'] = None  # Default value if missing

    # Save the updated data to MongoDB
    db['Users'].insert_one(data)

    print("Vapi Data:", data)  # Debugging log
    return jsonify({"message": "Data received successfully!"}), 200


