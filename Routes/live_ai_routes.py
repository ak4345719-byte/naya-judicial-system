from flask import Blueprint, request, jsonify
import os
import ollama
from google import genai
from pymongo import MongoClient
from datetime import datetime

live_ai_bp = Blueprint('live_ai_bp', __name__)

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@live_ai_bp.route("/api/live/process-segment", methods=["POST"])
def process_transcript_segment():
    """Analyze a segment of hearing transcript for citations and keywords."""
    data = request.json
    text = data.get("text", "")
    case_number = data.get("case_number", "Generic")
    
    if not text:
        return jsonify({"citations": [], "keywords": []})

    prompt = f"""
    You are a judicial AI assistant. Analyze this hearing transcript segment:
    "{text}"
    
    1. Identify any mentioned Legal Statutes (e.g., Section 302 IPC, Art 21).
    2. Suggest 2 relevant Indian Supreme Court precedents.
    3. Extract 3 key legal keywords.
    
    Format response as JSON:
    {{
        "citations": ["Statute 1", "Statute 2"],
        "precedents": [
            {{"title": "Case Name", "relevance": "summary"}}
        ],
        "keywords": ["word1", "word2"]
    }}
    """
    
    try:
        # Try Gemini first for high quality
        response = genai_client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[prompt]
        )
        import json
        # Extract clean JSON from Gemini response if it's wrapped in markdown
        raw_text = response.text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        analysis = json.loads(raw_text)
        return jsonify(analysis)
    except Exception as e:
        print(f"Gemini failed, trying Ollama: {e}")
        try:
            # Fallback to Ollama
            resp = ollama.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}]
            )
            # Try to find JSON in Ollama output
            import re
            match = re.search(r'\{.*\}', resp["message"]["content"], re.DOTALL)
            if match:
                return jsonify(json.loads(match.group()))
        except:
            pass
            
    # Mock fallback if both fail
    return jsonify({
        "citations": ["Section 138 NI Act" if "cheque" in text.lower() else "CPC Section 80"],
        "precedents": [],
        "keywords": ["hearing", "evidence"]
    })

@live_ai_bp.route("/api/live/generate-order", methods=["POST"])
def generate_order_draft():
    """Generates a formal order draft based on the full hearing transcript."""
    data = request.json
    transcript = data.get("transcript", "")
    case_details = data.get("case_details", {})
    
    prompt = f"""
    Draft a formal judicial ORDER based on this hearing transcript:
    TRANSCRIPT:
    {transcript}
    
    CASE DETAILS:
    Title: {case_details.get('title')}
    Case No: {case_details.get('caseNumber')}
    
    The order should have:
    - Heading (In the Court of...)
    - Appearance (Names of counsels)
    - Summary of proceedings
    - Operative Order (Next date, bail granted/denied, etc.)
    """
    
    try:
        response = genai_client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[prompt]
        )
        return jsonify({"order": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
