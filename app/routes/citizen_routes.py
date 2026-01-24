from flask import Blueprint, request, jsonify, render_template
import os
from pymongo import MongoClient

citizen_bp = Blueprint('citizen_bp', __name__)

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

@citizen_bp.route("/citizen")
def citizen_portal():
    return render_template("citizen-portal.html")

@citizen_bp.route("/api/public/search", methods=["GET"])
def public_search():
    case_number = request.args.get("caseNumber")
    if not case_number:
        return jsonify({"error": "Case Number required"}), 400
        
    db = get_db()
    
    
    case = db["cases"].find_one({"caseNumber": case_number}, {"_id": 0})
    
    if not case:
        return jsonify({"error": "Case not found"}), 404
        
    # Extract names from title if available
    title = case.get("title", "")
    plaintiff = "Unknown"
    defendant = "Unknown"
    
    if " Vs " in title:
        parts = title.split(" Vs ")
        plaintiff = parts[0].strip()
        defendant = parts[1].strip()
    elif " VS " in title:
        parts = title.split(" VS ")
        plaintiff = parts[0].strip()
        defendant = parts[1].strip()
        
    public_data = {
        "caseNumber": case.get("caseNumber"),
        "status": case.get("status"),
        "filingDate": case.get("filingDate"),
        "hearingDate": case.get("hearingDate", "Not Scheduled"),
        "caseType": case.get("caseType"),
        "plaintiff": mask_name(plaintiff),
        "defendant": mask_name(defendant)
    }
    
    return jsonify(public_data)

def mask_name(name):
    if not name or name == "Unknown": return "Unknown"
    name = str(name).strip()
    if len(name) < 3: return "***"
    return name[0] + "***" + name[-1]
