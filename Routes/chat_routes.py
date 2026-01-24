from flask import Blueprint, request, jsonify
import os
from pymongo import MongoClient
import ollama
from google import genai
import re

def mask_pii(text):
    """Mask Aadhaar and Phone numbers."""
    if not text: return ""
    
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '<AADHAAR-HIDDEN>', text)
    
    text = re.sub(r'\b[6-9]\d{9}\b', '<PHONE-HIDDEN>', text)
    return text

chat_bp = Blueprint('chat_bp', __name__)


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

client = get_gemini_client()

def get_db():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    return client["naya_court_db"]

def ask_gemini(system_prompt, user_question):
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[system_prompt, user_question]
        )
        return response.text
    except Exception as e:
        return f"Gemini Error: {str(e)}"

def ask_ollama(system_prompt, user_question):
    try:
        response = ollama.chat(
            model='mistral', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_question}
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"Ollama Error: {str(e)}"

from openai import OpenAI
def ask_openai(system_prompt, user_question):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {str(e)}"

@chat_bp.route("/api/chat/ask", methods=["POST"])
def ask_question():
    data = request.json
    case_number = data.get("case_number")
    question = data.get("question")
    selected_model = data.get("model", "ollama") 
    language = data.get("language", "English")
    
    if not case_number or not question:
        return jsonify({"error": "Missing case_number or question"}), 400

    db = get_db()
    
    
    
    case_details = db["cases"].find_one({"caseNumber": case_number})
    case_meta_str = ""
    if case_details:
        case_meta_str = f"""
        CASE METADATA:
        - Title: {case_details.get('title', 'N/A')}
        - Type: {case_details.get('caseType', 'N/A')}
        - Status: {case_details.get('status', 'N/A')}
        - Filed Date: {case_details.get('filingDate', 'N/A')}
        - Petitioner: {case_details.get('petitioner', 'N/A')}
        - Respondent: {case_details.get('respondent', 'N/A')}
        """
    else:
        case_meta_str = "CASE METADATA: Case not registered in system."

    
    evidence_docs = list(db["evidence"].find({"case_number": case_number}))
    
    context_parts = [case_meta_str]
    for doc in evidence_docs:
        if doc.get("analysis"):
            context_parts.append(f"--- DOCUMENT: {doc.get('filename')} ---\n{doc.get('analysis')}")
        else:
            # Proactively note presence of unanalyzed docs
            context_parts.append(f"Document '{doc.get('filename')}' exists but has not been analyzed yet.")

    context_str = "\n\n".join(context_parts)
    
    if len(evidence_docs) == 0:
        context_str += "\n(No evidence files uploaded for this case yet.)"

    
    system_prompt = f"""
    You are a legal assistant for the Naya Judicial System.
    You are answering questions about Case Number: {case_number}.
    
    Here is the available evidence context:
    {context_str}
    
    Answer the user's question based strictly on this context. 
    If the answer is not in the context, say "I cannot find that information in the case files."
    
    IMPORTANT: Provide your response in {language}.
    """
    
    
    system_prompt = mask_pii(system_prompt)
    question = mask_pii(question)

    if selected_model == "gemini":
        answer = ask_gemini(system_prompt, question)
        
        if "Gemini Error" in answer:
            if "RESOURCE_EXHAUSTED" in answer or "429" in answer:
                print(f"⚠️ Gemini Chat Quota Exceeded. Switching to Ollama.")
            else:
                print(f"Gemini failed, falling back to Ollama: {answer}")
            
            fallback_answer = ask_ollama(system_prompt, question)
            answer = f"{fallback_answer}\n\n_(Note: Switched to local Mistral model due to Gemini quota limits.)_"
    elif selected_model == "openai":
        answer = ask_openai(system_prompt, question)
        if "OpenAI Error" in answer:
            print(f"OpenAI failed ({answer}), falling back to Ollama.")
            fallback = ask_ollama(system_prompt, question)
            answer = f"{fallback}\n\n_(Note: Switched to local Mistral model due to OpenAI quota limits.)_"
    else:
        answer = ask_ollama(system_prompt, question)

    return jsonify({"answer": answer})
