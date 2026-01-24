from flask import Blueprint, request, jsonify
from pymongo import MongoClient
import os
import uuid
from datetime import datetime

judge_bp = Blueprint('judge_bp', __name__)


def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

@judge_bp.route("/api/judges", methods=["GET"])
def get_judges():
    """Return list of judges with analytics."""
    db = get_db()
    judges_col = db["judges"]
    schedules_col = db["schedules"]
    
    judges = list(judges_col.find({}, {"_id": 0}))
    
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    for j in judges:
        
        sched = list(schedules_col.find({"judge_id": j["id"], "date": today_str}))
        cases_assigned = len(sched)
        total_minutes = sum([s.get("duration_minutes", 0) for s in sched])
        capacity = j.get("daily_capacity_minutes", 300)
        
        j["analytics"] = {
            "cases_today": cases_assigned,
            "minutes_booked": total_minutes,
            "utilization": round((total_minutes / capacity) * 100, 1) if capacity > 0 else 0
        }
        
    return jsonify(judges)

@judge_bp.route("/api/add-judge", methods=["POST"])
def add_judge():
    data = request.json
    db = get_db()
    judges_col = db["judges"]
    
    judge_doc = {
        "id": str(uuid.uuid4())[:8],
        "name": data.get("name"),
        "court": data.get("court"),
        "experience_years": int(data.get("experience_years", 0)),
        "specializations": data.get("specializations", []),  
        "daily_capacity_minutes": int(data.get("daily_capacity_minutes", 300)),
        "status": "Available" 
    }
    judges_col.insert_one(judge_doc)
    judge_doc.pop("_id", None)
    return jsonify({"success": True, "judge": judge_doc})

@judge_bp.route("/api/delete-judge/<judge_id>", methods=["DELETE"])
def delete_judge(judge_id):
    """Delete a judge by ID."""
    db = get_db()
    result = db["judges"].delete_one({"id": judge_id})
    if result.deleted_count > 0:
        return jsonify({"success": True, "message": "Judge deleted"})
    return jsonify({"error": "Judge not found"}), 404
