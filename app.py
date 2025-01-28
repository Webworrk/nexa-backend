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

        # Extract and format meeting date and time
        meeting_date = "Not Provided"
        meeting_time = "Not Provided"
        for msg in messages:
            text = msg.get("message", "")
            date_match = re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s(\d{1,2}),\s(\d{4})\b', text)
            time_match = re.search(r'\b(\d{1,2}):(\d{2})\s?(AM|PM)\b', text, re.IGNORECASE)
            
            if date_match:
                month, day, year = date_match.groups()
                month_number = datetime.strptime(month, "%B").month  # Convert month name to number
                meeting_date = f"{int(day):02d}-{int(month_number):02d}-{year}"
            
            if time_match:
                hour, minute, am_pm = time_match.groups()
                meeting_time = f"{hour}:{minute} {am_pm.upper()}"

        extracted_data = {
            "nexa_id": message.get("nexa_id", "Unknown"),
            "user_name": message.get("user_name", "Unknown"),
            "phone": message.get("phone", ""),
            "email": message.get("email", ""),
            "profession_summary": {
                "industry": message.get("industry", ""),
                "experience": message.get("experience", ""),
                "skills": message.get("skills", []),
                "bio": message.get("profession", "")
            },
            "networking_goals": [{
                "goal": analysis.get("summary", ""),
                "status": "Active",
                "created_at": datetime.now().strftime("%d-%m-%Y"),
                "closed_at": None
            }],
            "meeting_history": [{
                "date": meeting_date,
                "time": meeting_time,
                "context": "Vapi Webhook Data Processing"
            }],
            "requested_to": message.get("requested_to", "Not Provided"),
            "context": "Vapi Webhook Data Processing"
        }

        print("📌 Extracted Data:", extracted_data)

        # Check if user already exists
        existing_user = db.webhooks.find_one({"nexa_id": extracted_data["nexa_id"]})
        if existing_user:
            # Append new networking goal
            db.webhooks.update_one(
                {"nexa_id": extracted_data["nexa_id"]},
                {"$set": {"profession_summary": extracted_data["profession_summary"]},
                 "$push": {
                     "networking_goals": extracted_data["networking_goals"][0],
                     "meeting_history": extracted_data["meeting_history"][0]
                 }}
            )
            print("✅ User data updated!")
        else:
            # Insert new user profile
            result = db.webhooks.insert_one(extracted_data)
            print("✅ New user data stored, ID:", result.inserted_id)

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        print("❌ Error Processing Webhook:", str(e))
        print(traceback.format_exc())  # Logs full traceback for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
