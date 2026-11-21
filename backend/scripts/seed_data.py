import sys
import uuid
import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from werkzeug.security import generate_password_hash
from app.config import Config
from app.repositories.sqlite_conn import get_db_connection

# Load Ahmedabad coordinates from localities.json
with open(Config.LOCALITIES_FILE, "r", encoding="utf-8") as f:
    localities_data = json.load(f)
    LOCALITY_COORDS = {
        loc["name"].strip().lower(): (loc["latitude"], loc["longitude"])
        for loc in localities_data.get("localities", [])
    }

DEMO_TIMESTAMP = datetime.datetime.now(datetime.timezone.utc).isoformat()

# ----------------- SYNTHETIC USERS ----------------- #
ADMIN_USER = {
    "user_id": str(uuid.uuid4()),
    "email": "admin@bloodplatform.local",
    "password_hash": generate_password_hash("AdminRoot2026!"),
    "role": "admin",
    "phone": "+919999900000",
    "full_name": "Platform Administrator",
    "is_active": 1,
    "created_at": DEMO_TIMESTAMP,
    "updated_at": DEMO_TIMESTAMP
}

REQUESTERS = [
    {
        "user_id": str(uuid.uuid4()),
        "email": "priya.patel@example.com",
        "password_hash": generate_password_hash("RequesterPass123!"),
        "role": "requester",
        "phone": "+919825100001",
        "full_name": "Priya Patel (Demo Requester)",
        "is_active": 1,
        "created_at": DEMO_TIMESTAMP,
        "updated_at": DEMO_TIMESTAMP
    },
    {
        "user_id": str(uuid.uuid4()),
        "email": "arjun.mehta@example.com",
        "password_hash": generate_password_hash("RequesterPass123!"),
        "role": "requester",
        "phone": "+919825100002",
        "full_name": "Arjun Mehta (Demo Requester)",
        "is_active": 1,
        "created_at": DEMO_TIMESTAMP,
        "updated_at": DEMO_TIMESTAMP
    }
]

HOSPITALS = [
    {
        "user": {
            "user_id": str(uuid.uuid4()),
            "email": "contact@apolloahmedabad.local",
            "password_hash": generate_password_hash("HospitalPass123!"),
            "role": "hospital",
            "phone": "+917966701800",
            "full_name": "Dr. Ramesh Desai (Medical Supt.)",
            "is_active": 1,
            "created_at": DEMO_TIMESTAMP,
            "updated_at": DEMO_TIMESTAMP
        },
        "profile": {
            "hospital_id": str(uuid.uuid4()),
            "hospital_name": "Apollo Hospitals International",
            "license_number": "GJ-AHM-HOSP-2026-001",
            "address": "Plot 1A, GIDC Bhat, Gandhinagar Highway",
            "locality": "Chandkheda",
            "official_phone": "+917966701800",
            "license_doc_url": "uploads/hospital_licenses/demo_apollo_license.pdf",
            "verification_status": "verified",
            "verified_at": DEMO_TIMESTAMP
        }
    },
    {
        "user": {
            "user_id": str(uuid.uuid4()),
            "email": "desk@kdhospital.local",
            "password_hash": generate_password_hash("HospitalPass123!"),
            "role": "hospital",
            "phone": "+917967770000",
            "full_name": "Dr. Neha Shah (Blood Bank Officer)",
            "is_active": 1,
            "created_at": DEMO_TIMESTAMP,
            "updated_at": DEMO_TIMESTAMP
        },
        "profile": {
            "hospital_id": str(uuid.uuid4()),
            "hospital_name": "KD Hospital",
            "license_number": "GJ-AHM-HOSP-2026-002",
            "address": "S.G. Highway, Near Vaishnodevi Circle",
            "locality": "SG Highway",
            "official_phone": "+917967770000",
            "license_doc_url": "uploads/hospital_licenses/demo_kd_license.pdf",
            "verification_status": "pending",
            "verified_at": None
        }
    }
]

RAW_DONORS = [
    # B+ Cohort (Primary scenario match)
    ("Rahul Sharma", "rahul.sharma@example.com", "B+", "Navrangpura", 1, 1, 1, "2026-08-10"),
    ("Amit Shah", "amit.shah@example.com", "B+", "Vastrapur", 1, 1, 1, "2026-07-20"),
    ("Sneha Joshi", "sneha.joshi@example.com", "B+", "Satellite", 1, 1, 1, "2026-06-15"),
    ("Kavita Trivedi", "kavita.t@example.com", "B+", "Bopal", 0, 1, 1, "2026-09-01"),  # Unavailable

    # O+ Universal Pack Cohort
    ("Vikram Rathod", "vikram.r@example.com", "O+", "Paldi", 1, 1, 1, "2026-05-10"),
    ("Pooja Nair", "pooja.nair@example.com", "O+", "Maninagar", 1, 1, 1, "2026-08-25"),
    ("Manish Prajapati", "manish.p@example.com", "O+", "Chandkheda", 1, 1, 1, "2026-07-12"),

    # A+ Cohort
    ("Ananya Roy", "ananya.roy@example.com", "A+", "Thaltej", 1, 1, 1, "2026-08-01"),
    ("Deepak Verma", "deepak.v@example.com", "A+", "Gota", 1, 0, 1, "2026-04-18"),

    # AB+ / AB- Cohorts
    ("Rohan Patel", "rohan.p@example.com", "AB+", "SG Highway", 1, 1, 1, "2026-08-30"),
    ("Bhavin Solanki", "bhavin.s@example.com", "AB-", "Navrangpura", 1, 1, 0, "2026-03-22"),

    # O- Rare Cohort
    ("Meera Vora", "meera.vora@example.com", "O-", "Vastrapur", 1, 1, 1, "2026-06-05")
]


def seed_database():
    print("---------------------------------------------------------------")
    print("  SEEDING ARTIFICIAL DEMONSTRATION DATA (AHMEDABAD LOCALITIES) ")
    print("---------------------------------------------------------------")

    with get_db_connection() as conn:
        # Clear existing test records to ensure an idempotent state
        conn.execute("DELETE FROM donor_responses;")
        conn.execute("DELETE FROM notifications;")
        conn.execute("DELETE FROM blood_requests;")
        conn.execute("DELETE FROM audit_logs;")
        conn.execute("DELETE FROM hospitals;")
        conn.execute("DELETE FROM donors;")
        conn.execute("DELETE FROM users;")

        # 1. Insert Admin
        conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, role, phone, full_name, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ADMIN_USER["user_id"],
                ADMIN_USER["email"],
                ADMIN_USER["password_hash"],
                ADMIN_USER["role"],
                ADMIN_USER["phone"],
                ADMIN_USER["full_name"],
                ADMIN_USER["is_active"],
                ADMIN_USER["created_at"],
                ADMIN_USER["updated_at"]
            )
        )
        print(f"[OK] Seeded Admin: {ADMIN_USER['email']}")

        # 2. Insert Requesters
        for req in REQUESTERS:
            conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, role, phone, full_name, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    req["user_id"],
                    req["email"],
                    req["password_hash"],
                    req["role"],
                    req["phone"],
                    req["full_name"],
                    req["is_active"],
                    req["created_at"],
                    req["updated_at"]
                )
            )
            print(f"[OK] Seeded Requester: {req['email']}")

        # 3. Insert Hospitals
        for hosp in HOSPITALS:
            u = hosp["user"]
            p = hosp["profile"]
            loc_key = p["locality"].strip().lower()
            lat, lon = LOCALITY_COORDS.get(loc_key, (23.0225, 72.5714))

            conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, role, phone, full_name, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (u["user_id"], u["email"], u["password_hash"], u["role"], u["phone"], u["full_name"], u["is_active"], u["created_at"], u["updated_at"])
            )
            conn.execute(
                """
                INSERT INTO hospitals (hospital_id, user_id, hospital_name, license_number, address, locality, latitude, longitude, official_phone, license_doc_url, verification_status, verified_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (p["hospital_id"], u["user_id"], p["hospital_name"], p["license_number"], p["address"], p["locality"], lat, lon, p["official_phone"], p["license_doc_url"], p["verification_status"], p["verified_at"], DEMO_TIMESTAMP, DEMO_TIMESTAMP)
            )
            print(f"[OK] Seeded Hospital: {p['hospital_name']} ({p['verification_status']})")

        # 4. Insert Donors
        seeded_donor_count = 0
        for name, email, bg, locality, avail, consent, notif, last_date in RAW_DONORS:
            user_id = str(uuid.uuid4())
            donor_id = str(uuid.uuid4())
            loc_key = locality.strip().lower()
            lat, lon = LOCALITY_COORDS.get(loc_key, (23.0225, 72.5714))

            conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, role, phone, full_name, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    email,
                    generate_password_hash("DonorPass123!"),
                    "donor",
                    f"+9198765{seeded_donor_count:05d}",
                    f"{name} (Demo)",
                    1,
                    DEMO_TIMESTAMP,
                    DEMO_TIMESTAMP
                )
            )

            conn.execute(
                """
                INSERT INTO donors (donor_id, user_id, blood_group, city, locality, latitude, longitude, is_available, consent_share_contact, email_notifications, last_donated_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    donor_id,
                    user_id,
                    bg,
                    "Ahmedabad",
                    locality,
                    lat,
                    lon,
                    avail,
                    consent,
                    notif,
                    last_date,
                    DEMO_TIMESTAMP,
                    DEMO_TIMESTAMP
                )
            )
            seeded_donor_count += 1

        print(f"[OK] Successfully seeded {seeded_donor_count} artificial voluntary donors.")

    print("---------------------------------------------------------------")
    print("Seed process complete. Credentials for demo scenario:")
    print("  - Admin     : admin@bloodplatform.local / AdminRoot2026!")
    print("  - Hospital  : contact@apolloahmedabad.local / HospitalPass123!")
    print("  - Requester : priya.patel@example.com / RequesterPass123!")
    print("  - Donors    : (All use password: DonorPass123!)")
    print("    * rahul.sharma@example.com (B+, Navrangpura)")
    print("    * amit.shah@example.com    (B+, Vastrapur)")
    print("    * sneha.joshi@example.com  (B+, Satellite)")
    print("---------------------------------------------------------------")


if __name__ == "__main__":
    seed_database()