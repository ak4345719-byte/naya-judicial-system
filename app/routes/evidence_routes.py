from flask import Blueprint, request, jsonify
import os
import uuid
from datetime import datetime
from pymongo import MongoClient
from pymongo import MongoClient
import ollama
from cryptography.fernet import InvalidToken
from app.utils.security import encrypt_data, decrypt_data, calculate_sha256
import io

evidence_bp = Blueprint('evidence_bp', __name__)


from flask import current_app

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

@evidence_bp.route("/api/evidence/upload", methods=["POST"])
def upload_evidence():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    case_number = request.form.get('case_number')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not case_number:
        return jsonify({"error": "Case number is required"}), 400

    filename = f"{uuid.uuid4()}_{file.filename}"
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    filepath = os.path.join(upload_folder, filename)
    
    file_bytes = file.read()
    
    
    file_hash = calculate_sha256(file_bytes)
    
    
    encrypted_bytes = encrypt_data(file_bytes)
    
    
    with open(filepath, "wb") as f:
        f.write(encrypted_bytes)

    
    db = get_db()
    evidence_id = str(uuid.uuid4())
    
    evidence_doc = {
        "id": evidence_id,
        "case_number": case_number,
        "filename": file.filename,
        "filepath": filepath,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_hash": file_hash,  
        "analysis": None
    }
    db["evidence"].insert_one(evidence_doc)
    
    
    ledger_entry = {
        "evidence_id": evidence_id,
        "original_hash": file_hash,
        "timestamp": datetime.now(),
        "status": "Verified"
    }
    db["ledger"].insert_one(ledger_entry) 
    
    evidence_doc.pop("_id", None)
    
    return jsonify({"success": True, "evidence": evidence_doc})

@evidence_bp.route("/api/evidence/<path:case_number>", methods=["GET"])
def get_evidence(case_number):
    db = get_db()
    evidence_list = list(db["evidence"].find({"case_number": case_number}, {"_id": 0}))
    return jsonify(evidence_list)

@evidence_bp.route("/api/evidence/list", methods=["GET"])
def get_evidence_list():
    case_number = request.args.get("case_number")
    if not case_number:
         return jsonify([])
    db = get_db()
    evidence_list = list(db["evidence"].find({"case_number": case_number}, {"_id": 0}))
    return jsonify(evidence_list)

@evidence_bp.route("/api/evidence/analyze", methods=["POST"])
def analyze_evidence():
    data = request.json
    evidence_id = data.get("evidence_id")
    
    db = get_db()
    doc = db["evidence"].find_one({"id": evidence_id})
    
    if not doc:
        return jsonify({"error": "Document not found"}), 404
        
    filepath = doc["filepath"]
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found on server"}), 404
        
    
    content = ""
    try:
        lower_path = filepath.lower()
        if lower_path.endswith('.pdf'):
            import PyPDF2
            
            with open(filepath, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = decrypt_data(encrypted_data)
            
            with io.BytesIO(decrypted_data) as f_mem:
                reader = PyPDF2.PdfReader(f_mem)
                num_pages = len(reader.pages)
                
                for i in range(min(num_pages, 20)):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        content += page_text + "\n"
        elif any(lower_path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            # VISION PROCESSING START
            from google import genai
            from google.genai import types
            import base64
            
            with open(filepath, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = decrypt_data(encrypted_data)
            
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            
            # Convert decrypted bytes to PIL image or direct bytes for Vision
            prompt = "Analyze this judicial evidence image. Extract text, identify parties mentioned, and describe objects or scenes. Summarize legally."
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    types.Part.from_bytes(data=decrypted_data, mime_type="image/jpeg")
                ]
            )
            content = f"[VISION ANALYSIS]: {response.text}"
            # VISION PROCESSING END
        else:
            with open(filepath, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = decrypt_data(encrypted_data)
            content = decrypted_data.decode("utf-8", errors='ignore')
            
        

        if not content.strip():
            return jsonify({"error": "Could not extract text from document (file may be empty or encrypted PDF)."}), 400

        prompt = f"""
        Analyze the following legal document content:
        {content[:4000]}  # Limit context for speed
        
        Extract:
        1. Key Dates
        2. Involved Parties
        3. A brief Summary (2-3 sentences)
        
        Format as JSON if possible, or clear Section Headers.
        """
        
        try:
            response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
            analysis_result = response['message']['content']
        except Exception as ai_error:
            print(f"❌ Ollama Error: {ai_error}")
            return jsonify({"error": f"AI Service Error: {str(ai_error)}. Is Ollama running?"}), 503
        
        
        db["evidence"].update_one({"id": evidence_id}, {"$set": {"analysis": analysis_result}})
        
        return jsonify({"success": True, "analysis": analysis_result})
        
    except InvalidToken:
        return jsonify({"error": "Encryption Key Mismatch: This file was uploaded before the security update. Please delete and re-upload it."}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Analysis Failed: {e}")
        return jsonify({"error": str(e) or "Unknown Server Error (Check Console Logs)"}), 500

@evidence_bp.route("/api/evidence/verify", methods=["POST"])
def verify_integrity():
    """Verify file integrity against the Immutable Ledger."""
    data = request.json
    evidence_id = data.get("evidence_id")
    
    db = get_db()
    
    
    evidence = db["evidence"].find_one({"id": evidence_id})
    if not evidence:
        return jsonify({"error": "Evidence not found"}), 404
        
    filepath = evidence["filepath"]
    if not os.path.exists(filepath):
        return jsonify({"error": "File missing from disk"}), 404
        
    
    
    with open(filepath, "rb") as f:
        encrypted_data = f.read()
    
    try:
        decrypted_data = decrypt_data(encrypted_data)
        current_hash = calculate_sha256(decrypted_data)
    except Exception as e:
        return jsonify({"verified": False, "message": f"Decryption Failed (Tampered?): {str(e)}"})
    
    
    ledger = db["ledger"].find_one({"evidence_id": evidence_id})
    
    if not ledger:
        return jsonify({"verified": False, "message": "No Ledger Entry Found (Risk: High)"})
        
    original_hash = ledger["original_hash"]
    
    if current_hash == original_hash:
        return jsonify({
            "verified": True, 
            "message": "Blockchain Verified: Document is authentic.",
            "hash": current_hash
        })
    else:
        return jsonify({
            "verified": False, 
            "message": "TAMPERING DETECTED: File hash mismatch!",
            "expected": original_hash,
            "actual": current_hash
        })

@evidence_bp.route("/api/evidence/<string:evidence_id>", methods=["DELETE"])
def delete_evidence(evidence_id):
    try:
        db = get_db()
        evidence_doc = db["evidence"].find_one({"id": evidence_id})
        
        if not evidence_doc:
            return jsonify({"error": "Evidence not found"}), 404
            
        
        filepath = evidence_doc.get("filepath")
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"⚠️ Failed to delete file from disk: {e}")
        
        
        db["evidence"].delete_one({"id": evidence_id})
        
        return jsonify({"success": True, "message": "Evidence deleted successfully."})
        
    except Exception as e:
        print(f"❌ Delete Failed: {e}")
        return jsonify({"error": str(e)}), 500
