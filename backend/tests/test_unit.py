import sys
from pathlib import Path

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
