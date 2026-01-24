from flask import Blueprint, request, jsonify
from pymongo import MongoClient
import os
import pickle
from datetime import datetime, timedelta
import random

schedule_bp = Blueprint('schedule_bp', __name__)

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]


MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "hearing_model.pkl")
model = None
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
except:
    pass

def predict_hearing_duration(case_data):
    """Predict duration using ML model or fallback."""
    if model:
        try:
            witnesses = int(case_data.get("witnesses", 0))
            advocates = int(case_data.get("advocates", 0))
            previous = int(case_data.get("previous_hearings", 0))
            pred = model.predict([[witnesses, advocates, previous]])
            return round(float(pred[0]), 2)
        except:
            pass
    
    base = 15
    base += int(case_data.get("witnesses", 0)) * 10
    return min(base, 120)  

@schedule_bp.route("/api/daily-schedule", methods=["GET"])
def get_daily_schedule():
    """Get schedule for a specific date."""
    db = get_db()
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    schedule = list(db["schedules"].find({"date": date_str}, {"_id": 0}))
    return jsonify(schedule)

@schedule_bp.route("/api/reschedule", methods=["POST"])
def reschedule_ai():
    """AI Auto-Scheduling Logic (Optimized)."""
    db = get_db()
    cases_col = db["cases"]
    judges_col = db["judges"]
    schedules_col = db["schedules"]
    
    date_str = request.json.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    
    schedules_col.delete_many({"date": date_str, "status": "Upcoming"})
    
    
    pending_cases = list(cases_col.find({"status": "Pending"}))
    available_judges = list(judges_col.find({"status": "Available"}, {"_id": 0}))
    
    if not available_judges:
        return jsonify({"error": "No judges available"}), 400

    new_schedule = []
    
    
    
    
    pending_cases.sort(key=lambda c: (
        1 if c.get("caseType") == "Criminal" else 2, 
        0 if c.get("priority") == "High" else 1      
    ))

    
    
    judge_timetrack = {j["id"]: datetime.strptime(f"{date_str} 10:00", "%Y-%m-%d %H:%M") for j in available_judges}

    for case in pending_cases:
        duration = predict_hearing_duration(case)
        buffer_time = 15 
        
        best_judge = None
        min_load = float('inf')
        
        
        for judge in available_judges:
            specializations = [s.lower() for s in judge.get("specializations", [])]
            case_type = case.get("caseType", "").lower()
            
            
            is_expert = any(s in case_type for s in specializations)
            
            current_time = judge_timetrack[judge["id"]]
            day_end = datetime.strptime(f"{date_str} 17:00", "%Y-%m-%d %H:%M")
            
            if current_time + timedelta(minutes=duration) <= day_end:
                
                finish_timestamp = current_time.timestamp()
                score = finish_timestamp
                if is_expert:
                    score -= 3600 
                    
                if score < min_load:
                    min_load = score
                    best_judge = judge
        
        
        if not best_judge:
             for judge in available_judges:
                current_time = judge_timetrack[judge["id"]]
                day_end = datetime.strptime(f"{date_str} 17:00", "%Y-%m-%d %H:%M")
                if current_time + timedelta(minutes=duration) <= day_end:
                    best_judge = judge
                    break
        
        if best_judge:
            start_time = judge_timetrack[best_judge["id"]]
            end_time = start_time + timedelta(minutes=duration)
            
            risk = "Low"
            if duration > 60: risk = "Medium"
            if duration > 90: risk = "High"

            
            demo_courts = ["District Court Complex", "High Court Annex", "City Civil Court"]
            demo_rooms = ["Room 101", "Hall 3", "Room 4B", "Chamber 2", "Court Hall 7"]
            
            sched_entry = {
                "case_number": case.get("caseNumber"),
                "case_type": case.get("caseType"),
                "judge_id": best_judge["id"],
                "judge_name": best_judge["name"],
                "date": date_str,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "duration_minutes": duration,
                "risk_level": risk,
                "status": "Upcoming",
                "court_name": random.choice(demo_courts),
                "court_room": random.choice(demo_rooms)
            }
            new_schedule.append(sched_entry)
            schedules_col.insert_one(sched_entry)
            
            cases_col.update_one(
                {"caseNumber": case.get("caseNumber")},
                {"$set": {"status": "Scheduled", "hearingDate": date_str}}
            )
            
            judge_timetrack[best_judge["id"]] = end_time + timedelta(minutes=buffer_time)

    return jsonify({"success": True, "scheduled_count": len(new_schedule)})
