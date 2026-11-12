import pytest
from backend.app.core.database import SessionLocal
from backend.app.core.security import verify_password, decode_access_token
from backend.app.models.user import User, Role
from backend.app.schemas.auth import UserRegisterRequest, UserLoginRequest
from backend.app.api.endpoints.auth import register_user, login_user
from backend.app.api.deps import require_admin
from fastapi import HTTPException, Response

class DummyRequest:
    def __init__(self, host="127.0.0.1", ua="pytest-agent"):
        self.client = type("Client", (), {"host": host})()
        self.headers = {"user-agent": ua}

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_user_registration_creates_user_role_only(db):
    """Ensure public registration assigns role USER strictly and hashes password with Argon2."""
    test_email = "citizen.test@suraksha.gov.in"
    # Clean up if existed
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    req = UserRegisterRequest(
        email=test_email,
        password="SecureCitizenPassword2026!",
        full_name="Rajesh Kumar",
        phone_number="9876543210",
        preferred_language="kn"
    )
    dummy_req = DummyRequest()
    dummy_res = Response()

    res = register_user(payload=req, response=dummy_res, request=dummy_req, db=db)
    assert res.access_token is not None
    assert res.user.email == test_email
    assert res.user.role == "USER"
    assert res.user.preferred_language == "kn"

    # Verify directly in DB
    created = db.query(User).filter(User.email == test_email).first()
    assert created is not None
    assert created.role.name == "USER"
    assert verify_password("SecureCitizenPassword2026!", created.password_hash) is True
    assert created.profile.full_name == "Rajesh Kumar"

def test_duplicate_registration_rejected(db):
    """Ensure duplicate email registration raises 400."""
    req = UserRegisterRequest(
        email="citizen.test@suraksha.gov.in",
        password="AnotherPassword123!",
        full_name="Duplicate User",
        preferred_language="en"
    )
    dummy_req = DummyRequest()
    dummy_res = Response()

    with pytest.raises(HTTPException) as exc_info:
        register_user(payload=req, response=dummy_res, request=dummy_req, db=db)
    assert exc_info.value.status_code == 400

def test_user_login_valid_credentials(db):
    """Ensure login succeeds with valid credentials."""
    login_req = UserLoginRequest(
        email="citizen.test@suraksha.gov.in",
        password="SecureCitizenPassword2026!"
    )
    dummy_req = DummyRequest()
    dummy_res = Response()

    res = login_user(payload=login_req, response=dummy_res, request=dummy_req, db=db)
    assert res.access_token is not None
    assert res.user.email == "citizen.test@suraksha.gov.in"
    assert res.user.role == "USER"

    payload = decode_access_token(res.access_token)
    assert payload["sub"] == res.user.id
    assert payload["role"] == "USER"

def test_user_login_invalid_password(db):
    """Ensure login fails with wrong password (401)."""
    login_req = UserLoginRequest(
        email="citizen.test@suraksha.gov.in",
        password="WrongPassword123!"
    )
    dummy_req = DummyRequest()
    dummy_res = Response()

    with pytest.raises(HTTPException) as exc_info:
        login_user(payload=login_req, response=dummy_res, request=dummy_req, db=db)
    assert exc_info.value.status_code == 401

def test_admin_rbac_enforcement(db):
    """Ensure normal user cannot pass require_admin dependency."""
    citizen = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    assert citizen.role.name == "USER"

    with pytest.raises(HTTPException) as exc_info:
        require_admin(citizen)
    assert exc_info.value.status_code == 403

def test_admin_rbac_success(db):
    """Ensure admin user passes require_admin dependency."""
    admin = db.query(User).filter(User.email == "admin@suraksha.gov.in").first()
    assert admin is not None
    assert admin.role.name == "ADMIN"

    authorized = require_admin(admin)
    assert authorized.id == admin.id

