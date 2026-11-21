import uuid
import json
import datetime
from typing import Dict, Any, Tuple, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from app.config import Config
from app.repositories import get_repository
from app.services.storage_service import get_storage_service
from app.utils.jwt_util import generate_jwt_token

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


class AuthService:
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
        # Ahmedabad geographical center default
        return 23.0225, 72.5714

    def register_donor(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Registers a user with the 'donor' role and creates a corresponding donor record."""
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        full_name = data.get("full_name", "").strip()
        phone = data.get("phone", "").strip()
        blood_group = data.get("blood_group", "").strip().upper()
        city = data.get("city", "Ahmedabad").strip()
        locality = data.get("locality", "").strip()

        if not all([email, password, full_name, phone, blood_group, locality]):
            return False, "All fields (email, password, full_name, phone, blood_group, locality) are required.", {}

        if blood_group not in VALID_BLOOD_GROUPS:
            return False, f"Invalid blood group. Must be one of: {sorted(list(VALID_BLOOD_GROUPS))}", {}

        if self.repo.get_user_by_email(email):
            return False, "An account with this email address already exists.", {}

        lat, lon = self._resolve_coordinates(locality)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_id = str(uuid.uuid4())
        donor_id = str(uuid.uuid4())

        user_record = {
            "user_id": user_id,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "donor",
            "phone": phone,
            "full_name": full_name,
            "is_active": 1,
            "created_at": now,
            "updated_at": now
        }
        self.repo.create_user(user_record)

        donor_record = {
            "donor_id": donor_id,
            "user_id": user_id,
            "blood_group": blood_group,
            "city": city,
            "locality": locality,
            "latitude": lat,
            "longitude": lon,
            "is_available": int(data.get("is_available", 1)),
            "consent_share_contact": int(data.get("consent_share_contact", 1)),
            "email_notifications": int(data.get("email_notifications", 1)),
            "last_donated_date": data.get("last_donated_date"),
            "created_at": now,
            "updated_at": now
        }
        self.repo.create_donor(donor_record)

        token = generate_jwt_token(user_id, email, "donor")
        return True, "Donor registered successfully.", {
            "token": token,
            "user": {
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "role": "donor",
                "phone": phone,
                "blood_group": blood_group,
                "locality": locality
            }
        }

    def register_requester(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Registers a user with the 'requester' role for individual blood requests."""
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        full_name = data.get("full_name", "").strip()
        phone = data.get("phone", "").strip()

        if not all([email, password, full_name, phone]):
            return False, "All fields (email, password, full_name, phone) are required.", {}

        if self.repo.get_user_by_email(email):
            return False, "An account with this email address already exists.", {}

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_id = str(uuid.uuid4())

        user_record = {
            "user_id": user_id,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "requester",
            "phone": phone,
            "full_name": full_name,
            "is_active": 1,
            "created_at": now,
            "updated_at": now
        }
        self.repo.create_user(user_record)

        token = generate_jwt_token(user_id, email, "requester")
        return True, "Requester registered successfully.", {
            "token": token,
            "user": {
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "role": "requester",
                "phone": phone
            }
        }

    def register_hospital(self, data: Dict[str, Any], uploaded_file: Optional[Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Registers a hospital account with 'hospital' role and initial 'pending' verification."""
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        contact_person = data.get("contact_person", "").strip()
        phone = data.get("phone", "").strip()
        hospital_name = data.get("hospital_name", "").strip()
        license_number = data.get("license_number", "").strip().upper()
        address = data.get("address", "").strip()
        locality = data.get("locality", "").strip()
        official_phone = data.get("official_phone", "").strip()

        if not all([email, password, contact_person, phone, hospital_name, license_number, address, locality, official_phone]):
            return False, "All hospital profile fields are required.", {}

        if self.repo.get_user_by_email(email):
            return False, "An account with this email address already exists.", {}

        license_doc_url = data.get("license_doc_url")
        if uploaded_file and uploaded_file.filename:
            doc_ok, doc_msg, saved_path = self.storage.save_file(uploaded_file, "hospital_licenses")
            if not doc_ok:
                return False, f"License document upload failed: {doc_msg}", {}
            license_doc_url = saved_path

        lat, lon = self._resolve_coordinates(locality)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_id = str(uuid.uuid4())
        hospital_id = str(uuid.uuid4())

        user_record = {
            "user_id": user_id,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "hospital",
            "phone": phone,
            "full_name": contact_person,
            "is_active": 1,
            "created_at": now,
            "updated_at": now
        }
        self.repo.create_user(user_record)

        hospital_record = {
            "hospital_id": hospital_id,
            "user_id": user_id,
            "hospital_name": hospital_name,
            "license_number": license_number,
            "address": address,
            "locality": locality,
            "latitude": lat,
            "longitude": lon,
            "official_phone": official_phone,
            "license_doc_url": license_doc_url,
            "verification_status": "pending",
            "verified_at": None,
            "created_at": now,
            "updated_at": now
        }
        self.repo.create_hospital(hospital_record)

        token = generate_jwt_token(user_id, email, "hospital")
        return True, "Hospital registered successfully. Account pending administrator verification.", {
            "token": token,
            "user": {
                "user_id": user_id,
                "email": email,
                "full_name": contact_person,
                "role": "hospital",
                "hospital_name": hospital_name,
                "verification_status": "pending"
            }
        }

    def login(self, email: str, password: str, expected_role: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Verifies credentials and returns JWT token alongside role-specific profile details."""
        email = email.strip().lower()
        user = self.repo.get_user_by_email(email)

        if not user:
            return False, "Invalid email or password.", {}

        if not check_password_hash(user["password_hash"], password):
            return False, "Invalid email or password.", {}

        if user.get("is_active") != 1:
            return False, "This account is inactive or has been suspended.", {}

        role = user["role"]
        if expected_role and role != expected_role.strip().lower():
            return (
                False,
                f"This account is registered as '{role}', not '{expected_role}'. Please choose '{role}' to sign in.",
                {},
            )

        user_id = user["user_id"]
        token = generate_jwt_token(user_id, email, role)

        user_info = {
            "user_id": user_id,
            "email": user["email"],
            "full_name": user["full_name"],
            "role": role,
            "phone": user["phone"]
        }

        # Role-specific metadata enrichment
        if role == "donor":
            donor = self.repo.get_donor_by_user_id(user_id)
            if donor:
                user_info["donor_id"] = donor["donor_id"]
                user_info["blood_group"] = donor["blood_group"]
                user_info["locality"] = donor["locality"]
                user_info["is_available"] = donor["is_available"]
                user_info["consent_share_contact"] = donor["consent_share_contact"]
        elif role == "hospital":
            hospital = self.repo.get_hospital_by_user_id(user_id)
            if hospital:
                user_info["hospital_id"] = hospital["hospital_id"]
                user_info["hospital_name"] = hospital["hospital_name"]
                user_info["verification_status"] = hospital["verification_status"]

        return True, "Login successful.", {"token": token, "user": user_info}

    def issue_local_admin_portal_session(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Issues a JWT session for the dedicated local admin portal origin."""
        admins = [u for u in self.repo.list_users(role="admin") if u.get("is_active") == 1]
        if not admins:
            return False, "No active administrator account found.", {}

        admin_user = admins[0]
        user_id = admin_user["user_id"]
        email = admin_user["email"]
        token = generate_jwt_token(user_id, email, "admin")
        user_info = {
            "user_id": user_id,
            "email": email,
            "full_name": admin_user["full_name"],
            "role": "admin",
            "phone": admin_user["phone"],
        }
        return True, "Admin portal session established.", {"token": token, "user": user_info}

    def get_current_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves hydrated profile of the authenticated user."""
        user = self.repo.get_user_by_id(user_id)
        if not user:
            return None

        profile = {
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "phone": user["phone"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }

        if user["role"] == "donor":
            donor = self.repo.get_donor_by_user_id(user_id)
            if donor:
                profile["donor_profile"] = donor
        elif user["role"] == "hospital":
            hospital = self.repo.get_hospital_by_user_id(user_id)
            if hospital:
                profile["hospital_profile"] = hospital

        return profile