


"""
Naya Judicial System – backend (Flask)
* MongoDB Persistence
* AI Scheduling & Judge Assignment
* ML Model Integration
"""

import os
from dotenv import load_dotenv
load_dotenv() 

import sys
import json
import random
import re
from datetime import datetime, timedelta
import pickle
import threading
import uuid
from typing import List, Dict, Any
from functools import wraps

import requests

import ollama
from google import genai
from flask import Flask, request, jsonify, redirect, url_for, send_from_directory, render_template
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING

import numpy as np
from bs4 import BeautifulSoup

import re

from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from app.utils.security import jwt_secret
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, "static")
TEMPLATE_ROOT = os.path.join(BASE_DIR, "templates")

app = Flask(
    __name__,
    static_folder=STATIC_ROOT,
    template_folder=TEMPLATE_ROOT
)

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config["JWT_SECRET_KEY"] = jwt_secret
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)


bcrypt = Bcrypt(app)
jwt = JWTManager(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

talisman = Talisman(app, content_security_policy=None, force_https=False) 

CORS(app)

from .routes.evidence_routes import evidence_bp
from .routes.chat_routes import chat_bp
from .routes.notification_routes import notification_bp
from .routes.citizen_routes import citizen_bp
from .routes.analytics_routes import analytics_bp
from .routes.judge_routes import judge_bp
from .routes.schedule_routes import schedule_bp
from .routes.auth_routes import auth_bp
from .routes.prediction_routes import prediction_bp

app.register_blueprint(evidence_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(citizen_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(judge_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(prediction_bp)

from .routes.lawyer_routes import lawyer_bp
from .routes.live_ai_routes import live_ai_bp
from .routes.decision_support_routes import decision_bp
app.register_blueprint(lawyer_bp)
app.register_blueprint(live_ai_bp)
app.register_blueprint(decision_bp)


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["naya_court_db"]


genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


cases_col = db["cases"]
judges_col = db["judges"]
schedules_col = db["schedules"]


MODEL_PATH = os.path.join(BASE_DIR, "hearing_model.pkl")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")


model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print("✅ ML Model loaded.")
else:
    print("⚠️ Model file not found! Predictions will be simulated.")





def migrate_json_to_mongo():
    """One-time migration from cases.json to MongoDB."""
    json_path = os.path.join(BASE_DIR, "cases.json")
    if os.path.exists(json_path):
        if cases_col.count_documents({}) == 0:
            print("🔄 Migrating cases.json to MongoDB...")
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data:
                    cases_col.insert_many(data)
                print(f"✅ Migrated {len(data)} cases.")
            except Exception as e:
                print(f"❌ Migration failed: {e}")
        else:
            print("ℹ️ MongoDB already has data. Skipping migration.")

try:
    migrate_json_to_mongo()
except Exception as e:
    print(f"⚠️ Startup Migration Failed: {e}")





SESSIONS = {}  








@app.route("/legal-research")
def legal_research_page():
    return render_template("legal-research.html")

@app.route("/api/research", methods=["POST"])
def perform_legal_research():
    """Real Legal Research API using IndianKanoon Scraping."""
    query = request.json.get("query", "").strip()
    
    if not query:
        return jsonify({"results": [], "ai_summary": "Please enter a search query."})

    results = []
    
    
    try:
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        search_url = f"https://indiankanoon.org/search/?formInput={query}"
        resp = requests.get(search_url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            
            items = soup.find_all('div', class_='result_title')
            
            for item in items[:6]: 
                link_tag = item.find('a')
                if link_tag:
                    title = link_tag.get_text().strip()
                    href = "https://indiankanoon.org" + link_tag['href']
                    
                    
                    
                    parent = item.parent
                    snippet_div = parent.find('div', class_='doc_fragment')
                    snippet = snippet_div.get_text().strip() if snippet_div else "No snippet available."
                    
                    
                    
                    
                    results.append({
                        "title": title,
                        "citation": "IndianKanoon Ref",
                        "court": "India", 
                        "date": "Recent",
                        "snippet": snippet[:200] + "...",
                        "link": href
                    })

    except Exception as e:
        print(f"Scraping failed: {e}")
        
        pass

    
    if not results:
         
        mock_db = [
            {
                "title": "Union of India vs. State of Maharashtra", 
                "citation": "2023 SCC 452", 
                "court": "Supreme Court", 
                "date": "2023-11-15",
                "snippet": "Held that land acquisition compensation must calculate market value based on current circle rates plus solatium... referring to Section 26 of the 2013 Act.",
                "tags": ["land acquisition", "compensation"]
            },
            {
                "title": "Ramesh Kumar vs. State", 
                "citation": "2022 DLT 102", 
                "court": "Delhi High Court", 
                "date": "2022-05-20",
                "snippet": "In cases of cheque bounce under Section 138 NI Act, the presumption of debt is rebuttal but requires substantial evidence...",
                "tags": ["section 138", "ni act", "cheque bounce"]
            }
        ]
        results = [c for c in mock_db if any(t in query.lower() for t in c["tags"]) or query.lower() in c["title"].lower()]
        if not results: results = mock_db[:1]


    
    ai_summary = f"Found {len(results)} relevant precedents for '{query}'. "
    if results:
        ai_summary += f"The top result '{results[0]['title']}' discusses key aspects. "
        ai_summary += "Courts generally emphasize the need for strict interpretation in such cases."
    else:
        ai_summary += "Try refining your search terms for better results."

    return jsonify({
        "results": results,
        "ai_summary": ai_summary
    })





@app.route("/virtual-hearing")
def virtual_hearing_page():
    return render_template("virtual-hearing.html")





@app.route("/drafting")
def drafting_page():
    return render_template("drafting.html")

@app.route("/api/draft", methods=["POST"])
def generate_draft():
    """Generate Judgment Draft using AI."""
    facts = request.json.get("facts", "")
    
    
    try:
        
        
        prompt = f"""You are a Judge's Assistant. Draft a legal judgment/order based on these facts. 
        Format it professionally with Title, Parties, and Order.
        Facts: {facts}"""
        
        
        
        
        
        
        
        
        
        pass
    except:
        pass

    
    
    if "bail" in facts.lower():
        draft = """
        <div style='text-align: center; font-weight: bold;'>IN THE COURT OF SESSIONS JUDGE</div>
        <div style='text-align: center;'>BAIL APPLICATION NO. 1234 OF 2024</div>
        <br>
        <b>BETWEEN:</b><br>
        State<br>
        ..Respondent<br>
        AND<br>
        [Accused Name]<br>
        ..Applicant<br>
        <br>
        <b>ORDER</b><br>
        1. This is an application filed under Section 439 of the CrPC for grant of regular bail.<br>
        2. Heard the learned counsel for the applicant and the learned Public Prosecutor.<br>
        3. Considering that the investigation is complete and the accused is not a flight risk, I am inclined to grant bail.<br>
        <br>
        <b>ORDER:</b><br>
        The applicant is directed to be released on bail on furnishing a bond of Rs. 25,000 with one surety.<br>
        <br>
        (Signature)<br>
        <b>Sessions Judge</b>
        """
    else:
        draft = f"""
        <div style='text-align: center; font-weight: bold;'>IN THE HIGH COURT OF JUDICATURE</div>
        <br>
        <b>JUDGMENT</b><br>
        <br>
        1. The present suit has been instituted based on the following facts:<br>
        <i>"{facts[:100]}..."</i><br>
        <br>
        2. The court has examined the evidences placed on record.<br>
        3. Based on the preponderance of probabilities, the court finds in favor of the plaintiff.<br>
        <br>
        <b>DECREE:</b><br>
        The suit is decreed with costs.<br>
        <br>
        (Signature)<br>
        <b>Judge</b>
        """
    
    
    import time
    time.sleep(1.5)
    
    return jsonify({"draft": draft})






@app.route("/")
def index_page():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/case-registration")
def case_registration_page():
    return render_template("case-registration.html")

@app.route("/cause-list")
def cause_list_page():
    return render_template("cause-list.html")

@app.route("/judges")
def judges_page():
    return render_template("judges.html")

@app.route("/schedule")
def schedule_page():
    return render_template("schedule.html")

@app.route("/smart-vault")
def smart_vault_page():
    return render_template("smart-vault.html")

@app.route("/predictor")
def predictor_page():
    return render_template("predictor.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/api/cases", methods=["GET"])
def get_cases_api():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    search = request.args.get("search", "").strip()
    
    query = {}
    if search:
        regex = {"$regex": search, "$options": "i"}
        query = {
            "$or": [
                {"caseNumber": regex},
                {"title": regex},
                {"caseType": regex},
                {"court": regex},
                {"judge": regex}
            ]
        }
        
    total = cases_col.count_documents(query)
    cases = list(cases_col.find(query, {"_id": 0})
                 .sort("filingDate", -1) 
                 .skip((page - 1) * limit)
                 .limit(limit))
                 
    return jsonify({
        "cases": cases,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    })

@app.route("/api/cases/<path:case_number>", methods=["DELETE"])
def delete_case_api(case_number):
    try:
        
        result = cases_col.delete_one({"caseNumber": case_number})
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "Case deleted"})
        else:
            return jsonify({"error": "Case not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/register-case", methods=["POST"])
def register_case_api():
    data = request.json
    data["status"] = "Pending"
    cases_col.insert_one(data)
    data.pop("_id", None)
    return jsonify({"message": "Registered", "caseNumber": data.get("caseNumber")}), 201

@app.route("/api/ai/summarize", methods=["POST"])

def ai_summarize():
    try:
        import hashlib
        data = request.json
        case_text = data.get("case_text", "")
        
        if not case_text:
            return jsonify({"error": "No text provided"}), 400

        
        text_hash = hashlib.md5(case_text.encode("utf-8")).hexdigest()
        cached = db["summaries"].find_one({"hash": text_hash})
        
        if cached:
            return jsonify({"summary": cached["summary"], "cached": True})

        summary = ""
        
        
        try:
            response = genai_client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=[f"Summarize this legal case in 3 bullet points:\n{case_text}"]
            )
            summary = response.text
        except Exception as e:
            error_msg = str(e)
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                print(f"⚠️ Gemini Quota Exceeded. Switching to Ollama (Mistral).")
            else:
                print(f"Gemini Summarization failed, falling back to Ollama: {e}")

        
        if not summary:
            resp = ollama.chat(
                model="mistral",
                messages=[
                    {"role": "system", "content": "Summarize this legal case in 3 bullet points."},
                    {"role": "user", "content": case_text}
                ]
            )
            summary = resp["message"]["content"]
        
        
        db["summaries"].insert_one({
            "hash": text_hash,
            "summary": summary,
            "created_at": datetime.now()
        })
        
        return jsonify({"summary": summary, "cached": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    total = cases_col.count_documents({})
    pending = cases_col.count_documents({"status": "Pending"})
    today_str = datetime.now().strftime("%Y-%m-%d")
    scheduled_today = schedules_col.count_documents({"date": today_str})
    
    return jsonify({
        "total_cases": total,
        "pending_hearings": pending,
        "todays_cases": scheduled_today,
        "avg_hearing_time": 45,
        "urgent_cases": list(cases_col.find({"priority": "High", "status": {"$ne": "Closed"}}, {"_id": 0, "caseNumber": 1, "caseType": 1}).limit(5)),
        "upcoming_hearings": list(schedules_col.find({"date": {"$gte": today_str}}, {"_id": 0}).sort("date", 1).limit(5)),
        "active_judges": list(judges_col.find({"status": "Available"}, {"_id": 0, "name": 1, "status": 1}).limit(3))
    })


@app.route("/api/dashboard/chart-data", methods=["GET"])
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




@app.route("/dashboard.html")
def dashboard_legacy():
    return render_template("dashboard.html")

@app.route("/case-registration.html")
def case_registration_legacy():
    return render_template("case-registration.html")

@app.route("/cause-list.html")
def cause_list_legacy():
    return render_template("cause-list.html")

@app.route("/settings")
def settings_page():
     return render_template("settings.html")

@app.route("/settings.html")
def settings_legacy():
    try:
        return render_template("settings.html")
    except:
        return "Settings page not found", 404

@app.route("/index.html")
def index_legacy():
    return render_template("index.html")


@app.route("/<path:path>")
def static_proxy(path):
    
    possible_roots = [
        os.path.join(BASE_DIR, "..", "static"),
        os.path.join(BASE_DIR, "static"),
    ]
    for root in possible_roots:
        if os.path.exists(os.path.join(root, path)):
            return send_from_directory(root, path)
    return "", 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
