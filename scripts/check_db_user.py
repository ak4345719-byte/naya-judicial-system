
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def check_user():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(MONGO_URI)
    db = client["naya_court_db"]
    users_col = db["users"]
    
    user = users_col.find_one({"username": "admin"})
    if user:
        print(f"User 'admin' found.")
        print(f"Role: {user.get('role')}")
        print(f"Has password: {bool(user.get('password'))}")
        print(f"MFA Enabled: {user.get('mfa_enabled', False)}")
    else:
        print("User 'admin' NOT found!")

if __name__ == "__main__":
    check_user()
