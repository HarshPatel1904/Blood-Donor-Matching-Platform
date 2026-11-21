import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import Config
from app.repositories.sqlite_conn import get_db_connection, get_db_path

DDL_STATEMENTS = [
    # 1. Users Table
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('donor', 'requester', 'hospital', 'admin')),
        phone TEXT NOT NULL,
        full_name TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,

    # 2. Donors Table
    """
    CREATE TABLE IF NOT EXISTS donors (
        donor_id TEXT PRIMARY KEY,
        user_id TEXT UNIQUE NOT NULL,
        blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
        city TEXT NOT NULL,
        locality TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        is_available INTEGER NOT NULL DEFAULT 1 CHECK(is_available IN (0, 1)),
        consent_share_contact INTEGER NOT NULL DEFAULT 1 CHECK(consent_share_contact IN (0, 1)),
        email_notifications INTEGER NOT NULL DEFAULT 1 CHECK(email_notifications IN (0, 1)),
        last_donated_date TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """,

    # 3. Hospitals Table
    """
    CREATE TABLE IF NOT EXISTS hospitals (
        hospital_id TEXT PRIMARY KEY,
        user_id TEXT UNIQUE NOT NULL,
        hospital_name TEXT NOT NULL,
        license_number TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        locality TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        official_phone TEXT NOT NULL,
        license_doc_url TEXT,
        verification_status TEXT NOT NULL DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
        verified_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """,

    # 4. Blood Requests Table
    """
    CREATE TABLE IF NOT EXISTS blood_requests (
        request_id TEXT PRIMARY KEY,
        requester_user_id TEXT NOT NULL,
        request_type TEXT NOT NULL CHECK(request_type IN ('individual', 'hospital')),
        blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
        units_needed INTEGER NOT NULL CHECK(units_needed > 0),
        hospital_name TEXT NOT NULL,
        locality TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        urgency TEXT NOT NULL CHECK(urgency IN ('normal', 'urgent', 'critical')),
        requisition_doc_url TEXT,
        verification_status TEXT NOT NULL DEFAULT 'pending' CHECK(verification_status IN ('pending', 'approved', 'rejected', 'on_hold')),
        request_status TEXT NOT NULL DEFAULT 'open' CHECK(request_status IN ('open', 'donors_notified', 'fulfilled', 'cancelled', 'expired')),
        required_by_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (requester_user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """,

    # 5. Donor Responses Table
    """
    CREATE TABLE IF NOT EXISTS donor_responses (
        response_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        donor_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'declined', 'unavailable', 'withdrawn')),
        contact_revealed INTEGER NOT NULL DEFAULT 0 CHECK(contact_revealed IN (0, 1)),
        responded_at TEXT NOT NULL,
        UNIQUE(request_id, donor_id),
        FOREIGN KEY (request_id) REFERENCES blood_requests(request_id) ON DELETE CASCADE,
        FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE
    );
    """,

    # 6. Notifications Table
    """
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id TEXT PRIMARY KEY,
        recipient_user_id TEXT NOT NULL,
        request_id TEXT,
        channel TEXT NOT NULL DEFAULT 'console_simulator',
        subject TEXT NOT NULL,
        message_body TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'delivered' CHECK(status IN ('queued', 'delivered', 'failed')),
        created_at TEXT NOT NULL,
        FOREIGN KEY (recipient_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (request_id) REFERENCES blood_requests(request_id) ON DELETE SET NULL
    );
    """,

    # 7. Audit Logs Table
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id TEXT PRIMARY KEY,
        actor_user_id TEXT,
        action TEXT NOT NULL,
        target_entity TEXT NOT NULL,
        target_id TEXT NOT NULL,
        details_json TEXT,
        ip_address TEXT DEFAULT '127.0.0.1',
        created_at TEXT NOT NULL,
        FOREIGN KEY (actor_user_id) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """
]

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
    "CREATE INDEX IF NOT EXISTS idx_donors_blood_group ON donors(blood_group);",
    "CREATE INDEX IF NOT EXISTS idx_donors_locality ON donors(locality);",
    "CREATE INDEX IF NOT EXISTS idx_hospitals_status ON hospitals(verification_status);",
    "CREATE INDEX IF NOT EXISTS idx_requests_status ON blood_requests(request_status);",
    "CREATE INDEX IF NOT EXISTS idx_requests_verification ON blood_requests(verification_status);",
    "CREATE INDEX IF NOT EXISTS idx_requests_blood ON blood_requests(blood_group);",
    "CREATE INDEX IF NOT EXISTS idx_responses_req_donor ON donor_responses(request_id, donor_id);",
    "CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_user_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);"
]


def init_database():
    """Initializes the SQLite schema and indexes."""
    db_path = get_db_path()
    print(f"Initializing database at: {db_path}")

    with get_db_connection() as conn:
        for ddl in DDL_STATEMENTS:
            conn.execute(ddl)
        for idx in INDEX_STATEMENTS:
            conn.execute(idx)

    print("All 7 tables and 11 indexes created successfully.")


if __name__ == "__main__":
    init_database()