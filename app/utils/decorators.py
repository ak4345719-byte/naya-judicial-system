from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.utils.logger import log_audit

def role_required(required_roles):
    """
    Decorator to enforce Role-Based Access Control.
    required_roles: list of strings (e.g. ["admin", "judge"])
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get("role")
                user_id = get_jwt_identity()

                if user_role not in required_roles:
                    log_audit(user_id, "UNAUTHORIZED_ACCESS_ATTEMPT", details={"required": required_roles, "actual": user_role, "endpoint": request.path}, ip_address=request.remote_addr)
                    return jsonify({"error": "Access denied: Insufficient permissions"}), 403

                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": str(e)}), 401
        return wrapper
    return decorator

def audit_log(action_name):
    """
    Decorator to automatically log successful API calls.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)
            try:
                
                try:
                    verify_jwt_in_request(optional=True)
                    user = get_jwt_identity() or "anonymous"
                except:
                    user = "anonymous"

                
                
                log_audit(user, action_name, details={"path": request.path, "method": request.method}, ip_address=request.remote_addr)
            except Exception as e:
                print(f"Audit Log Error: {e}")
            return response
        return wrapper
    return decorator
