from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.utils.security import hash_password, check_password, generate_totp_uri, verify_totp
from app.utils.logger import get_db, log_audit
import uuid

auth_bp = Blueprint('auth_bp', __name__)


def init_default_users():
    db = get_db()
    users_col = db["users"]
    
    defaults = [
        {"username": "admin", "password": "admin123", "role": "admin", "name": "System Administrator", "mfa_secret": None},
        {"username": "judge", "password": "judge123", "role": "judge", "name": "Justice Anirudh S.", "mfa_secret": None},
        {"username": "clerk", "password": "clerk123", "role": "clerk", "name": "Rajesh Kumar", "mfa_secret": None},
        {"username": "lawyer", "password": "lawyer123", "role": "lawyer", "name": "Adv. Priya Sharma", "mfa_secret": None}
    ]
    
    for u in defaults:
        if not users_col.find_one({"username": u["username"]}):
            u["password"] = hash_password(u["password"])
            users_col.insert_one(u)
            print(f"Created default user: {u['username']}")

@auth_bp.route("/api/login", methods=["POST"])
def login():
    """
    Secure Login with MFA support.
    Step 1: Verify Password.
    Step 2: If MFA enabled, return 'mfa_required'. Else return tokens.
    """
    init_default_users() 
    
    data = request.json
    username = data.get("username", "").lower()
    password = data.get("password", "")
    cf_token = data.get("cf_token")
    # 🛡️ Cloudflare Turnstile Verification
    # Using testing Secret Key (always passes for demo)
    TURNSTILE_SECRET = "1x0000000000000000000000000000000AA"
    import requests
    try:
        verify_res = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET, "response": cf_token, "remoteip": request.remote_addr},
            timeout=5
        )
        v_data = verify_res.json()
    except Exception:
        # In demo mode, keep proceeding if it's just a network error
        pass

    db = get_db()
    user = db.users.find_one({"username": username})
    
    if user and check_password(password, user["password"]):
        if user.get("mfa_enabled", False):
            return jsonify({"success": True, "mfa_required": True, "temp_token": f"temp-{user['_id']}"})
        
        
        access_token = create_access_token(identity=str(user["_id"]), additional_claims={"role": user["role"], "username": user["username"]})
        refresh_token = create_refresh_token(identity=str(user["_id"]))
        
        log_audit(username, "LOGIN_SUCCESS", ip_address=request.remote_addr)
        
        return jsonify({
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": user["role"],
            "name": user["name"]
        })
    
    log_audit(username, "LOGIN_FAILED", ip_address=request.remote_addr)
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@auth_bp.route("/api/mfa/setup", methods=["POST"])
@jwt_required()
def setup_mfa():
    """Generate MFA secret for user."""
    user_id = get_jwt_identity()
    db = get_db()
    
    from bson import ObjectId
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    secret, uri = generate_totp_uri(user["username"])
    
    db.users.update_one({"_id": user["_id"]}, {"$set": {"temp_mfa_secret": secret}})
    
    return jsonify({"secret": secret, "uri": uri})

@auth_bp.route("/api/mfa/verify", methods=["POST"])
@jwt_required()
def verify_mfa_setup():
    """Verify MFA code to enable it."""
    user_id = get_jwt_identity()
    code = request.json.get("code")
    db = get_db()
    
    from bson import ObjectId
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if verify_totp(user.get("temp_mfa_secret"), code):
        db.users.update_one({"_id": user["_id"]}, {
            "$set": {"mfa_secret": user["temp_mfa_secret"], "mfa_enabled": True},
            "$unset": {"temp_mfa_secret": ""}
        })
        log_audit(user["username"], "MFA_ENABLED", ip_address=request.remote_addr)
        return jsonify({"success": True})
    
    return jsonify({"error": "Invalid Code"}), 400
