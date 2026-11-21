import datetime
import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from app.config import Config
from app.repositories.base_repository import BaseRepository


def _to_dynamo(value: Any) -> Any:
    """Recursively converts Python float values into Decimal for DynamoDB compatibility."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_dynamo(v) for v in value]
    return value


def _from_dynamo(value: Any) -> Any:
    """Recursively converts DynamoDB Decimal values back to int or float for JSON safety."""
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(v) for v in value]
    return value


def _is_truthy_flag(val: Any) -> bool:
    """Handles both integer (1/0) and boolean (True/False) flag representations."""
    if isinstance(val, bool):
        return val
    try:
        return int(val) == 1
    except (TypeError, ValueError):
        return False


class DynamoDBRepository(BaseRepository):
    """Concrete DynamoDB implementation of BaseRepository for Stage 2 AWS deployment."""

    def __init__(self, dynamodb_resource: Optional[Any] = None):
        self.dynamodb = dynamodb_resource or boto3.resource(
            "dynamodb", region_name=Config.AWS_REGION
        )
        prefix = Config.DYNAMODB_TABLE_PREFIX
        self.users_table = self.dynamodb.Table(f"{prefix}users")
        self.donors_table = self.dynamodb.Table(f"{prefix}donors")
        self.hospitals_table = self.dynamodb.Table(f"{prefix}hospitals")
        self.requests_table = self.dynamodb.Table(f"{prefix}blood_requests")
        self.responses_table = self.dynamodb.Table(f"{prefix}donor_responses")
        self.notifications_table = self.dynamodb.Table(f"{prefix}notifications")
        self.audit_table = self.dynamodb.Table(f"{prefix}audit_logs")

    @staticmethod
    def _scan_all(table: Any, filter_expression: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Performs a paginated DynamoDB scan and normalizes all returned items."""
        kwargs: Dict[str, Any] = {}
        if filter_expression is not None:
            kwargs["FilterExpression"] = filter_expression

        items: List[Dict[str, Any]] = []
        response = table.scan(**kwargs)
        items.extend(_from_dynamo(item) for item in response.get("Items", []))

        while "LastEvaluatedKey" in response:
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.scan(**kwargs)
            items.extend(_from_dynamo(item) for item in response.get("Items", []))

        return items

    @staticmethod
    def _now_iso() -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _update_fields(
        self,
        table: Any,
        key: Dict[str, Any],
        pk_attr: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Executes a conditional DynamoDB update_item if the primary key exists."""
        expr_names: Dict[str, str] = {}
        expr_values: Dict[str, Any] = {}
        set_clauses: List[str] = []

        for idx, (field, val) in enumerate(updates.items()):
            name_ph = f"#f{idx}"
            val_ph = f":v{idx}"
            expr_names[name_ph] = field
            expr_values[val_ph] = _to_dynamo(val)
            set_clauses.append(f"{name_ph} = {val_ph}")

        try:
            table.update_item(
                Key=key,
                UpdateExpression="SET " + ", ".join(set_clauses),
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ConditionExpression=Attr(pk_attr).exists(),
            )
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return False
            raise

    def _users_by_id_map(self) -> Dict[str, Dict[str, Any]]:
        return {u["user_id"]: u for u in self._scan_all(self.users_table)}

    # ---------------- USER OPERATIONS ---------------- #
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(user_data)
        record.setdefault("is_active", 1)
        self.users_table.put_item(Item=_to_dynamo(record))
        return record

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        res = self.users_table.get_item(Key={"user_id": user_id})
        item = res.get("Item")
        return _from_dynamo(item) if item else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        target = (email or "").strip().lower()
        if not target:
            return None
        for user in self._scan_all(self.users_table):
            if (user.get("email") or "").strip().lower() == target:
                return user
        return None

    def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        filter_expr = Attr("role").eq(role) if role else None
        users = self._scan_all(self.users_table, filter_expr)
        users.sort(key=lambda u: u.get("created_at") or "", reverse=True)
        return users

    def update_user_status(self, user_id: str, is_active: int) -> bool:
        return self._update_fields(
            self.users_table,
            {"user_id": user_id},
            "user_id",
            {"is_active": int(is_active), "updated_at": self._now_iso()},
        )

    # ---------------- DONOR OPERATIONS ---------------- #
    def create_donor(self, donor_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(donor_data)
        record.setdefault("is_available", 1)
        record.setdefault("consent_share_contact", 1)
        record.setdefault("email_notifications", 1)
        self.donors_table.put_item(Item=_to_dynamo(record))
        return record

    def _enrich_donor(
        self, donor: Dict[str, Any], user: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        enriched = dict(donor)
        if user:
            enriched["full_name"] = user.get("full_name")
            enriched["email"] = user.get("email")
            enriched["phone"] = user.get("phone")
            enriched["is_active"] = user.get("is_active", 1)
        return enriched

    def get_donor_by_id(self, donor_id: str) -> Optional[Dict[str, Any]]:
        res = self.donors_table.get_item(Key={"donor_id": donor_id})
        item = res.get("Item")
        if not item:
            return None
        donor = _from_dynamo(item)
        user = self.get_user_by_id(donor["user_id"])
        return self._enrich_donor(donor, user)

    def get_donor_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        matches = self._scan_all(self.donors_table, Attr("user_id").eq(user_id))
        if not matches:
            return None
        user = self.get_user_by_id(user_id)
        return self._enrich_donor(matches[0], user)

    def update_donor_profile(self, donor_id: str, updates: Dict[str, Any]) -> bool:
        allowed_fields = {
            "blood_group",
            "city",
            "locality",
            "latitude",
            "longitude",
            "is_available",
            "consent_share_contact",
            "email_notifications",
            "last_donated_date",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed_fields}
        if not filtered:
            return False
        filtered["updated_at"] = self._now_iso()
        return self._update_fields(
            self.donors_table, {"donor_id": donor_id}, "donor_id", filtered
        )

    def update_donor_availability(self, donor_id: str, is_available: int) -> bool:
        return self._update_fields(
            self.donors_table,
            {"donor_id": donor_id},
            "donor_id",
            {"is_available": int(is_available), "updated_at": self._now_iso()},
        )

    def list_donors(
        self,
        blood_group: Optional[str] = None,
        is_available: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        filter_expr = Attr("blood_group").eq(blood_group) if blood_group else None
        donors = self._scan_all(self.donors_table, filter_expr)
        users_map = self._users_by_id_map()

        results: List[Dict[str, Any]] = []
        for donor in donors:
            user = users_map.get(donor.get("user_id"))
            if not user or not _is_truthy_flag(user.get("is_active", 0)):
                continue
            if is_available is not None:
                if int(_is_truthy_flag(donor.get("is_available", 0))) != int(
                    _is_truthy_flag(is_available)
                ):
                    continue
            enriched = dict(donor)
            enriched["full_name"] = user.get("full_name")
            enriched["email"] = user.get("email")
            enriched["phone"] = user.get("phone")
            results.append(enriched)

        results.sort(key=lambda d: d.get("created_at") or "", reverse=True)
        return results

    # ---------------- HOSPITAL OPERATIONS ---------------- #
    def create_hospital(self, hospital_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(hospital_data)
        record.setdefault("verification_status", "pending")
        self.hospitals_table.put_item(Item=_to_dynamo(record))
        return record

    def _enrich_hospital(
        self, hospital: Dict[str, Any], user: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        enriched = dict(hospital)
        if user:
            enriched["contact_person"] = user.get("full_name")
            enriched["account_email"] = user.get("email")
            enriched["account_phone"] = user.get("phone")
        return enriched

    def get_hospital_by_id(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        res = self.hospitals_table.get_item(Key={"hospital_id": hospital_id})
        item = res.get("Item")
        if not item:
            return None
        hospital = _from_dynamo(item)
        user = self.get_user_by_id(hospital["user_id"])
        return self._enrich_hospital(hospital, user)

    def get_hospital_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        matches = self._scan_all(self.hospitals_table, Attr("user_id").eq(user_id))
        if not matches:
            return None
        user = self.get_user_by_id(user_id)
        return self._enrich_hospital(matches[0], user)

    def update_hospital_verification(
        self,
        hospital_id: str,
        status: str,
        verified_at: Optional[str] = None,
    ) -> bool:
        return self._update_fields(
            self.hospitals_table,
            {"hospital_id": hospital_id},
            "hospital_id",
            {
                "verification_status": status,
                "verified_at": verified_at,
                "updated_at": self._now_iso(),
            },
        )

    def list_hospitals(
        self, verification_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filter_expr = (
            Attr("verification_status").eq(verification_status)
            if verification_status
            else None
        )
        hospitals = self._scan_all(self.hospitals_table, filter_expr)
        users_map = self._users_by_id_map()

        results: List[Dict[str, Any]] = []
        for hospital in hospitals:
            user = users_map.get(hospital.get("user_id"))
            if not user:
                continue
            enriched = dict(hospital)
            enriched["account_email"] = user.get("email")
            results.append(enriched)

        results.sort(key=lambda h: h.get("created_at") or "", reverse=True)
        return results

    # ---------------- BLOOD REQUEST OPERATIONS ---------------- #
    def create_blood_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(request_data)
        record.setdefault("verification_status", "pending")
        record.setdefault("request_status", "open")
        self.requests_table.put_item(Item=_to_dynamo(record))
        return record

    def get_blood_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        res = self.requests_table.get_item(Key={"request_id": request_id})
        item = res.get("Item")
        if not item:
            return None
        req = _from_dynamo(item)
        user = self.get_user_by_id(req["requester_user_id"])
        if user:
            req["requester_name"] = user.get("full_name")
            req["requester_phone"] = user.get("phone")
            req["requester_email"] = user.get("email")
        return req

    def update_request_verification(
        self,
        request_id: str,
        verification_status: str,
    ) -> bool:
        return self._update_fields(
            self.requests_table,
            {"request_id": request_id},
            "request_id",
            {
                "verification_status": verification_status,
                "updated_at": self._now_iso(),
            },
        )

    def update_request_lifecycle(
        self,
        request_id: str,
        request_status: str,
    ) -> bool:
        return self._update_fields(
            self.requests_table,
            {"request_id": request_id},
            "request_id",
            {
                "request_status": request_status,
                "updated_at": self._now_iso(),
            },
        )

    def list_blood_requests(
        self,
        requester_user_id: Optional[str] = None,
        verification_status: Optional[str] = None,
        request_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        expr = None
        for attr_name, attr_val in (
            ("requester_user_id", requester_user_id),
            ("verification_status", verification_status),
            ("request_status", request_status),
        ):
            if attr_val:
                cond = Attr(attr_name).eq(attr_val)
                expr = cond if expr is None else (expr & cond)

        requests = self._scan_all(self.requests_table, expr)
        users_map = self._users_by_id_map()

        results: List[Dict[str, Any]] = []
        for req in requests:
            user = users_map.get(req.get("requester_user_id"))
            if not user:
                continue
            enriched = dict(req)
            enriched["requester_name"] = user.get("full_name")
            enriched["requester_phone"] = user.get("phone")
            results.append(enriched)

        results.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return results

    # ---------------- DONOR RESPONSE OPERATIONS ---------------- #
    def save_donor_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(response_data)
        record.setdefault("contact_revealed", 0)
        existing = self.get_donor_response(record["request_id"], record["donor_id"])
        if existing:
            record["response_id"] = existing["response_id"]
        self.responses_table.put_item(Item=_to_dynamo(record))
        return record

    def get_donor_response(
        self, request_id: str, donor_id: str
    ) -> Optional[Dict[str, Any]]:
        matches = self._scan_all(
            self.responses_table,
            Attr("request_id").eq(request_id) & Attr("donor_id").eq(donor_id),
        )
        return matches[0] if matches else None

    def list_responses_for_request(self, request_id: str) -> List[Dict[str, Any]]:
        responses = self._scan_all(
            self.responses_table, Attr("request_id").eq(request_id)
        )
        donors_map = {
            d["donor_id"]: d for d in self._scan_all(self.donors_table)
        }
        users_map = self._users_by_id_map()

        results: List[Dict[str, Any]] = []
        for resp in responses:
            donor = donors_map.get(resp.get("donor_id"))
            if not donor:
                continue
            user = users_map.get(donor.get("user_id"))
            if not user:
                continue

            revealed = _is_truthy_flag(resp.get("contact_revealed", 0))
            enriched = dict(resp)
            enriched["blood_group"] = donor.get("blood_group")
            enriched["donor_locality"] = donor.get("locality")
            enriched["donor_name"] = user.get("full_name")
            enriched["donor_phone"] = user.get("phone") if revealed else None
            enriched["donor_email"] = user.get("email") if revealed else None
            results.append(enriched)

        results.sort(key=lambda r: r.get("responded_at") or "")
        return results

    def list_responses_for_donor(self, donor_id: str) -> List[Dict[str, Any]]:
        responses = self._scan_all(
            self.responses_table, Attr("donor_id").eq(donor_id)
        )
        requests_map = {
            r["request_id"]: r for r in self._scan_all(self.requests_table)
        }

        results: List[Dict[str, Any]] = []
        for resp in responses:
            req = requests_map.get(resp.get("request_id"))
            if not req:
                continue
            enriched = dict(resp)
            enriched["blood_group"] = req.get("blood_group")
            enriched["units_needed"] = req.get("units_needed")
            enriched["hospital_name"] = req.get("hospital_name")
            enriched["request_locality"] = req.get("locality")
            enriched["urgency"] = req.get("urgency")
            enriched["request_status"] = req.get("request_status")
            results.append(enriched)

        results.sort(key=lambda r: r.get("responded_at") or "", reverse=True)
        return results

    # ---------------- NOTIFICATION OPERATIONS ---------------- #
    def create_notification(
        self, notification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        record = dict(notification_data)
        record.setdefault("channel", "console_simulator")
        record.setdefault("status", "delivered")
        self.notifications_table.put_item(Item=_to_dynamo(record))
        return record

    def list_notifications(
        self, recipient_user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filter_expr = (
            Attr("recipient_user_id").eq(recipient_user_id)
            if recipient_user_id
            else None
        )
        items = self._scan_all(self.notifications_table, filter_expr)
        items.sort(key=lambda n: n.get("created_at") or "", reverse=True)
        return items

    # ---------------- AUDIT LOG OPERATIONS ---------------- #
    def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(log_data)
        details = record.get("details_json")
        if isinstance(details, (dict, list)):
            record["details_json"] = json.dumps(details)
        record.setdefault("ip_address", "127.0.0.1")
        self.audit_table.put_item(Item=_to_dynamo(record))
        return log_data

    def list_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        logs = self._scan_all(self.audit_table)
        users_map = self._users_by_id_map()

        results: List[Dict[str, Any]] = []
        for item in logs:
            enriched = dict(item)
            actor = users_map.get(enriched.get("actor_user_id"))
            enriched["actor_email"] = actor.get("email") if actor else None
            enriched["actor_role"] = actor.get("role") if actor else None
            if isinstance(enriched.get("details_json"), str):
                try:
                    enriched["details_json"] = json.loads(enriched["details_json"])
                except Exception:
                    pass
            results.append(enriched)

        results.sort(key=lambda l: l.get("created_at") or "", reverse=True)
        return results[:limit]
