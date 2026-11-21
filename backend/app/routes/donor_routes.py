from flask import Blueprint, request, jsonify, g
from app.services.donor_service import DonorService
from app.services.response_service import ResponseService
from app.middleware.auth_guard import token_required, role_required

donor_bp = Blueprint("donors", __name__, url_prefix="/api/donors")
donor_service = DonorService()
response_service = ResponseService()


@donor_bp.route("/profile", methods=["GET"])
@token_required
@role_required(["donor"])
def get_profile():
    """Returns the profile of the currently logged-in donor."""
    user_id = g.current_user["user_id"]
    donor = donor_service.get_donor_by_user_id(user_id)
    if not donor:
        return jsonify({"success": False, "error": "Donor record not found."}), 404
    return jsonify({"success": True, "data": donor}), 200


@donor_bp.route("/profile", methods=["PUT"])
@token_required
@role_required(["donor"])
def update_profile():
    """Updates donor attributes (locality, blood group, notifications, contact consent)."""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    success, message, updated_data = donor_service.update_profile(user_id, data)
    if not success:
        return jsonify({"success": False, "error": message}), 400
    return jsonify({"success": True, "message": message, "data": updated_data}), 200


@donor_bp.route("/availability", methods=["PATCH"])
@token_required
@role_required(["donor"])
def toggle_availability():
    """Toggles donor availability between 1 (available) and 0 (unavailable)."""
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    if "is_available" not in data:
        return jsonify({"success": False, "error": "'is_available' boolean field is required."}), 400

    is_available = bool(data["is_available"])
    success, message, result = donor_service.set_availability(user_id, is_available)
    if not success:
        return jsonify({"success": False, "error": message}), 400
    return jsonify({"success": True, "message": message, "data": result}), 200


@donor_bp.route("/history", methods=["GET"])
@token_required
@role_required(["donor"])
def get_history():
    """Returns the response history of the logged-in donor."""
    user_id = g.current_user["user_id"]
    history = donor_service.get_response_history(user_id)
    return jsonify({"success": True, "data": history, "count": len(history)}), 200


@donor_bp.route("/matching-requests", methods=["GET"])
@token_required
@role_required(["donor"])
def get_matching_requests():
    """Retrieves all requests dispatched to this donor for review."""
    user_id = g.current_user["user_id"]
    requests_list = response_service.get_donor_dispatched_requests(user_id)
    return jsonify({"success": True, "data": requests_list, "count": len(requests_list)}), 200


@donor_bp.route("/requests/<request_id>/respond", methods=["POST"])
@token_required
@role_required(["donor"])
def respond_to_request(request_id: str):
    """
    Donor accepts, declines, or marks unavailable for a blood request.
    Payload: {"status": "accepted"|"declined", "consent_share_contact": true|false}
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    consent_share_contact = bool(data.get("consent_share_contact", True))
    ip_addr = request.remote_addr or "127.0.0.1"

    if not status:
        return jsonify({"success": False, "error": "'status' (accepted/declined/unavailable) is required."}), 400

    success, message, result = response_service.submit_donor_response(
        user_id=user_id,
        request_id=request_id,
        status=status,
        consent_share_contact=consent_share_contact,
        ip_address=ip_addr
    )

    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 200