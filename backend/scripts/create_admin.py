import sys
import uuid
import datetime
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from werkzeug.security import generate_password_hash
from app.repositories import get_repository


def create_admin_account(
    email: str = "admin@bloodplatform.local",
    password: str = "AdminRoot2026!",
    full_name: str = "System Administrator",
    phone: str = "+919999900000"
):
    repo = get_repository()
    existing = repo.get_user_by_email(email)
    if existing:
        print(f"Admin account with email '{email}' already exists. User ID: {existing['user_id']}")
        return existing["user_id"]

    user_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    admin_record = {
        "user_id": user_id,
        "email": email.strip().lower(),
        "password_hash": generate_password_hash(password),
        "role": "admin",
        "phone": phone.strip(),
        "full_name": full_name.strip(),
        "is_active": 1,
        "created_at": now,
        "updated_at": now
    }

    repo.create_user(admin_record)
    print("--------------------------------------------------")
    print("Platform Administrator created successfully:")
    print(f"  User ID : {user_id}")
    print(f"  Email   : {email}")
    print(f"  Role    : admin")
    print(f"  Password: {password}")
    print("--------------------------------------------------")
    return user_id


if __name__ == "__main__":
    create_admin_account()