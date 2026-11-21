import uuid
import json
import datetime
from typing import Dict, Any, Tuple, Optional, List
from app.config import Config
from app.repositories import get_repository
from app.services.storage_service import get_storage_service

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
VALID_URGENCIES = {"normal", "urgent", "critical"}


class RequestService:
    def __init__(self):
        self.repo = get_repository()
        self.storage = get_storage_service()
        self._localities_cache = None

    def _get_localities(self) -> Dict[str, Dict[str, Any]]:
        """Loads and indexes the Ahmedabad localities dataset."""
        if self._localities_cache is None:
            try:
                with open(Config.LOCALITIES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._localities_cache = {
                        loc["name"].strip().lower(): loc for loc in data.get("localities", [])
                    }
            except Exception:
                self._localities_cache = {}
        return self._localities_cache

    def _resolve_coordinates(self, locality_name: str) -> Tuple[float, float]:
        """Resolves latitude and longitude from localities.json, defaults to Ahmedabad center."""
        localities = self._get_localities()
        match = localities.get(locality_name.strip().lower())
        if match:
            return float(match["latitude"]), float(match["longitude"])
        return 23.0225, 72.5714

    def create_individual_request(
        self,
        user_id: str,
        data: Dict[str, Any],
        uploaded_file: Optional[Any] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Creates an individual blood request. Requires administrator review ('pending' verification).
        """
        blood_group = data.get("blood_group", "").strip().upper()
        hospital_name = data.get("hospital_name", "").strip()
        locality = data.get("locality", "").strip()
        urgency = data.get("urgency", "normal").strip().lower()
        required_by_date = data.get("required_by_date", "").strip()

        try:
            units_needed = int(data.get("units_needed", 1))
        except (ValueError, TypeError):
            return False, "Units needed must be a positive whole integer.", {}

        if units_needed <= 0:
            return False, "Units needed must be greater than zero.", {}

        if not all([blood_group, hospital_name, locality, required_by_date]):
            return False, "Blood group, hospital name, locality, and required-by date are required.", {}

        if blood_group not in VALID_BLOOD_GROUPS:
            return False, f"Invalid blood group. Allowed: {sorted(list(VALID_BLOOD_GROUPS))}", {}

        if urgency not in VALID_URGENCIES:
            return False, f"Invalid urgency. Allowed: {sorted(list(VALID_URGENCIES))}", {}

        # Handle document upload if attached
        doc_url = None
        if uploaded_file and uploaded_file.filename:
            success, msg, saved_path = self.storage.save_file(uploaded_file, "requisitions")
            if not success:
                return False, f"Document upload failed: {msg}", {}
            doc_url = saved_path

        lat, lon = self._resolve_coordinates(locality)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        request_id = str(uuid.uuid4())

        request_record = {
            "request_id": request_id,
            "requester_user_id": user_id,
            "request_type": "individual",
            "blood_group": blood_group,
            "units_needed": units_needed,
            "hospital_name": hospital_name,
            "locality": locality,
            "latitude": lat,
            "longitude": lon,
            "urgency": urgency,
            "requisition_doc_url": doc_url,
            "verification_status": "pending",  # Must be approved by admin in Phase 6
            "request_status": "open",
            "required_by_date": required_by_date,
            "created_at": now,
            "updated_at": now
        }

        self.repo.create_blood_request(request_record)
        return True, "Blood request submitted successfully and is pending administrative verification.", request_record

    def create_hospital_request(
        self,
        user_id: str,
        data: Dict[str, Any],
        uploaded_file: Optional[Any] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Creates a hospital-initiated blood request.
        If the hospital is verified, verification_status is automatically set to 'approved'.
        If the hospital account is pending verification, request verification is set to 'pending'.
        """
        hospital = self.repo.get_hospital_by_user_id(user_id)
        if not hospital:
            return False, "Authenticated user does not have an associated hospital profile.", {}

        is_verified_hospital = (hospital.get("verification_status") == "verified")

        blood_group = data.get("blood_group", "").strip().upper()
        locality = data.get("locality", hospital.get("locality", "")).strip()
        urgency = data.get("urgency", "urgent").strip().lower()
        required_by_date = data.get("required_by_date", "").strip()

        try:
            units_needed = int(data.get("units_needed", 1))
        except (ValueError, TypeError):
            return False, "Units needed must be a positive whole integer.", {}

        if units_needed <= 0:
            return False, "Units needed must be greater than zero.", {}

        if not all([blood_group, locality, required_by_date]):
            return False, "Blood group, locality, and required-by date are required.", {}

        if blood_group not in VALID_BLOOD_GROUPS:
            return False, f"Invalid blood group. Allowed: {sorted(list(VALID_BLOOD_GROUPS))}", {}

        if urgency not in VALID_URGENCIES:
            return False, f"Invalid urgency. Allowed: {sorted(list(VALID_URGENCIES))}", {}

        # Handle document upload if provided
        doc_url = None
        if uploaded_file and uploaded_file.filename:
            success, msg, saved_path = self.storage.save_file(uploaded_file, "requisitions")
            if not success:
                return False, f"Document upload failed: {msg}", {}
            doc_url = saved_path

        lat, lon = self._resolve_coordinates(locality)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        request_id = str(uuid.uuid4())

        # Verified hospitals receive trusted privileges; unverified hospitals are queued for review
        verification_status = "approved" if is_verified_hospital else "pending"

        request_record = {
            "request_id": request_id,
            "requester_user_id": user_id,
            "request_type": "hospital",
            "blood_group": blood_group,
            "units_needed": units_needed,
            "hospital_name": hospital.get("hospital_name"),
            "locality": locality,
            "latitude": lat,
            "longitude": lon,
            "urgency": urgency,
            "requisition_doc_url": doc_url,
            "verification_status": verification_status,
            "request_status": "open",
            "required_by_date": required_by_date,
            "created_at": now,
            "updated_at": now
        }

        self.repo.create_blood_request(request_record)

        msg = (
            "Hospital blood request created and approved for donor matching."
            if is_verified_hospital
            else "Hospital request submitted. Pending verification because your hospital account is not yet verified."
        )
        return True, msg, request_record

    def get_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Fetches single blood request details with requester information."""
        return self.repo.get_blood_request_by_id(request_id)

    def list_user_requests(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches all requests submitted by a specific user (individual or hospital staff)."""
        return self.repo.list_blood_requests(requester_user_id=user_id)

    def update_request_status(
        self,
        request_id: str,
        user_id: str,
        user_role: str,
        new_status: str
    ) -> Tuple[bool, str]:
        """
        Allows the owner or an administrator to cancel or mark a request as fulfilled.
        """
        allowed_lifecycle = {"open", "fulfilled", "cancelled"}
        if new_status not in allowed_lifecycle:
            return False, f"Invalid status transition. Allowed: {sorted(list(allowed_lifecycle))}"

        request_item = self.repo.get_blood_request_by_id(request_id)
        if not request_item:
            return False, "Blood request not found."

        # Ownership authorization: owner or admin
        if user_role != "admin" and request_item["requester_user_id"] != user_id:
            return False, "Access denied. You can only update requests that you created."

        success = self.repo.update_request_lifecycle(request_id, new_status)
        if not success:
            return False, "Failed to update request status."

        return True, f"Request status updated to '{new_status}'."