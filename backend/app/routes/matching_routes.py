from flask import Blueprint, request, jsonify, g
from app.services.matching_service import MatchingService
from app.repositories import get_repository
from app.middleware.auth_guard import token_required, role_required

matching_bp = Blueprint("matching", __name__, url_prefix="/api/matching")
matching_service = MatchingService()
repo = get_repository()


@matching_bp.route("/<request_id>/preview", methods=["GET"])
@token_required
def preview_matches(request_id: str):
    """
    Previews matching donors within a given radius (default: 10 km).
    Does not notify donors or change request status.
    """
    radius_km = float(request.args.get("radius", 10.0))
    success, message, result = matching_service.find_matching_donors(request_id, radius_km)
    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 200


@matching_bp.route("/<request_id>/dispatch", methods=["POST"])
@token_required
def dispatch_request(request_id: str):
    """
    Finds matching donors, dispatches email notifications, initializes response tracking,
    and transitions request_status to 'donors_notified'.
    Authorized roles: requester (owner), hospital (owner), or admin.
    """
    data = request.get_json(silent=True) or {}
    radius_km = float(data.get("radius", 10.0))

    user_id = g.current_user["user_id"]
    user_role = g.current_user["role"]
    ip_addr = request.remote_addr or "127.0.0.1"

    # Verify authorization: owner of the request or admin
    req_item = repo.get_blood_request_by_id(request_id)
    if not req_item:
        return jsonify({"success": False, "error": "Blood request not found."}), 404

    if user_role != "admin" and req_item["requester_user_id"] != user_id:
        return jsonify({
            "success": False,
            "error": "Access denied. Only the request creator or an administrator can trigger donor dispatch."
        }), 403

    success, message, summary = matching_service.dispatch_request_to_donors(
        request_id=request_id,
        actor_user_id=user_id,
        radius_km=radius_km,
        ip_address=ip_addr
    )

    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": summary}), 200


@matching_bp.route("/notifications", methods=["GET"])
@token_required
def list_notifications():
    """
    Lists notification history.
    Admin sees all notifications; regular users see only their received notifications.
    """
    user_id = g.current_user["user_id"]
    user_role = g.current_user["role"]

    if user_role == "admin":
        recipient_filter = request.args.get("recipient_user_id")
        notifications = repo.list_notifications(recipient_user_id=recipient_filter)
    else:
        notifications = repo.list_notifications(recipient_user_id=user_id)

    return jsonify({"success": True, "data": notifications, "count": len(notifications)}), 200