from flask import Blueprint, jsonify, request
import os
from pymongo import MongoClient
import random

dashboard_bp = Blueprint("dashboard", __name__)

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

@dashboard_bp.route("/api/dashboard/stats")
def dashboard_stats():
    db = get_db()
    total_cases = db.cases.count_documents({})
    pending = db.cases.count_documents({"status": "Pending"})
    
    return jsonify({
        "total_cases": total_cases,
        "pending_hearings": pending
    })

@dashboard_bp.route("/api/dashboard/chart-data")
def dashboard_chart_data():
    """
    Returns mock monthly data for the 'Cases Filed vs. Disposed' chart.
    """
    data = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
        "filed": [45, 52, 38, 65, 48, 59, 62],
        "disposed": [40, 48, 45, 60, 55, 68, 70]
    }
    return jsonify(data)

@dashboard_bp.route("/api/seed-data", methods=["POST"])
def seed_data():
    """Populates MongoDB with demo data."""
    try:
        db = get_db()
        
        # Clear existing data
        db.cases.delete_many({})
        db.judges.delete_many({})
        db.schedules.delete_many({})
        
        # Insert Judges
        judges = [
            {"id": "J01", "name": "Hon. Anirudh S.", "status": "Available", "specializations": ["Criminal", "Constitutional"]},
            {"id": "J02", "name": "Hon. Sarah Jenkins", "status": "Available", "specializations": ["Civil", "Family"]},
            {"id": "J03", "name": "Hon. Rajesh Kumar", "status": "Available", "specializations": ["Corporate", "Tax"]}
        ]
        db.judges.insert_many(judges)

        # Insert Demo Cases
        case_types = ["Criminal", "Civil", "Family", "Corporate"]
        statuses = ["Pending", "Scheduled", "Closed"]
        
        demo_cases = []
        for i in range(1, 16):
            c_type = random.choice(case_types)
            status = "Pending" if i > 5 else random.choice(statuses) 
            
            case_doc = {
                "caseNumber": f"DEMO-2024-{100+i}",
                "title": f"Demo Case {i} vs State",
                "caseType": c_type,
                "complexity": random.randint(1, 10),
                "witnesses": random.randint(1, 5),
                "advocates": random.randint(1, 3),
                "status": status,
                "description": f"This is a sample {c_type} case regarding a dispute in sector {i}.",
                "priority": random.choice(["Normal", "High"]),
                "filingDate": "2024-01-01"
            }
            demo_cases.append(case_doc)
            
        db.cases.insert_many(demo_cases)
        
        return jsonify({"success": True, "message": "MongoDB populated with Demo Data!"})
        
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
