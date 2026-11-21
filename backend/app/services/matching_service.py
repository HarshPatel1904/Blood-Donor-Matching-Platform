import uuid
import datetime
from typing import Dict, Any, List, Tuple, Optional
from app.config import Config
from app.repositories import get_repository
from app.utils.haversine import calculate_haversine_distance
from app.services.notification_service import get_notification_provider
from app.utils.audit_logger import log_action


class MatchingService:
    def __init__(self):
        self.repo = get_repository()
        self.notifier = get_notification_provider()

    def find_matching_donors(
        self,
        request_id: str,
        radius_km: float = 10.0
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Finds donors matching requested blood group, availability, and radius.
        Sanitizes donor output to omit direct contact and coordinate details.
        """
        blood_request = self.repo.get_blood_request_by_id(request_id)
        if not blood_request:
            return False, "Blood request not found.", {}

        req_blood_group = blood_request["blood_group"]
        req_lat = float(blood_request["latitude"])
        req_lon = float(blood_request["longitude"])
        req_coord = (req_lat, req_lon)

        # Retrieve available donors for the exact blood group
        candidates = self.repo.list_donors(blood_group=req_blood_group, is_available=1)

        matched_donors = []
        for donor in candidates:
            # Check if donor coordinates exist
            try:
                donor_lat = float(donor["latitude"])
                donor_lon = float(donor["longitude"])
            except (ValueError, TypeError):
                continue

            distance_km = calculate_haversine_distance(req_coord, (donor_lat, donor_lon))

            if distance_km <= radius_km:
                matched_donors.append({
                    "donor_id": donor["donor_id"],
                    "user_id": donor["user_id"],
                    "full_name": donor.get("full_name"),
                    "blood_group": donor["blood_group"],
                    "locality": donor["locality"],
                    "city": donor["city"],
                    "distance_km": distance_km,
                    "email_notifications": donor.get("email_notifications", 1),
                    "last_donated_date": donor.get("last_donated_date")
                })

        # Sort ascending by distance (nearest donor first)
        matched_donors.sort(key=lambda d: d["distance_km"])

        result = {
            "request_id": request_id,
            "blood_group": req_blood_group,
            "request_locality": blood_request["locality"],
            "hospital_name": blood_request["hospital_name"],
            "search_radius_km": radius_km,
            "total_matches": len(matched_donors),
            "donors": matched_donors
        }
        return True, f"Found {len(matched_donors)} eligible donor(s) within {radius_km} km.", result

    def dispatch_request_to_donors(
        self,
        request_id: str,
        actor_user_id: str,
        radius_km: float = 10.0,
        ip_address: str = "127.0.0.1"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Dispatches alerts to matching donors:
        1. Validates that the blood request is approved.
        2. Filters eligible donors within radius.
        3. Creates 'pending' response records in donor_responses.
        4. Triggers the notification provider to emit emails.
        5. Updates blood request lifecycle to 'donors_notified'.
        6. Creates an audit trail log.
        """
        blood_request = self.repo.get_blood_request_by_id(request_id)
        if not blood_request:
            return False, "Blood request not found.", {}

        # Individual requests must be approved by admin before dispatching
        if blood_request.get("verification_status") != "approved":
            return False, (
                f"Cannot dispatch request. Current verification status is "
                f"'{blood_request.get('verification_status')}'. Request must be 'approved' first."
            ), {}

        if blood_request.get("request_status") in ["fulfilled", "cancelled", "expired"]:
            return False, f"Cannot dispatch. Request is already '{blood_request.get('request_status')}'.", {}

        success, msg, match_data = self.find_matching_donors(request_id, radius_km)
        if not success:
            return False, msg, {}

        donors_list = match_data.get("donors", [])
        if not donors_list:
            return False, f"No available {blood_request['blood_group']} donors found within {radius_km} km.", {}

        frontend_url = Config.FRONTEND_URL
        units_needed = blood_request["units_needed"]
        hospital_name = blood_request["hospital_name"]
        locality = blood_request["locality"]
        urgency = blood_request["urgency"].upper()
        req_date = blood_request["required_by_date"]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        notifications_sent = 0
        responses_created = 0

        for d in donors_list:
            donor_id = d["donor_id"]
            user_id = d["user_id"]
            donor_name = d["full_name"]
            distance = d["distance_km"]

            # 1. Initialize or maintain pending record in donor_responses
            existing_response = self.repo.get_donor_response(request_id, donor_id)
            if not existing_response:
                response_record = {
                    "response_id": str(uuid.uuid4()),
                    "request_id": request_id,
                    "donor_id": donor_id,
                    "status": "pending",
                    "contact_revealed": 0,
                    "responded_at": now
                }
                self.repo.save_donor_response(response_record)
                responses_created += 1

            # 2. Check if donor has opted in to email notifications
            if d.get("email_notifications") == 1:
                # Retrieve donor's email from users table
                donor_user = self.repo.get_user_by_id(user_id)
                if donor_user and donor_user.get("email"):
                    subject = f"URGENT: Blood Request for {blood_request['blood_group']} ({urgency})"
                    body = f"""Hello {donor_name},

A verified blood request matching your blood group ({blood_request['blood_group']}) has been posted.

Request Details:
  - Hospital      : {hospital_name}
  - Location      : {locality} (~{distance} km from your area)
  - Units Needed  : {units_needed} unit(s)
  - Urgency Level : {urgency}
  - Required By   : {req_date}

Please click the secure link below to accept or decline this request:
{frontend_url}/donor/requests/{request_id}

Important Note: This is an automated notification platform. Actual donor screening, compatibility tests, and collection are conducted directly by the hospital blood bank.

Thank you for being a voluntary donor.
"""
                    self.notifier.send_email(
                        to_email=donor_user["email"],
                        subject=subject,
                        body_text=body,
                        recipient_user_id=user_id,
                        request_id=request_id
                    )
                    notifications_sent += 1

        # 3. Update blood request lifecycle to 'donors_notified'
        self.repo.update_request_lifecycle(request_id, "donors_notified")

        # 4. Create audit log
        log_action(
            actor_user_id=actor_user_id,
            action="REQUEST_DISPATCHED",
            target_entity="blood_request",
            target_id=request_id,
            details={
                "radius_km": radius_km,
                "matches_count": len(donors_list),
                "notifications_sent": notifications_sent
            },
            ip_address=ip_address
        )

        dispatch_summary = {
            "request_id": request_id,
            "status": "donors_notified",
            "search_radius_km": radius_km,
            "total_matches": len(donors_list),
            "notifications_sent": notifications_sent,
            "donor_responses_initialized": responses_created
        }

        return True, f"Successfully dispatched alerts to {notifications_sent} matching donor(s).", dispatch_summary