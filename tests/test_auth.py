import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, engine, Base
from app.db import crud
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.auth.routes import COOKIE_NAME

client = TestClient(app)

def test_password_hashing_and_verification():
    """Verify PBKDF2 password hashing and constant-time verification."""
    password = "SecurePassword@2026"
    hashed = hash_password(password)
    assert hashed != password
    assert "$" in hashed
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "invalid_hash_string") is False

def test_jwt_token_encode_decode():
    """Verify RFC 7519 HMAC-SHA256 JWT creation, payload preservation, and validation."""
    payload = {"sub": "user-123", "email": "test@sca.gov.in", "role": "FIELD_OFFICER"}
    token = create_access_token(payload, expires_in=3600)
    assert token is not None
    assert len(token.split('.')) == 3

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-123"
    assert decoded["email"] == "test@sca.gov.in"
    assert decoded["role"] == "FIELD_OFFICER"

    # Test expired token
    expired_token = create_access_token(payload, expires_in=-10)
    assert decode_access_token(expired_token) is None

    # Test tampered token
    tampered = token[:-4] + "xxxx"
    assert decode_access_token(tampered) is None

def test_seed_default_users():
    """Verify default demo accounts are seeded properly in database."""
    db = SessionLocal()
    try:
        crud.seed_default_users(db)
        officer = crud.get_user_by_email(db, "officer.belagavi@sca.gov.in")
        assert officer is not None
        assert officer.role == "FIELD_OFFICER"
        assert officer.district == "Belagavi"
        assert verify_password("Officer@123", officer.hashed_password) is True

        admin = crud.get_user_by_email(db, "admin@sca.gov.in")
        assert admin is not None
        assert admin.role == "ADMIN"
        assert verify_password("Admin@123", admin.hashed_password) is True
    finally:
        db.close()

def test_signup_flow():
    """Test full officer registration endpoint."""
    unique_email = f"officer_{uuid.uuid4().hex[:8]}@sca.gov.in"
    response = client.post("/auth/signup", json={
        "email": unique_email,
        "password": "Password@123",
        "full_name": "Suresh Gowda",
        "role": "FIELD_OFFICER",
        "district": "Mandya",
        "badge_number": "SCA-MDY-01"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["district"] == "Mandya"

    # Ensure cookie was set
    assert COOKIE_NAME in response.cookies

    # Test duplicate signup rejected
    dup_res = client.post("/auth/signup", json={
        "email": unique_email,
        "password": "Password@123",
        "full_name": "Duplicate Person"
    })
    assert dup_res.status_code == 400

def test_login_flow():
    """Test login with valid and invalid credentials."""
    # Invalid password
    res = client.post("/auth/login", json={
        "email": "officer.belagavi@sca.gov.in",
        "password": "WrongPassword999"
    })
    assert res.status_code == 401

    # Valid login
    res = client.post("/auth/login", json={
        "email": "officer.belagavi@sca.gov.in",
        "password": "Officer@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["user"]["role"] == "FIELD_OFFICER"
    assert COOKIE_NAME in res.cookies

def test_me_endpoint_and_logout():
    """Test /auth/me with cookie and logout clearing."""
    # Login first
    login_res = client.post("/auth/login", json={
        "email": "admin@sca.gov.in",
        "password": "Admin@123"
    })
    token = login_res.json()["access_token"]

    # Call /auth/me using Bearer header
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["email"] == "admin@sca.gov.in"
    assert user_info["role"] == "ADMIN"

    # Call /auth/logout
    logout_res = client.post("/auth/logout")
    assert logout_res.status_code == 200

def test_admin_redirect_when_unauthenticated():
    """Test that navigating to /admin without a session cookie redirects to /login."""
    # Clear any cookies
    unauthed_client = TestClient(app)
    response = unauthed_client.get("/admin", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert response.headers["location"] == "/login"

def test_login_page_renders():
    """Test that GET /login serves the registration/login HTML portal."""
    unauthed_client = TestClient(app)
    response = unauthed_client.get("/login")
    assert response.status_code == 200
    assert "State Channelizing Agency" in response.text
    assert "Sign In" in response.text
    assert "Register Officer" in response.text
