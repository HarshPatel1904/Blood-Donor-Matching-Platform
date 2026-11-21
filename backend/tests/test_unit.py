import io
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.utils.haversine import calculate_haversine_distance, is_within_radius
from app.utils.jwt_util import generate_jwt_token, decode_jwt_token


def test_haversine_identical_coordinates():
    navrangpura = (23.0365, 72.5611)
    assert calculate_haversine_distance(navrangpura, navrangpura) == 0.0


def test_haversine_ahmedabad_localities():
    navrangpura = (23.0365, 72.5611)
    vastrapur = (23.0396, 72.5293)
    bopal = (23.0338, 72.4634)

    dist_vastrapur = calculate_haversine_distance(navrangpura, vastrapur)
    dist_bopal = calculate_haversine_distance(navrangpura, bopal)

    assert 3.0 <= dist_vastrapur <= 4.0
    assert 9.0 <= dist_bopal <= 11.0
    assert dist_vastrapur < dist_bopal


def test_is_within_radius_filtering():
    navrangpura = (23.0365, 72.5611)
    satellite = (23.0262, 72.5210)
    chandkheda = (23.1095, 72.5877)

    match_close, dist_close = is_within_radius(navrangpura, satellite, radius_km=10.0)
    match_tight, _ = is_within_radius(navrangpura, chandkheda, radius_km=5.0)

    assert match_close is True
    assert dist_close <= 10.0
    assert match_tight is False


def test_password_hashing_and_verification():
    raw = "DonorPass123!"
    hashed = generate_password_hash(raw)

    assert hashed != raw
    assert check_password_hash(hashed, raw) is True
    assert check_password_hash(hashed, "WrongPassword") is False


def test_jwt_roundtrip_claims():
    token = generate_jwt_token("user-123", "donor@example.com", "donor", expires_in_hours=1)
    decoded = decode_jwt_token(token)

    assert decoded is not None
    assert decoded["sub"] == "user-123"
    assert decoded["email"] == "donor@example.com"
    assert decoded["role"] == "donor"
    assert decode_jwt_token("invalid.token.value") is None


def test_dynamodb_decimal_conversion_and_privacy_masking():
    from app.repositories.dynamodb_repository import (
        DynamoDBRepository,
        _from_dynamo,
        _to_dynamo,
    )

    converted = _to_dynamo({"latitude": 23.0365, "is_available": True, "units": 2})
    assert isinstance(converted["latitude"], Decimal)
    assert converted["is_available"] is True

    restored = _from_dynamo(converted)
    assert restored["latitude"] == 23.0365
    assert isinstance(restored["units"], int)

    # In-memory table stub for DynamoDBRepository
    tables = {name: {} for name in (
        "blood_platform_users",
        "blood_platform_donors",
        "blood_platform_hospitals",
        "blood_platform_blood_requests",
        "blood_platform_donor_responses",
        "blood_platform_notifications",
        "blood_platform_audit_logs",
    )}
    pk_map = {
        "blood_platform_users": "user_id",
        "blood_platform_donors": "donor_id",
        "blood_platform_hospitals": "hospital_id",
        "blood_platform_blood_requests": "request_id",
        "blood_platform_donor_responses": "response_id",
        "blood_platform_notifications": "notification_id",
        "blood_platform_audit_logs": "log_id",
    }

    def eval_expr(expr, item):
        if expr is None:
            return True
        from boto3.dynamodb.conditions import Equals, And
        if isinstance(expr, Equals):
            attr, val = expr._values
            return item.get(attr.name) == val
        if isinstance(expr, And):
            return all(eval_expr(child, item) for child in expr._values)
        return True

    def make_table(tname):
        store = tables[tname]
        pk = pk_map[tname]
        tbl = MagicMock()
        tbl.put_item.side_effect = lambda Item: store.__setitem__(Item[pk], Item)
        tbl.get_item.side_effect = lambda Key: (
            {"Item": store[Key[pk]]} if Key[pk] in store else {}
        )
        tbl.scan.side_effect = lambda **kw: {
            "Items": [
                item
                for item in store.values()
                if eval_expr(kw.get("FilterExpression"), item)
            ]
        }
        return tbl

    mock_ddb = SimpleNamespace(Table=make_table)
    repo = DynamoDBRepository(dynamodb_resource=mock_ddb)

    repo.create_user({
        "user_id": "u-d1", "email": "d1@example.com", "password_hash": "x",
        "role": "donor", "phone": "+919999900001", "full_name": "Donor One",
        "is_active": 1, "created_at": "2026-11-21T00:00:00Z", "updated_at": "2026-11-21T00:00:00Z",
    })
    repo.create_user({
        "user_id": "u-d2", "email": "d2@example.com", "password_hash": "x",
        "role": "donor", "phone": "+919999900002", "full_name": "Donor Two",
        "is_active": 1, "created_at": "2026-11-21T00:00:00Z", "updated_at": "2026-11-21T00:00:00Z",
    })
    repo.create_donor({
        "donor_id": "d1", "user_id": "u-d1", "blood_group": "B+", "city": "Ahmedabad",
        "locality": "Navrangpura", "latitude": 23.0365, "longitude": 72.5611,
        "is_available": 1, "consent_share_contact": 1, "email_notifications": 1,
        "created_at": "2026-11-21T00:00:00Z", "updated_at": "2026-11-21T00:00:00Z",
    })
    repo.create_donor({
        "donor_id": "d2", "user_id": "u-d2", "blood_group": "B+", "city": "Ahmedabad",
        "locality": "Vastrapur", "latitude": 23.0396, "longitude": 72.5293,
        "is_available": 1, "consent_share_contact": 0, "email_notifications": 1,
        "created_at": "2026-11-21T00:00:00Z", "updated_at": "2026-11-21T00:00:00Z",
    })
    repo.save_donor_response({
        "response_id": "r1", "request_id": "req-1", "donor_id": "d1",
        "status": "accepted", "contact_revealed": 1, "responded_at": "2026-11-21T01:00:00Z",
    })
    repo.save_donor_response({
        "response_id": "r2", "request_id": "req-1", "donor_id": "d2",
        "status": "accepted", "contact_revealed": 0, "responded_at": "2026-11-21T01:05:00Z",
    })

    responses = repo.list_responses_for_request("req-1")
    assert len(responses) == 2
    by_name = {r["donor_name"]: r for r in responses}
    assert by_name["Donor One"]["donor_phone"] == "+919999900001"
    assert by_name["Donor Two"]["donor_phone"] is None
    assert by_name["Donor Two"]["donor_email"] is None


def test_s3_storage_service_upload_and_stream():
    from app.services.storage_service import S3StorageService

    mock_s3 = MagicMock()
    storage = S3StorageService(s3_client=mock_s3, bucket_name="raktsetu-docs-harsh-2026")

    bad_file = FileStorage(stream=io.BytesIO(b"bad"), filename="malware.exe")
    ok_bad, _, _ = storage.save_file(bad_file, "requisitions")
    assert ok_bad is False

    good_file = FileStorage(
        stream=io.BytesIO(b"%PDF-1.4 sample"),
        filename="req.pdf",
        content_type="application/pdf",
    )
    ok_good, _, key = storage.save_file(good_file, "requisitions")
    assert ok_good is True and key.startswith("requisitions/")
    mock_s3.put_object.assert_called_once()
    put_kwargs = mock_s3.put_object.call_args.kwargs
    assert put_kwargs["Bucket"] == "raktsetu-docs-harsh-2026"
    assert put_kwargs["ServerSideEncryption"] == "AES256"

    mock_s3.get_object.return_value = {
        "Body": io.BytesIO(b"%PDF-1.4 sample"),
        "ContentType": "application/pdf",
    }
    stream, ctype, dl_name = storage.get_file_stream(key)
    assert stream.read() == b"%PDF-1.4 sample"
    assert ctype == "application/pdf"
    assert dl_name.endswith("req.pdf")
    assert storage.get_file_stream("requisitions/../../.env") is None

