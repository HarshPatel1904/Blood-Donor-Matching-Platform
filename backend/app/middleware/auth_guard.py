from functools import wraps
from flask import request, jsonify, g
from app.utils.jwt_util import decode_jwt_token
from app.repositories import get_repository


def token_required(f):
    """
    Decorator that verifies the Authorization Bearer JWT token.
    Attaches the verified user dictionary to Flask's global context (g.current_user).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({
                "success": False,
                "error": "Authorization header is missing. Token required."
            }), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "success": False,
                "error": "Invalid Authorization format. Expected: Bearer <token>"
            }), 401

        token = parts[1]
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({
                "success": False,
                "error": "Token is invalid or has expired. Please log in again."
            }), 401

        repo = get_repository()
        user = repo.get_user_by_id(payload["sub"])
        if not user:
            return jsonify({
                "success": False,
                "error": "User account associated with this token no longer exists."
            }), 401

        if user.get("is_active") != 1:
            return jsonify({
                "success": False,
                "error": "This account has been deactivated or suspended."
            }), 403

        # Store authenticated user in request context
        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def role_required(allowed_roles: list):
    """
    Decorator that checks if the authenticated user possesses one of the allowed roles.
    Must be stacked after @token_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, "current_user") or not g.current_user:
                return jsonify({
                    "success": False,
                    "error": "Authentication required prior to role verification."
                }), 401

            user_role = g.current_user.get("role")
            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": f"Access denied. Required roles: {allowed_roles}. Current role: '{user_role}'."
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator