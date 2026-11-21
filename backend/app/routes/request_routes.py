from flask import Blueprint, request, jsonify, g, send_file
from app.services.request_service import RequestService
from app.services.response_service import ResponseService
from app.services.storage_service import get_storage_service
from app.middleware.auth_guard import token_required, role_required

request_bp = Blueprint("requests", __name__, url_prefix="/api/requests")
request_service = RequestService()
response_service = ResponseService()
storage_service = get_storage_service()


def _extract_payload_and_file():
    """Helper to extract payload and file regardless of multipart or application/json encoding."""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        file = None
    else:
        data = request.form.to_dict()
        file = request.files.get("requisition_doc") or request.files.get("document")
    return data, file


@request_bp.route("/individual", methods=["POST"])
@token_required
@role_required(["requester", "admin"])
def create_individual_request():
    """Submits a blood request for an individual or family member."""
    user_id = g.current_user["user_id"]
    data, file = _extract_payload_and_file()

    success, message, result = request_service.create_individual_request(user_id, data, file)
    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 201


@request_bp.route("/hospital", methods=["POST"])
@token_required
@role_required(["hospital", "admin"])
def create_hospital_request():
    """Submits a blood request on behalf of an authorized hospital."""
    user_id = g.current_user["user_id"]
    data, file = _extract_payload_and_file()

    success, message, result = request_service.create_hospital_request(user_id, data, file)
    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message, "data": result}), 201


@request_bp.route("/my", methods=["GET"])
@token_required
def get_my_requests():
    """Lists all blood requests submitted by the currently logged-in account."""
    user_id = g.current_user["user_id"]
    requests_list = request_service.list_user_requests(user_id)
    return jsonify({"success": True, "data": requests_list, "count": len(requests_list)}), 200


@request_bp.route("/<request_id>", methods=["GET"])
@token_required
def get_request_details(request_id: str):
    """Retrieves full details of a specific blood request."""
    item = request_service.get_request_by_id(request_id)
    if not item:
        return jsonify({"success": False, "error": "Blood request not found."}), 404

    current_role = g.current_user["role"]
    current_user_id = g.current_user["user_id"]

    if current_role not in ["admin", "donor"] and item["requester_user_id"] != current_user_id:
        return jsonify({"success": False, "error": "Access denied to request details."}), 403

    return jsonify({"success": True, "data": item}), 200


@request_bp.route("/<request_id>/status", methods=["PATCH"])
@token_required
def update_status(request_id: str):
    """Allows request creator or admin to mark request as fulfilled or cancelled."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("request_status")
    if not new_status:
        return jsonify({"success": False, "error": "'request_status' is required."}), 400

    user_id = g.current_user["user_id"]
    user_role = g.current_user["role"]

    success, message = request_service.update_request_status(request_id, user_id, user_role, new_status)
    if not success:
        return jsonify({"success": False, "error": message}), 400

    return jsonify({"success": True, "message": message}), 200


@request_bp.route("/<request_id>/responses", methods=["GET"])
@token_required
def get_request_responses(request_id: str):
    """
    Gated endpoint: Returns responses and consenting donor contacts for a request.
    Only accessible by the requester who submitted the request or platform administrators.
    """
    user_id = g.current_user["user_id"]
    user_role = g.current_user["role"]

    success, message, responses = response_service.get_responses_for_request(
        request_id=request_id,
        user_id=user_id,
        user_role=user_role
    )

    if not success:
        return jsonify({"success": False, "error": message}), 403

    return jsonify({"success": True, "data": responses, "count": len(responses)}), 200


@request_bp.route("/documents/<category>/<filename>", methods=["GET"])
@token_required
def serve_document(category: str, filename: str):
    """Protected document streaming route."""
    relative_path = f"uploads/{category}/{filename}"
    resolved_path = storage_service.get_file_path(relative_path)

    if not resolved_path or not resolved_path.exists():
        return jsonify({"success": False, "error": "Document not found or access denied."}), 404

    return send_file(str(resolved_path), as_attachment=False)