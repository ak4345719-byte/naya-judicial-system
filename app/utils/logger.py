from datetime import datetime
from pymongo import MongoClient
import os


def get_db():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(MONGO_URI)
    return client["naya_court_db"]

def log_audit(user_id: str, action: str, target_id: str = None, details: dict = None, ip_address: str = None):
    """
    Log sensitive actions to the audit_logs collection.
    
    Args:
        user_id (str): ID or Username of the actor.
        action (str): Description of the action (e.g., 'LOGIN', 'VIEW_CASE').
        target_id (str): ID of the object being acted upon (e.g., Case Number).
        details (dict): Additional context.
        ip_address (str): IP address of the request.
    """
    try:
        db = get_db()
        log_entry = {
            "timestamp": datetime.now(),
            "user_id": user_id,
            "action": action.upper(),
            "target_id": target_id,
            "details": details or {},
            "ip_address": ip_address
        }
        db.audit_logs.insert_one(log_entry)
    except Exception as e:
        
        print(f"CRITICAL: Failed to write audit log: {e} | Entry: {user_id} {action}")
