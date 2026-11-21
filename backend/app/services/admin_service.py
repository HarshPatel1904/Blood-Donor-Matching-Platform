import datetime
from typing import Dict, Any, List, Optional, Tuple
from app.repositories import get_repository
from app.utils.audit_logger import log_action

VALID_HOSPITAL_STATUSES = {"verified", "rejected", "pending"}
VALID_REQUEST_VERIFICATION_STATUSES = {"approved", "rejected", "on_hold", "pending"}


class AdminService:
    def __init__(self):
        self.repo = get_repository()

    # ---------------- HOSPITAL VERIFICATION ---------------- #
    def list_hospitals(self, verification_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists hospitals filtered by verification status or all hospitals."""
        return self.repo.list_hospitals(verification_status=verification_status)

    def verify_hospital(
        self,
        admin_user_id: str,
        hospital_id: str,
        status: str,
        notes: Optional[str] = None,
        ip_address: str = "127.0.0.1"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Approves or rejects a hospital account after administrative verification.
        """
        status = status.strip().lower()
        if status not in VALID_HOSPITAL_STATUSES:
            return False, f"Invalid status. Must be one of: {sorted(list(VALID_HOSPITAL_STATUSES))}", {}

        hospital = self.repo.get_hospital_by_id(hospital_id)
        if not hospital:
            return False, "Hospital not found.", {}

        verified_at = datetime.datetime.now(datetime.timezone.utc).isoformat() if status == "verified" else None
        success = self.repo.update_hospital_verification(hospital_id, status, verified_at)
        if not success:
            return False, "Failed to update hospital status in database.", {}

        # Record audit log
        log_action(
            actor_user_id=admin_user_id,
            action=f"HOSPITAL_{status.upper()}",
            target_entity="hospital",
            target_id=hospital_id,
            details={"notes": notes, "hospital_name": hospital.get("hospital_name")},
            ip_address=ip_address
        )

        updated_hospital = self.repo.get_hospital_by_id(hospital_id)
        return True, f"Hospital verification status updated to '{status}'.", updated_hospital

    # ---------------- BLOOD REQUEST REVIEW ---------------- #
    def list_blood_requests(
        self,
        verification_status: Optional[str] = None,
        request_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists all requests across individual and hospital categories."""
        return self.repo.list_blood_requests(
            verification_status=verification_status,
            request_status=request_status
        )

    def review_blood_request(
        self,
        admin_user_id: str,
        request_id: str,
        status: str,
        notes: Optional[str] = None,
        ip_address: str = "127.0.0.1"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Approves, rejects, or holds an individual blood request.
        """
        status = status.strip().lower()
        if status not in VALID_REQUEST_VERIFICATION_STATUSES:
            return False, f"Invalid verification status. Allowed: {sorted(list(VALID_REQUEST_VERIFICATION_STATUSES))}", {}

        request_item = self.repo.get_blood_request_by_id(request_id)
        if not request_item:
            return False, "Blood request not found.", {}

        success = self.repo.update_request_verification(request_id, status)
        if not success:
            return False, "Failed to update request verification status.", {}

        # Record audit trail
        log_action(
            actor_user_id=admin_user_id,
            action=f"REQUEST_{status.upper()}",
            target_entity="blood_request",
            target_id=request_id,
            details={"notes": notes, "blood_group": request_item.get("blood_group"), "urgency": request_item.get("urgency")},
            ip_address=ip_address
        )

        updated_request = self.repo.get_blood_request_by_id(request_id)
        return True, f"Request verification status set to '{status}'.", updated_request

    # ---------------- USER MANAGEMENT ---------------- #
    def toggle_user_active_status(
        self,
        admin_user_id: str,
        target_user_id: str,
        is_active: bool,
        reason: Optional[str] = None,
        ip_address: str = "127.0.0.1"
    ) -> Tuple[bool, str]:
        """Suspends or reactivates any user account."""
        if admin_user_id == target_user_id:
            return False, "Administrators cannot suspend their own account."

        target_user = self.repo.get_user_by_id(target_user_id)
        if not target_user:
            return False, "Target user not found."

        int_status = 1 if is_active else 0
        success = self.repo.update_user_status(target_user_id, int_status)
        if not success:
            return False, "Failed to update user active status."

        action_name = "USER_ACTIVATED" if is_active else "USER_SUSPENDED"
        log_action(
            actor_user_id=admin_user_id,
            action=action_name,
            target_entity="user",
            target_id=target_user_id,
            details={"email": target_user.get("email"), "reason": reason},
            ip_address=ip_address
        )

        state_label = "activated" if is_active else "suspended"
        return True, f"User account has been {state_label}."

    # ---------------- AUDIT & DASHBOARD STATS ---------------- #
    def list_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves system audit logs ordered by newest first."""
        return self.repo.list_audit_logs(limit=limit)

    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Calculates system metrics for the administrative dashboard."""
        all_users = self.repo.list_users()
        all_donors = self.repo.list_donors()
        all_hospitals = self.repo.list_hospitals()
        all_requests = self.repo.list_blood_requests()

        donors_available = sum(1 for d in all_donors if d.get("is_available") == 1)
        hospitals_verified = sum(1 for h in all_hospitals if h.get("verification_status") == "verified")
        hospitals_pending = sum(1 for h in all_hospitals if h.get("verification_status") == "pending")

        requests_pending = sum(1 for r in all_requests if r.get("verification_status") == "pending")
        requests_approved = sum(1 for r in all_requests if r.get("verification_status") == "approved")
        requests_open = sum(1 for r in all_requests if r.get("request_status") == "open")
        requests_fulfilled = sum(1 for r in all_requests if r.get("request_status") == "fulfilled")

        return {
            "users": {
                "total": len(all_users),
                "donors": len(all_donors),
                "donors_available": donors_available,
                "hospitals": len(all_hospitals),
                "hospitals_verified": hospitals_verified,
                "hospitals_pending": hospitals_pending
            },
            "requests": {
                "total": len(all_requests),
                "pending_verification": requests_pending,
                "approved_verification": requests_approved,
                "open": requests_open,
                "fulfilled": requests_fulfilled
            }
        }