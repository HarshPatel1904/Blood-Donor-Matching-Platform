import json
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

BASE_URL = "http://127.0.0.1:5000/api"
BACKEND_DIR = Path(__file__).resolve().parent.parent


def make_json_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    encoded = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}


def make_raw_request(
    endpoint: str,
    token: Optional[str] = None,
) -> Tuple[int, bytes, Dict[str, str]]:
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def make_multipart_request(
    endpoint: str,
    fields: Dict[str, str],
    file_field: str,
    filename: str,
    file_bytes: bytes,
    content_type_file: str,
    token: str,
) -> Tuple[int, Dict[str, Any]]:
    boundary = f"----RaktSetuBoundary{uuid.uuid4().hex}"
    parts = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
            f"{v}\r\n".encode("utf-8")
        )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type_file}\r\n\r\n"
        ).encode("utf-8")
        + file_bytes
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}


def login(email: str, password: str) -> str:
    status, res = make_json_request("/auth/login", "POST", {"email": email, "password": password})
    assert status == 200, f"Login failed for {email}: {res}"
    return res["data"]["token"]


def run_edge_case_tests():
    print("=================================================================")
    print(" RUNNING PHASE D: SECURITY, RBAC, UPLOAD & EDGE-CASE SUITE       ")
    print("=================================================================\n")

    admin_token = login("admin@bloodplatform.local", "AdminRoot2026!")
    req_a_token = login("priya.patel@example.com", "RequesterPass123!")
    req_b_token = login("arjun.mehta@example.com", "RequesterPass123!")
    donor_rahul_token = login("rahul.sharma@example.com", "DonorPass123!")

    # 1. Authentication & RBAC Enforcement
    print("[1/5] Verifying Authentication & RBAC enforcement...")
    status, _ = make_json_request("/admin/stats")
    assert status == 401, f"Expected 401 without token on /admin/stats, got {status}"

    status, _ = make_json_request("/donors/profile")
    assert status == 401, f"Expected 401 without token on /donors/profile, got {status}"

    status, _ = make_json_request("/admin/stats", token=donor_rahul_token)
    assert status == 403, f"Expected 403 for donor calling /admin/stats, got {status}"

    status, req_created = make_json_request(
        "/requests/individual",
        "POST",
        {
            "blood_group": "B+",
            "units_needed": 1,
            "hospital_name": "Edge Case Hospital",
            "locality": "Navrangpura",
            "urgency": "urgent",
            "required_by_date": "2026-12-10",
        },
        token=req_a_token,
    )
    assert status == 201, f"Failed creating individual request: {req_created}"
    ind_req_id = req_created["data"]["request_id"]

    status, _ = make_json_request(f"/requests/{ind_req_id}/responses", token=req_b_token)
    assert status == 403, f"Expected 403 when Requester B views Requester A responses, got {status}"
    print("   ✓ 401/403 RBAC and cross-requester ownership boundaries enforced.")

    # 2. Two-Tier Request Verification
    print("[2/5] Verifying Two-Tier Request Verification...")
    assert req_created["data"]["verification_status"] == "pending"

    status, disp_before = make_json_request(
        f"/matching/{ind_req_id}/dispatch",
        "POST",
        {"radius": 10},
        token=req_a_token,
    )
    assert status == 400, f"Expected 400 dispatching unapproved request, got {status}: {disp_before}"

    status, approved = make_json_request(
        f"/admin/requests/{ind_req_id}/verify",
        "PATCH",
        {"status": "approved", "notes": "Verified for edge-case suite"},
        token=admin_token,
    )
    assert status == 200 and approved["data"]["verification_status"] == "approved"

    status, disp_after = make_json_request(
        f"/matching/{ind_req_id}/dispatch",
        "POST",
        {"radius": 10},
        token=req_a_token,
    )
    assert status == 200 and disp_after["data"]["notifications_sent"] >= 1, disp_after
    print("   ✓ Unapproved dispatch blocked (400); dispatch succeeded after admin approval.")

    # 3. Donor Availability Filtering
    print("[3/5] Verifying Donor Availability Filtering...")
    status, preview_all = make_json_request(
        f"/matching/{ind_req_id}/preview?radius=20",
        token=req_a_token,
    )
    assert status == 200
    names_before = [d["full_name"] for d in preview_all["data"]["donors"]]
    assert not any("Kavita" in n for n in names_before), f"Unavailable donor Kavita leaked: {names_before}"
    assert any("Rahul" in n for n in names_before), f"Available donor Rahul missing: {names_before}"

    status, _ = make_json_request(
        "/donors/availability",
        "PATCH",
        {"is_available": False},
        token=donor_rahul_token,
    )
    assert status == 200

    status, preview_paused = make_json_request(
        f"/matching/{ind_req_id}/preview?radius=20",
        token=req_a_token,
    )
    assert status == 200
    names_paused = [d["full_name"] for d in preview_paused["data"]["donors"]]
    assert not any("Rahul" in n for n in names_paused), f"Paused donor Rahul still matched: {names_paused}"

    status, _ = make_json_request(
        "/donors/availability",
        "PATCH",
        {"is_available": True},
        token=donor_rahul_token,
    )
    assert status == 200

    status, preview_restored = make_json_request(
        f"/matching/{ind_req_id}/preview?radius=20",
        token=req_a_token,
    )
    assert status == 200
    names_restored = [d["full_name"] for d in preview_restored["data"]["donors"]]
    assert any("Rahul" in n for n in names_restored), f"Restored donor Rahul missing: {names_restored}"
    print("   ✓ Unavailable donor excluded and live availability toggle dynamically updates matches.")

    # 4. Document Upload & Path Traversal Security
    print("[4/5] Verifying Document Upload & Path Traversal Security...")
    sample_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    fields = {
        "blood_group": "O+",
        "units_needed": "1",
        "hospital_name": "Civil Hospital",
        "locality": "Paldi",
        "urgency": "normal",
        "required_by_date": "2026-12-15",
    }
    status, upload_res = make_multipart_request(
        "/requests/individual",
        fields,
        "requisition_doc",
        "edge_test_doc.pdf",
        sample_pdf,
        "application/pdf",
        req_a_token,
    )
    assert status == 201, f"PDF upload failed: {upload_res}"
    doc_url = upload_res["data"]["requisition_doc_url"]
    assert doc_url and doc_url.startswith("uploads/requisitions/")

    saved_file = BACKEND_DIR / doc_url
    assert saved_file.is_file(), f"Uploaded file not found on disk at {saved_file}"

    try:
        doc_filename = Path(doc_url).name
        dl_status, dl_bytes, _ = make_raw_request(
            f"/requests/documents/requisitions/{doc_filename}",
            token=admin_token,
        )
        assert dl_status == 200 and dl_bytes == sample_pdf, f"Download mismatch: {dl_status}"
    finally:
        if saved_file.exists():
            saved_file.unlink()

    status, bad_ext = make_multipart_request(
        "/requests/individual",
        fields,
        "requisition_doc",
        "malware.exe",
        b"MZ\x90\x00",
        "application/octet-stream",
        req_a_token,
    )
    assert status == 400, f"Expected 400 for .exe upload, got {status}: {bad_ext}"

    status, bad_txt = make_multipart_request(
        "/requests/individual",
        fields,
        "requisition_doc",
        "notes.txt",
        b"plain text",
        "text/plain",
        req_a_token,
    )
    assert status == 400, f"Expected 400 for .txt upload, got {status}: {bad_txt}"

    trav_status1, _, _ = make_raw_request("/requests/documents/requisitions/../../.env", token=admin_token)
    trav_status2, _, _ = make_raw_request("/requests/documents/requisitions/..%2F..%2F.env", token=admin_token)
    assert trav_status1 in (400, 404), f"Unexpected traversal status1: {trav_status1}"
    assert trav_status2 in (400, 404), f"Unexpected traversal status2: {trav_status2}"
    print("   ✓ PDF upload/download verified; invalid extensions (.exe/.txt) and path traversal blocked.")

    # 5. Coordinate Privacy Verification
    print("[5/5] Verifying Coordinate Privacy in Donor Responses...")
    status, _ = make_json_request(
        f"/donors/requests/{ind_req_id}/respond",
        "POST",
        {"status": "accepted", "consent_share_contact": True},
        token=donor_rahul_token,
    )
    assert status == 200

    status, resp_res = make_json_request(f"/requests/{ind_req_id}/responses", token=req_a_token)
    assert status == 200 and len(resp_res["data"]) >= 1
    for item in resp_res["data"]:
        assert "latitude" not in item and "longitude" not in item, f"Raw coordinates leaked: {item}"
        assert "donor_locality" in item and "approximate_distance_km" in item
    print("   ✓ Raw donor coordinates absent; only locality and approximate distance returned.")

    print("\n=================================================================")
    print(" ALL PHASE D EDGE-CASE & SECURITY TESTS PASSED!                  ")
    print("=================================================================\n")


if __name__ == "__main__":
    try:
        run_edge_case_tests()
    except AssertionError as err:
        print(f"\n[EDGE-CASE ASSERTION ERROR] {err}")
        sys.exit(1)
    except urllib.error.URLError as err:
        print(f"\n[NETWORK ERROR] Could not connect to {BASE_URL}: {err}")
        sys.exit(1)
