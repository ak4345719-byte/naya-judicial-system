import os
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "naya_court_db"
COLLECTION_NAME = "cases"

def reset_db():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        print(f"Connecting to {DB_NAME}.{COLLECTION_NAME}...")
        
        
        count_before = db[COLLECTION_NAME].count_documents({})
        print(f"Current document count: {count_before}")
        
        if count_before > 0:
            db[COLLECTION_NAME].drop()
            print("✅ Collection dropped successfully.")
        else:
            print("ℹ️ Collection is already empty.")
            
        print("Ready for re-migration on next app startup.")
        
    except Exception as e:
        print(f"❌ Error resetting DB: {e}")

if __name__ == "__main__":
    reset_db()
