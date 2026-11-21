from flask import Blueprint, request, jsonify, g
from app.services.admin_service import AdminService
from app.middleware.auth_guard import token_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
admin_service = AdminService()


@admin_bp.route("/stats", methods=["GET"])
@token_required
@role_required(["admin"])
def get_stats():
    """Returns platform overview counts and operational health."""
    stats = admin_service.get_dashboard_statistics()
    return jsonify({"success": True, "data": stats}), 200


@admin_bp.route("/hospitals", methods=["GET"])
@token_required
@role_required(["admin"])
def list_hospitals():
    """Lists hospitals, optional query param: ?status=pending|verified|rejected."""
    status_filter = request.args.get("status")
    hospitals = admin_service.list_hospitals(verification_status=status_filter)
    return jsonify({"success": True, "data": hospitals, "count": len(hospitals)}), 200


@admin_bp.route("/hospitals/<hospital_id>/verify", methods=["PATCH"])
@token_required
@role_required(["admin"])
def verify_hospital(hospital_id: str):
    """Verifies or rejects a registered hospital account."""
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    notes = data.get("notes")

    if not status:
        return jsonify({"success": False, "error": "'status' (verified/rejected) is required."}), 400

    admin_user_id = g.current_user["user_id"]
    ip_addr = request.remote_addr or "127.0.0.1"

    success, message, result = admin_service.verify_hospital(
        admin_user_id=admin_user_id,
        hospital_id=hospital_id,
        status=status,
        notes=notes,
        ip_address=ip_addr
    )

    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 200


@admin_bp.route("/requests", methods=["GET"])
@token_required
@role_required(["admin"])
def list_requests():
    """Lists blood requests with optional ?verification_status= and ?request_status= filters."""
    verif_status = request.args.get("verification_status")
    req_status = request.args.get("request_status")

    requests_list = admin_service.list_blood_requests(
        verification_status=verif_status,
        request_status=req_status
    )
    return jsonify({"success": True, "data": requests_list, "count": len(requests_list)}), 200


@admin_bp.route("/requests/<request_id>/verify", methods=["PATCH"])
@token_required
@role_required(["admin"])
def verify_request(request_id: str):
    """Approves, rejects, or holds an individual blood request."""
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    notes = data.get("notes")

    if not status:
        return jsonify({"success": False, "error": "'status' (approved/rejected/on_hold) is required."}), 400

    admin_user_id = g.current_user["user_id"]
    ip_addr = request.remote_addr or "127.0.0.1"

    success, message, result = admin_service.review_blood_request(
        admin_user_id=admin_user_id,
        request_id=request_id,
        status=status,
        notes=notes,
        ip_address=ip_addr
    )

    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 200


@admin_bp.route("/users/<target_user_id>/status", methods=["PATCH"])
@token_required
@role_required(["admin"])
def update_user_status(target_user_id: str):
    """Suspends or reactivates a user account."""
    data = request.get_json(silent=True) or {}
    if "is_active" not in data:
        return jsonify({"success": False, "error": "'is_active' (boolean) is required."}), 400

    is_active = bool(data["is_active"])
    reason = data.get("reason")
    admin_user_id = g.current_user["user_id"]
    ip_addr = request.remote_addr or "127.0.0.1"

    success, message = admin_service.toggle_user_active_status(
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        is_active=is_active,
        reason=reason,
        ip_address=ip_addr
    )

    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message}), 200


@admin_bp.route("/audit-logs", methods=["GET"])
@token_required
@role_required(["admin"])
def get_audit_logs():
    """Lists audit logs."""
    limit = int(request.args.get("limit", 100))
    logs = admin_service.list_audit_logs(limit=limit)
    return jsonify({"success": True, "data": logs, "count": len(logs)}), 200