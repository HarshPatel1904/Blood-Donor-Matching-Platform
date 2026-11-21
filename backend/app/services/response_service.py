import uuid
import datetime
from typing import Dict, Any, List, Tuple, Optional
from app.repositories import get_repository
from app.services.notification_service import get_notification_provider
from app.utils.audit_logger import log_action
from app.utils.haversine import calculate_haversine_distance

VALID_RESPONSE_STATUSES = {"accepted", "declined", "unavailable", "withdrawn"}


class ResponseService:
    def __init__(self):
        self.repo = get_repository()
        self.notifier = get_notification_provider()

    def get_donor_dispatched_requests(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all requests where this donor has been matched and notified,
        including their current response state.
        """
        donor = self.repo.get_donor_by_user_id(user_id)
        if not donor:
            return []

        donor_id = donor["donor_id"]
        donor_coord = (float(donor["latitude"]), float(donor["longitude"]))

        # Get existing responses recorded for this donor
        recorded_responses = self.repo.list_responses_for_donor(donor_id)
        response_map = {r["request_id"]: r for r in recorded_responses}

        # Build list of active requests
        results = []
        for req_id, resp in response_map.items():
            req = self.repo.get_blood_request_by_id(req_id)
            if not req:
                continue

            # Calculate straight-line distance
            try:
                req_coord = (float(req["latitude"]), float(req["longitude"]))
                distance_km = calculate_haversine_distance(donor_coord, req_coord)
            except (ValueError, TypeError):
                distance_km = 0.0

            results.append({
                "request_id": req["request_id"],
                "hospital_name": req["hospital_name"],
                "blood_group": req["blood_group"],
                "units_needed": req["units_needed"],
                "locality": req["locality"],
                "urgency": req["urgency"],
                "required_by_date": req["required_by_date"],
                "request_status": req["request_status"],
                "distance_km": distance_km,
                "response_status": resp.get("status", "pending"),
                "contact_revealed": resp.get("contact_revealed", 0),
                "responded_at": resp.get("responded_at")
            })

        return results

    def submit_donor_response(
        self,
        user_id: str,
        request_id: str,
        status: str,
        consent_share_contact: bool = True,
        ip_address: str = "127.0.0.1"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Records the donor's decision (accepted/declined/unavailable/withdrawn)
        and enforces contact-sharing consent.
        """
        status = status.strip().lower()
        if status not in VALID_RESPONSE_STATUSES:
            return False, f"Invalid status. Allowed values: {sorted(list(VALID_RESPONSE_STATUSES))}", {}

        donor = self.repo.get_donor_by_user_id(user_id)
        if not donor:
            return False, "Donor profile not found for this account.", {}

        donor_id = donor["donor_id"]
        donor_user = self.repo.get_user_by_id(user_id)
        donor_name = donor_user.get("full_name", "Voluntary Donor")

        blood_request = self.repo.get_blood_request_by_id(request_id)
        if not blood_request:
            return False, "Blood request not found.", {}

        if blood_request.get("request_status") in ["fulfilled", "cancelled", "expired"]:
            return False, f"Cannot respond. Request is already '{blood_request.get('request_status')}'.", {}

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Contact reveal flag: only true if donor explicitly accepted AND consented
        contact_revealed = 1 if (status == "accepted" and consent_share_contact) else 0

        existing_response = self.repo.get_donor_response(request_id, donor_id)
        response_id = existing_response["response_id"] if existing_response else str(uuid.uuid4())

        response_data = {
            "response_id": response_id,
            "request_id": request_id,
            "donor_id": donor_id,
            "status": status,
            "contact_revealed": contact_revealed,
            "responded_at": now
        }

        self.repo.save_donor_response(response_data)

        # Notify the requester if a donor accepts
        if status == "accepted":
            requester = self.repo.get_user_by_id(blood_request["requester_user_id"])
            if requester and requester.get("email"):
                contact_info_text = (
                    f"Phone : {donor_user.get('phone')}\n  Email : {donor_user.get('email')}"
                    if contact_revealed == 1
                    else "Donor has agreed to donate but requested contact anonymity through the portal.\n"
                         "  Please coordinate via your hospital blood bank desk."
                )

                subject = f"MATCH UPDATE: A Donor Accepted Your Request for {blood_request['blood_group']}"
                body = f"""Hello {requester.get('full_name')},

A voluntary donor has ACCEPTED your blood request at {blood_request['hospital_name']}.

Donor Details:
  Name  : {donor_name}
  Group : {donor['blood_group']}
  Area  : {donor['locality']}
  {contact_info_text}

Important Safety Notice:
This platform facilitates donor-patient communication only. Final donor medical eligibility,
screening, cross-matching, and collection are strictly governed by the attending hospital blood bank.
"""
                self.notifier.send_email(
                    to_email=requester["email"],
                    subject=subject,
                    body_text=body,
                    recipient_user_id=requester["user_id"],
                    request_id=request_id
                )

        # Audit log
        log_action(
            actor_user_id=user_id,
            action=f"DONOR_RESPONSE_{status.upper()}",
            target_entity="blood_request",
            target_id=request_id,
            details={
                "status": status,
                "contact_revealed": contact_revealed
            },
            ip_address=ip_address
        )

        return True, f"Response recorded as '{status}'.", {
            "response_id": response_id,
            "request_id": request_id,
            "status": status,
            "contact_revealed": contact_revealed,
            "responded_at": now
        }

    def get_responses_for_request(
        self,
        request_id: str,
        user_id: str,
        user_role: str
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Retrieves donor responses for a blood request.
        Restricted to the request creator and administrators.
        Omits raw coordinates and shows only approximate distance and locality.
        """
        blood_request = self.repo.get_blood_request_by_id(request_id)
        if not blood_request:
            return False, "Blood request not found.", []

        # Access control
        if user_role != "admin" and blood_request["requester_user_id"] != user_id:
            return False, "Access denied. Only the request creator or an administrator can view responses.", []

        raw_responses = self.repo.list_responses_for_request(request_id)
        req_coord = (float(blood_request["latitude"]), float(blood_request["longitude"]))

        sanitized_responses = []
        for r in raw_responses:
            donor = self.repo.get_donor_by_id(r["donor_id"])
            distance_km = 0.0
            if donor:
                try:
                    d_coord = (float(donor["latitude"]), float(donor["longitude"]))
                    distance_km = calculate_haversine_distance(req_coord, d_coord)
                except (ValueError, TypeError):
                    pass

            sanitized_responses.append({
                "response_id": r["response_id"],
                "status": r["status"],
                "contact_revealed": bool(r["contact_revealed"]),
                "donor_name": r["donor_name"],
                "donor_locality": r["donor_locality"],
                "blood_group": r["blood_group"],
                "approximate_distance_km": distance_km,
                "donor_phone": r["donor_phone"] if r["contact_revealed"] == 1 else None,
                "donor_email": r["donor_email"] if r["contact_revealed"] == 1 else None,
                "responded_at": r["responded_at"]
            })

        return True, "Responses retrieved successfully.", sanitized_responses