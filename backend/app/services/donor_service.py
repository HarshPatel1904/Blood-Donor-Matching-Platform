import json
from typing import Dict, Any, Tuple, Optional, List
from app.config import Config
from app.repositories import get_repository
from app.utils.haversine import calculate_haversine_distance

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


class DonorService:
    def __init__(self):
        self.repo = get_repository()
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

    def get_donor_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full donor profile linked to a user_id."""
        return self.repo.get_donor_by_user_id(user_id)

    def update_profile(
        self, user_id: str, updates: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Updates donor profile fields. If locality changes, coordinates
        are recalculated from the predefined Ahmedabad dataset.
        """
        donor = self.repo.get_donor_by_user_id(user_id)
        if not donor:
            return False, "Donor profile not found.", {}

        donor_id = donor["donor_id"]
        valid_updates = {}

        if "blood_group" in updates:
            bg = updates["blood_group"].strip().upper()
            if bg not in VALID_BLOOD_GROUPS:
                return False, f"Invalid blood group. Allowed: {sorted(list(VALID_BLOOD_GROUPS))}", {}
            valid_updates["blood_group"] = bg

        if "locality" in updates:
            new_locality = updates["locality"].strip()
            lat, lon = self._resolve_coordinates(new_locality)
            valid_updates["locality"] = new_locality
            valid_updates["latitude"] = lat
            valid_updates["longitude"] = lon

        if "city" in updates:
            valid_updates["city"] = updates["city"].strip()

        if "is_available" in updates:
            valid_updates["is_available"] = 1 if updates["is_available"] else 0

        if "consent_share_contact" in updates:
            valid_updates["consent_share_contact"] = 1 if updates["consent_share_contact"] else 0

        if "email_notifications" in updates:
            valid_updates["email_notifications"] = 1 if updates["email_notifications"] else 0

        if "last_donated_date" in updates:
            valid_updates["last_donated_date"] = updates["last_donated_date"]

        if not valid_updates:
            return False, "No valid profile fields provided for update.", {}

        success = self.repo.update_donor_profile(donor_id, valid_updates)
        if not success:
            return False, "Failed to update donor profile in database.", {}

        updated_donor = self.repo.get_donor_by_id(donor_id)
        return True, "Profile updated successfully.", updated_donor

    def set_availability(self, user_id: str, is_available: bool) -> Tuple[bool, str, Dict[str, Any]]:
        """Toggles a donor's active donation availability."""
        donor = self.repo.get_donor_by_user_id(user_id)
        if not donor:
            return False, "Donor profile not found.", {}

        int_status = 1 if is_available else 0
        success = self.repo.update_donor_availability(donor["donor_id"], int_status)
        if not success:
            return False, "Failed to update availability status.", {}

        return True, f"Availability set to {'available' if is_available else 'unavailable'}.", {
            "donor_id": donor["donor_id"],
            "is_available": int_status
        }

    def get_response_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all past request responses for the donor."""
        donor = self.repo.get_donor_by_user_id(user_id)
        if not donor:
            return []
        return self.repo.list_responses_for_donor(donor["donor_id"])