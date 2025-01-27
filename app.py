from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB connection
client = MongoClient(os.environ.get("MONGO_URI"))  # Use an environment variable for MongoDB URI
db = client['nexa_db']

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
