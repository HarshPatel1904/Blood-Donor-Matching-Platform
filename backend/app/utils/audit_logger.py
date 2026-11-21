import uuid
import datetime
import json
from typing import Optional, Dict, Any
from app.repositories import get_repository


def log_action(
    actor_user_id: Optional[str],
    action: str,
    target_entity: str,
    target_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1"
) -> Dict[str, Any]:
    """
    Creates an immutable audit record for administrative and system actions.
    """
    repo = get_repository()
    log_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    log_entry = {
        "log_id": log_id,
        "actor_user_id": actor_user_id,
        "action": action,
        "target_entity": target_entity,
        "target_id": target_id,
        "details_json": details or {},
        "ip_address": ip_address,
        "created_at": now
    }

    repo.create_audit_log(log_entry)
    return log_entry