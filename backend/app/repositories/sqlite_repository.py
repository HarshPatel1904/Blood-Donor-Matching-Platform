import json
from typing import Dict, List, Optional, Any
from app.repositories.base_repository import BaseRepository
from app.repositories.sqlite_conn import get_db_connection


class SQLiteRepository(BaseRepository):
    """Concrete SQLite implementation of BaseRepository."""

    # ---------------- USER OPERATIONS ---------------- #
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO users (user_id, email, password_hash, role, phone, full_name, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_data["user_id"],
            user_data["email"],
            user_data["password_hash"],
            user_data["role"],
            user_data["phone"],
            user_data["full_name"],
            user_data.get("is_active", 1),
            user_data["created_at"],
            user_data["updated_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return user_data

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM users WHERE user_id = ?"
        with get_db_connection() as conn:
            row = conn.execute(query, (user_id,)).fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM users WHERE LOWER(email) = LOWER(?)"
        with get_db_connection() as conn:
            row = conn.execute(query, (email,)).fetchone()
            return dict(row) if row else None

    def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            if role:
                rows = conn.execute("SELECT * FROM users WHERE role = ? ORDER BY created_at DESC", (role,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def update_user_status(self, user_id: str, is_active: int) -> bool:
        query = "UPDATE users SET is_active = ?, updated_at = datetime('now') WHERE user_id = ?"
        with get_db_connection() as conn:
            cursor = conn.execute(query, (is_active, user_id))
            return cursor.rowcount > 0

    # ---------------- DONOR OPERATIONS ---------------- #
    def create_donor(self, donor_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO donors (
                donor_id, user_id, blood_group, city, locality,
                latitude, longitude, is_available, consent_share_contact,
                email_notifications, last_donated_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            donor_data["donor_id"],
            donor_data["user_id"],
            donor_data["blood_group"],
            donor_data["city"],
            donor_data["locality"],
            donor_data["latitude"],
            donor_data["longitude"],
            donor_data.get("is_available", 1),
            donor_data.get("consent_share_contact", 1),
            donor_data.get("email_notifications", 1),
            donor_data.get("last_donated_date"),
            donor_data["created_at"],
            donor_data["updated_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return donor_data

    def get_donor_by_id(self, donor_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT d.*, u.full_name, u.email, u.phone, u.is_active
            FROM donors d
            JOIN users u ON d.user_id = u.user_id
            WHERE d.donor_id = ?
        """
        with get_db_connection() as conn:
            row = conn.execute(query, (donor_id,)).fetchone()
            return dict(row) if row else None

    def get_donor_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT d.*, u.full_name, u.email, u.phone, u.is_active
            FROM donors d
            JOIN users u ON d.user_id = u.user_id
            WHERE d.user_id = ?
        """
        with get_db_connection() as conn:
            row = conn.execute(query, (user_id,)).fetchone()
            return dict(row) if row else None

    def update_donor_profile(self, donor_id: str, updates: Dict[str, Any]) -> bool:
        fields = []
        values = []
        for key, val in updates.items():
            if key in {"blood_group", "city", "locality", "latitude", "longitude",
                        "is_available", "consent_share_contact", "email_notifications", "last_donated_date"}:
                fields.append(f"{key} = ?")
                values.append(val)
        if not fields:
            return False

        fields.append("updated_at = datetime('now')")
        values.append(donor_id)
        query = f"UPDATE donors SET {', '.join(fields)} WHERE donor_id = ?"

        with get_db_connection() as conn:
            cursor = conn.execute(query, tuple(values))
            return cursor.rowcount > 0

    def update_donor_availability(self, donor_id: str, is_available: int) -> bool:
        query = "UPDATE donors SET is_available = ?, updated_at = datetime('now') WHERE donor_id = ?"
        with get_db_connection() as conn:
            cursor = conn.execute(query, (is_available, donor_id))
            return cursor.rowcount > 0

    def list_donors(
        self,
        blood_group: Optional[str] = None,
        is_available: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        conditions = ["u.is_active = 1"]
        params = []

        if blood_group:
            conditions.append("d.blood_group = ?")
            params.append(blood_group)
        if is_available is not None:
            conditions.append("d.is_available = ?")
            params.append(is_available)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f"""
            SELECT d.*, u.full_name, u.email, u.phone
            FROM donors d
            JOIN users u ON d.user_id = u.user_id
            {where_clause}
            ORDER BY d.created_at DESC
        """
        with get_db_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(row) for row in rows]

    # ---------------- HOSPITAL OPERATIONS ---------------- #
    def create_hospital(self, hospital_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO hospitals (
                hospital_id, user_id, hospital_name, license_number, address,
                locality, latitude, longitude, official_phone, license_doc_url,
                verification_status, verified_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            hospital_data["hospital_id"],
            hospital_data["user_id"],
            hospital_data["hospital_name"],
            hospital_data["license_number"],
            hospital_data["address"],
            hospital_data["locality"],
            hospital_data["latitude"],
            hospital_data["longitude"],
            hospital_data["official_phone"],
            hospital_data.get("license_doc_url"),
            hospital_data.get("verification_status", "pending"),
            hospital_data.get("verified_at"),
            hospital_data["created_at"],
            hospital_data["updated_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return hospital_data

    def get_hospital_by_id(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT h.*, u.full_name as contact_person, u.email as account_email, u.phone as account_phone
            FROM hospitals h
            JOIN users u ON h.user_id = u.user_id
            WHERE h.hospital_id = ?
        """
        with get_db_connection() as conn:
            row = conn.execute(query, (hospital_id,)).fetchone()
            return dict(row) if row else None

    def get_hospital_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT h.*, u.full_name as contact_person, u.email as account_email, u.phone as account_phone
            FROM hospitals h
            JOIN users u ON h.user_id = u.user_id
            WHERE h.user_id = ?
        """
        with get_db_connection() as conn:
            row = conn.execute(query, (user_id,)).fetchone()
            return dict(row) if row else None

    def update_hospital_verification(
        self,
        hospital_id: str,
        status: str,
        verified_at: Optional[str] = None
    ) -> bool:
        query = """
            UPDATE hospitals
            SET verification_status = ?, verified_at = ?, updated_at = datetime('now')
            WHERE hospital_id = ?
        """
        with get_db_connection() as conn:
            cursor = conn.execute(query, (status, verified_at, hospital_id))
            return cursor.rowcount > 0

    def list_hospitals(self, verification_status: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            if verification_status:
                query = """
                    SELECT h.*, u.email as account_email
                    FROM hospitals h
                    JOIN users u ON h.user_id = u.user_id
                    WHERE h.verification_status = ?
                    ORDER BY h.created_at DESC
                """
                rows = conn.execute(query, (verification_status,)).fetchall()
            else:
                query = """
                    SELECT h.*, u.email as account_email
                    FROM hospitals h
                    JOIN users u ON h.user_id = u.user_id
                    ORDER BY h.created_at DESC
                """
                rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    # ---------------- BLOOD REQUEST OPERATIONS ---------------- #
    def create_blood_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO blood_requests (
                request_id, requester_user_id, request_type, blood_group,
                units_needed, hospital_name, locality, latitude, longitude,
                urgency, requisition_doc_url, verification_status, request_status,
                required_by_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            request_data["request_id"],
            request_data["requester_user_id"],
            request_data["request_type"],
            request_data["blood_group"],
            request_data["units_needed"],
            request_data["hospital_name"],
            request_data["locality"],
            request_data["latitude"],
            request_data["longitude"],
            request_data["urgency"],
            request_data.get("requisition_doc_url"),
            request_data.get("verification_status", "pending"),
            request_data.get("request_status", "open"),
            request_data["required_by_date"],
            request_data["created_at"],
            request_data["updated_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return request_data

    def get_blood_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT r.*, u.full_name as requester_name, u.phone as requester_phone, u.email as requester_email
            FROM blood_requests r
            JOIN users u ON r.requester_user_id = u.user_id
            WHERE r.request_id = ?
        """
        with get_db_connection() as conn:
            row = conn.execute(query, (request_id,)).fetchone()
            return dict(row) if row else None

    def update_request_verification(
        self,
        request_id: str,
        verification_status: str
    ) -> bool:
        query = """
            UPDATE blood_requests
            SET verification_status = ?, updated_at = datetime('now')
            WHERE request_id = ?
        """
        with get_db_connection() as conn:
            cursor = conn.execute(query, (verification_status, request_id))
            return cursor.rowcount > 0

    def update_request_lifecycle(
        self,
        request_id: str,
        request_status: str
    ) -> bool:
        query = """
            UPDATE blood_requests
            SET request_status = ?, updated_at = datetime('now')
            WHERE request_id = ?
        """
        with get_db_connection() as conn:
            cursor = conn.execute(query, (request_status, request_id))
            return cursor.rowcount > 0

    def list_blood_requests(
        self,
        requester_user_id: Optional[str] = None,
        verification_status: Optional[str] = None,
        request_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []

        if requester_user_id:
            conditions.append("r.requester_user_id = ?")
            params.append(requester_user_id)
        if verification_status:
            conditions.append("r.verification_status = ?")
            params.append(verification_status)
        if request_status:
            conditions.append("r.request_status = ?")
            params.append(request_status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT r.*, u.full_name as requester_name, u.phone as requester_phone
            FROM blood_requests r
            JOIN users u ON r.requester_user_id = u.user_id
            {where_clause}
            ORDER BY r.created_at DESC
        """
        with get_db_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(row) for row in rows]

    # ---------------- DONOR RESPONSE OPERATIONS ---------------- #
    def save_donor_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO donor_responses (
                response_id, request_id, donor_id, status, contact_revealed, responded_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_id, donor_id) DO UPDATE SET
                status = excluded.status,
                contact_revealed = excluded.contact_revealed,
                responded_at = excluded.responded_at
        """
        params = (
            response_data["response_id"],
            response_data["request_id"],
            response_data["donor_id"],
            response_data["status"],
            response_data.get("contact_revealed", 0),
            response_data["responded_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return response_data

    def get_donor_response(self, request_id: str, donor_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM donor_responses
            WHERE request_id = ? AND donor_id = ?
        """
        with get_db_connection() as conn:
            row = conn.execute(query, (request_id, donor_id)).fetchone()
            return dict(row) if row else None

    def list_responses_for_request(self, request_id: str) -> List[Dict[str, Any]]:
        query = """
            SELECT dr.*, d.blood_group, d.locality as donor_locality,
                   u.full_name as donor_name,
                   CASE WHEN dr.contact_revealed = 1 THEN u.phone ELSE NULL END as donor_phone,
                   CASE WHEN dr.contact_revealed = 1 THEN u.email ELSE NULL END as donor_email
            FROM donor_responses dr
            JOIN donors d ON dr.donor_id = d.donor_id
            JOIN users u ON d.user_id = u.user_id
            WHERE dr.request_id = ?
            ORDER BY dr.responded_at ASC
        """
        with get_db_connection() as conn:
            rows = conn.execute(query, (request_id,)).fetchall()
            return [dict(row) for row in rows]

    def list_responses_for_donor(self, donor_id: str) -> List[Dict[str, Any]]:
        query = """
            SELECT dr.*, r.blood_group, r.units_needed, r.hospital_name,
                   r.locality as request_locality, r.urgency, r.request_status
            FROM donor_responses dr
            JOIN blood_requests r ON dr.request_id = r.request_id
            WHERE dr.donor_id = ?
            ORDER BY dr.responded_at DESC
        """
        with get_db_connection() as conn:
            rows = conn.execute(query, (donor_id,)).fetchall()
            return [dict(row) for row in rows]

    # ---------------- NOTIFICATION OPERATIONS ---------------- #
    def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO notifications (
                notification_id, recipient_user_id, request_id, channel, subject, message_body, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            notification_data["notification_id"],
            notification_data["recipient_user_id"],
            notification_data.get("request_id"),
            notification_data.get("channel", "console_simulator"),
            notification_data["subject"],
            notification_data["message_body"],
            notification_data.get("status", "delivered"),
            notification_data["created_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return notification_data

    def list_notifications(
        self,
        recipient_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            if recipient_user_id:
                rows = conn.execute(
                    "SELECT * FROM notifications WHERE recipient_user_id = ? ORDER BY created_at DESC",
                    (recipient_user_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM notifications ORDER BY created_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]

    # ---------------- AUDIT LOG OPERATIONS ---------------- #
    def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO audit_logs (
                log_id, actor_user_id, action, target_entity, target_id, details_json, ip_address, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        details = log_data.get("details_json")
        if isinstance(details, (dict, list)):
            details = json.dumps(details)

        params = (
            log_data["log_id"],
            log_data.get("actor_user_id"),
            log_data["action"],
            log_data["target_entity"],
            log_data["target_id"],
            details,
            log_data.get("ip_address", "127.0.0.1"),
            log_data["created_at"]
        )
        with get_db_connection() as conn:
            conn.execute(query, params)
        return log_data

    def list_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
            SELECT a.*, u.email as actor_email, u.role as actor_role
            FROM audit_logs a
            LEFT JOIN users u ON a.actor_user_id = u.user_id
            ORDER BY a.created_at DESC
            LIMIT ?
        """
        with get_db_connection() as conn:
            rows = conn.execute(query, (limit,)).fetchall()
            results = []
            for row in rows:
                item = dict(row)
                if item["details_json"]:
                    try:
                        item["details_json"] = json.loads(item["details_json"])
                    except Exception:
                        pass
                results.append(item)
            return results