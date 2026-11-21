import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple

BASE_URL = "http://127.0.0.1:5000/api"


def make_request(
    endpoint: str,
    method: str = "GET",
    data: Dict[str, Any] = None,
    token: str = None
) -> Tuple[int, Dict[str, Any]]:
    """Helper executing HTTP calls with JSON encoding and token header injection."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}


def run_e2e_test():
    print("=================================================================")
    print(" STARTING 10-STEP E2E INTEGRATION SUITE ON LOCALHOST:5000       ")
    print("=================================================================\n")

    # -------------------------------------------------------------
    # Step 1: Platform Health & Localities Verification
    # -------------------------------------------------------------
    print("[STEP 1] Checking API health and localities...")
    status, res = make_request("/health")
    assert status == 200 and res["database"] == "sqlite", f"Health check failed: {res}"

    status, res = make_request("/localities")
    assert status == 200 and len(res["data"]) >= 10, "Localities data missing or incomplete."
    print("   ✓ Health check OK. 10 Ahmedabad localities verified.")

    # -------------------------------------------------------------
    # Step 2: Admin Logs In & Verifies Pending Hospital
    # -------------------------------------------------------------
    print("\n[STEP 2] Admin authentication & hospital verification...")
    status, res = make_request("/auth/login", "POST", {
        "email": "admin@bloodplatform.local",
        "password": "AdminRoot2026!"
    })
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["data"]["token"]

    # Fetch hospitals pending verification
    status, res = make_request("/admin/hospitals?status=pending", token=admin_token)
    assert status == 200 and len(res["data"]) > 0, "No pending hospitals found in seed data."
    pending_hospital = res["data"][0]
    hosp_id = pending_hospital["hospital_id"]

    # Approve hospital
    status, res = make_request(f"/admin/hospitals/{hosp_id}/verify", "PATCH", {
        "status": "verified",
        "notes": "Verified via Gujarat Council directory"
    }, token=admin_token)
    assert status == 200 and res["data"]["verification_status"] == "verified"
    print(f"   ✓ Verified Hospital: {pending_hospital['hospital_name']}")

    # -------------------------------------------------------------
    # Step 3: Verified Hospital Submits Blood Request (B+, Navrangpura)
    # -------------------------------------------------------------
    print("\n[STEP 3] Verified Hospital submits B+ critical blood request...")
    status, res = make_request("/auth/login", "POST", {
        "email": "contact@apolloahmedabad.local",
        "password": "HospitalPass123!"
    })
    assert status == 200, f"Hospital login failed: {res}"
    hospital_token = res["data"]["token"]

    status, res = make_request("/requests/hospital", "POST", {
        "blood_group": "B+",
        "units_needed": 2,
        "locality": "Navrangpura",
        "urgency": "critical",
        "required_by_date": "2026-11-15"
    }, token=hospital_token)
    assert status == 201, f"Failed to create hospital request: {res}"
    request_id = res["data"]["request_id"]
    assert res["data"]["verification_status"] == "approved", "Verified hospital request should be auto-approved."
    print(f"   ✓ Blood request created and auto-approved. ID: {request_id}")

    # -------------------------------------------------------------
    # Step 4: Proximity Matching Calculation (Haversine within 10 km)
    # -------------------------------------------------------------
    print("\n[STEP 4] Preview matching B+ donors within 10 km radius...")
    status, res = make_request(f"/matching/{request_id}/preview?radius=10", token=hospital_token)
    assert status == 200, f"Match preview failed: {res}"
    matches = res["data"]["donors"]
    assert len(matches) >= 3, f"Expected at least 3 matching B+ donors, got {len(matches)}"

    # Validate distance ordering (nearest first)
    distances = [d["distance_km"] for d in matches]
    assert distances == sorted(distances), f"Donors not sorted by distance: {distances}"
    print(f"   ✓ Found {len(matches)} eligible B+ donors within 10 km:")
    for d in matches:
        print(f"     * {d['full_name']} ({d['locality']}) -> {d['distance_km']} km")

    # -------------------------------------------------------------
    # Step 5: Dispatch Request & Verify Console Notifications
    # -------------------------------------------------------------
    print("\n[STEP 5] Dispatching request to donors...")
    status, res = make_request(f"/matching/{request_id}/dispatch", "POST", {
        "radius": 10.0
    }, token=hospital_token)
    assert status == 200, f"Dispatch failed: {res}"
    assert res["data"]["status"] == "donors_notified"
    assert res["data"]["notifications_sent"] >= 3
    print(f"   ✓ Dispatched. {res['data']['notifications_sent']} notification(s) generated.")

    # -------------------------------------------------------------
    # Step 6: Donor 1 (Rahul Sharma) ACCEPTS with consent_share_contact=False
    # -------------------------------------------------------------
    print("\n[STEP 6] Donor 1 (Rahul Sharma) logs in and ACCEPTS (Contact Hidden)...")
    status, res = make_request("/auth/login", "POST", {
        "email": "rahul.sharma@example.com",
        "password": "DonorPass123!"
    })
    assert status == 200, "Donor 1 login failed."
    d1_token = res["data"]["token"]

    status, res = make_request(f"/donors/requests/{request_id}/respond", "POST", {
        "status": "accepted",
        "consent_share_contact": False
    }, token=d1_token)
    assert status == 200 and res["data"]["contact_revealed"] == 0
    print("   ✓ Donor 1 accepted. Contact consent withheld (anonymity maintained).")

    # -------------------------------------------------------------
    # Step 7: Donor 2 (Amit Shah) DECLINES
    # -------------------------------------------------------------
    print("\n[STEP 7] Donor 2 (Amit Shah) logs in and DECLINES...")
    status, res = make_request("/auth/login", "POST", {
        "email": "amit.shah@example.com",
        "password": "DonorPass123!"
    })
    assert status == 200, "Donor 2 login failed."
    d2_token = res["data"]["token"]

    status, res = make_request(f"/donors/requests/{request_id}/respond", "POST", {
        "status": "declined",
        "consent_share_contact": False
    }, token=d2_token)
    assert status == 200 and res["data"]["status"] == "declined"
    print("   ✓ Donor 2 declined request.")

    # -------------------------------------------------------------
    # Step 8: Donor 3 (Sneha Joshi) ACCEPTS with consent_share_contact=True
    # -------------------------------------------------------------
    print("\n[STEP 8] Donor 3 (Sneha Joshi) logs in and ACCEPTS (Contact Consented)...")
    status, res = make_request("/auth/login", "POST", {
        "email": "sneha.joshi@example.com",
        "password": "DonorPass123!"
    })
    assert status == 200, "Donor 3 login failed."
    d3_token = res["data"]["token"]

    status, res = make_request(f"/donors/requests/{request_id}/respond", "POST", {
        "status": "accepted",
        "consent_share_contact": True
    }, token=d3_token)
    assert status == 200 and res["data"]["contact_revealed"] == 1
    print("   ✓ Donor 3 accepted and granted contact sharing.")

    # -------------------------------------------------------------
    # Step 9: Requester Views Gated Donor Responses & Privacy Masks
    # -------------------------------------------------------------
    print("\n[STEP 9] Requester checks response list & privacy boundaries...")
    status, res = make_request(f"/requests/{request_id}/responses", token=hospital_token)
    assert status == 200, f"Failed to retrieve responses: {res}"
    responses = res["data"]
    assert len(responses) >= 3, "Expected at least 3 donor responses."

    # Verify contact revelation rules:
    # Sneha Joshi (consented): phone and email MUST be visible
    # Rahul Sharma (withheld consent): phone and email MUST be None
    # Amit Shah (declined): phone and email MUST be None
    resp_map = {r["donor_name"]: r for r in responses}

    # Test Sneha Joshi
    sneha = next((v for k, v in resp_map.items() if "Sneha" in k), None)
    assert sneha and sneha["contact_revealed"] is True
    assert sneha["donor_phone"] is not None and len(sneha["donor_phone"]) > 0
    print(f"   ✓ Consenting Donor Revealed: {sneha['donor_name']} -> {sneha['donor_phone']}")

    # Test Rahul Sharma
    rahul = next((v for k, v in resp_map.items() if "Rahul" in k), None)
    assert rahul and rahul["contact_revealed"] is False
    assert rahul["donor_phone"] is None and rahul["donor_email"] is None
    print(f"   ✓ Non-Consenting Donor Masked: {rahul['donor_name']} -> Phone: [MASKED]")

    # Test Amit Shah
    amit = next((v for k, v in resp_map.items() if "Amit" in k), None)
    assert amit and amit["status"] == "declined"
    assert amit["donor_phone"] is None
    print(f"   ✓ Declined Donor Masked: {amit['donor_name']} -> Phone: [MASKED]")

    # -------------------------------------------------------------
    # Step 10: Admin Audits Workflow & Confirms Logs
    # -------------------------------------------------------------
    print("\n[STEP 10] Admin reviews audit trail & marks request fulfilled...")
    status, res = make_request("/admin/audit-logs?limit=10", token=admin_token)
    assert status == 200 and len(res["data"]) >= 4, "Expected audit trail records missing."
    print("   ✓ Verified audit actions recorded:")
    for entry in res["data"][:4]:
        print(f"     * Action: {entry['action']} on {entry['target_entity']} (Time: {entry['created_at'][:19]})")

    # Mark request fulfilled
    status, res = make_request(f"/requests/{request_id}/status", "PATCH", {
        "request_status": "fulfilled"
    }, token=hospital_token)
    assert status == 200
    print(f"   ✓ Blood request {request_id} transitioned to 'fulfilled'.")

    print("\n=================================================================")
    print(" ALL 10 DEMONSTRATION WORKFLOW STEPS PASSED SUCCESSFULLY!       ")
    print(" Local platform is fully functional and ready for faculty demo. ")
    print("=================================================================\n")


if __name__ == "__main__":
    try:
        run_e2e_test()
    except AssertionError as err:
        print(f"\n[E2E ASSERTION ERROR] {err}")
        sys.exit(1)
    except urllib.error.URLError as err:
        print(f"\n[NETWORK ERROR] Could not connect to {BASE_URL}. Ensure Flask server is running on localhost:5000!")
        sys.exit(1)