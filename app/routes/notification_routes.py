from flask import Blueprint, request, jsonify
import os
import uuid
from datetime import datetime
from pymongo import MongoClient

notification_bp = Blueprint('notification_bp', __name__)

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

@notification_bp.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get recent alerts."""
    db = get_db()
    
    notifs = list(db["notifications"].find().sort("date", -1).limit(15))
    for n in notifs:
        n["_id"] = str(n["_id"])
    
    
    unread_count = db["notifications"].count_documents({"read": False})
    
    return jsonify({"notifications": notifs, "unread_count": unread_count})

@notification_bp.route("/api/notifications/send", methods=["POST"])
def send_notification():
    """Simulate sending an SMS/Email (Demo Mode)."""
    data = request.json
    message = data.get("message")
    channel = data.get("type", "Info") 
    
    if not message:
        return jsonify({"error": "Message required"}), 400
        
    db = get_db()
    
    
    notif = {
        "id": str(uuid.uuid4()),
        "message": message,
        "type": channel, 
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "timestamp": datetime.now(),
        "read": False
    }
    db["notifications"].insert_one(notif)
    
    return jsonify({"success": True, "details": f"Simulated {channel} sent to user."})

@notification_bp.route("/api/notifications/mark-read", methods=["POST"])
def mark_read():
    """Mark all as read."""
    db = get_db()
    db["notifications"].update_many({}, {"$set": {"read": True}})
    return jsonify({"success": True})
