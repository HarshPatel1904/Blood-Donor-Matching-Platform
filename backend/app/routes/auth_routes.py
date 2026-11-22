from flask import Blueprint, request, jsonify, g
from app.config import Config
from app.services.auth_service import AuthService
from app.middleware.auth_guard import token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
auth_service = AuthService()


@auth_bp.route("/register/donor", methods=["POST"])
def register_donor():
    data = request.get_json(silent=True) or {}
    success, message, result = auth_service.register_donor(data)
    if not success:
        return jsonify({"success": False, "error": message}), 400
    return jsonify({"success": True, "message": message, "data": result}), 201


@auth_bp.route("/register/requester", methods=["POST"])
def register_requester():
    data = request.get_json(silent=True) or {}
    success, message, result = auth_service.register_requester(data)
    if not success:
        return jsonify({"success": False, "error": message}), 400
    return jsonify({"success": True, "message": message, "data": result}), 201


@auth_bp.route("/register/hospital", methods=["POST"])
def register_hospital():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        file = None
    else:
        data = request.form.to_dict()
        file = request.files.get("license_doc") or request.files.get("document")
    success, message, result = auth_service.register_hospital(data, uploaded_file=file)
    if not success:
        return jsonify({"success": False, "error": message}), 400
    return jsonify({"success": True, "message": message, "data": result}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    expected_role = data.get("role")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    success, message, result = auth_service.login(email, password, expected_role=expected_role)
    if not success:
        return jsonify({"success": False, "error": message}), 401

    return jsonify({"success": True, "message": message, "data": result}), 200


@auth_bp.route("/admin-portal", methods=["POST"])
def admin_portal_session():
    """Establishes an admin session strictly for configured admin portal origins."""
    origin = (request.headers.get("Origin") or "").rstrip("/")
    allowed_admin_origins = list(dict.fromkeys([
        *Config.ADMIN_PORTAL_ORIGINS,
        *[u for u in getattr(Config, "FRONTEND_URLS", []) if "admin" in u.lower()],
    ]))
    if origin not in allowed_admin_origins:
        return jsonify({"success": False, "error": "Direct admin portal access is restricted to configured admin origins."}), 403

    success, message, result = auth_service.issue_local_admin_portal_session()
    if not success:
        return jsonify({"success": False, "error": message}), 404

    return jsonify({"success": True, "message": message, "data": result}), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me():
    user_id = g.current_user["user_id"]
    profile = auth_service.get_current_user_profile(user_id)
    if not profile:
        return jsonify({"success": False, "error": "User not found."}), 404
    return jsonify({"success": True, "data": profile}), 200