import pytest
import os
import secrets
import json
from starlette.responses import Response

from backend.app.core.security_headers import OWASP_SECURITY_HEADERS, apply_security_headers
from backend.app.core.rate_limiter import (
    limiter,
    RATE_LIMIT_RULES,
    EXCLUDED_PREFIXES,
    create_rate_limit_exceeded_response
)
from backend.app.core.sanitizer import sanitize_text, validate_safe_path, check_sqli_anomaly
from backend.app.core.database import SessionLocal
from backend.app.models.reports import Report

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Ensure clean rate limiting state before and after each test."""
    limiter.reset()
    yield
    limiter.reset()

def test_owasp_security_headers_structure():
    """Verify standard OWASP defensive headers are correctly configured."""
    assert OWASP_SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
    assert OWASP_SECURITY_HEADERS["X-Frame-Options"] == "DENY"
    assert OWASP_SECURITY_HEADERS["X-XSS-Protection"] == "1; mode=block"
    assert "max-age=31536000" in OWASP_SECURITY_HEADERS["Strict-Transport-Security"]
    assert OWASP_SECURITY_HEADERS["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in OWASP_SECURITY_HEADERS["Permissions-Policy"]
    assert "frame-ancestors 'none'" in OWASP_SECURITY_HEADERS["Content-Security-Policy"]

def test_owasp_security_headers_application():
    """Verify security headers are properly attached to outgoing HTTP responses."""
    raw_response = Response(content="OK", media_type="text/plain")
    secured_response = apply_security_headers(raw_response)
    
    headers = secured_response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("Permissions-Policy", "")
    assert "frame-ancestors 'none'" in headers.get("Content-Security-Policy", "")

def test_rate_limiter_blocks_brute_force_login():
    """
    Verify in-memory sliding-window rate limiter triggers block
    when requests exceed the 10 req/min threshold on auth/login.
    """
    client_key = "auth_login:198.51.100.25"
    max_req = 10
    window_sec = 60

    # First 10 requests must be allowed
    for i in range(10):
        allowed, retry_after, remaining = limiter.is_allowed(client_key, max_req, window_sec)
        assert allowed is True
        assert remaining == (max_req - (i + 1))
        assert retry_after == 0

    # 11th request must be intercepted
    allowed_11, retry_after_11, remaining_11 = limiter.is_allowed(client_key, max_req, window_sec)
    assert allowed_11 is False
    assert remaining_11 == 0
    assert retry_after_11 > 0

def test_rate_limiter_exceeded_response_structure():
    """Verify HTTP 429 response formatting with Retry-After and statutory helpline notice."""
    resp_429 = create_rate_limit_exceeded_response(retry_after=45, max_requests=10)
    assert resp_429.status_code == 429
    assert resp_429.headers.get("Retry-After") == "45"
    assert resp_429.headers.get("X-RateLimit-Limit") == "10"
    assert resp_429.headers.get("X-RateLimit-Remaining") == "0"

    body = json.loads(resp_429.body.decode("utf-8"))
    assert "Rate limit exceeded" in body["detail"]
    assert body["retry_after_seconds"] == 45
    assert "1930" in body["helpline_notice"]
    assert "cybercrime.gov.in" in body["helpline_notice"]

def test_rate_limiter_rules_and_exclusions():
    """Verify configured rate limit rules and path exclusions."""
    rule_names = [rule[3] for rule in RATE_LIMIT_RULES]
    assert "auth_login" in rule_names
    assert "auth_register" in rule_names
    assert "scam_scan" in rule_names
    assert "url_scan" in rule_names

    assert "/api/v1/health" in EXCLUDED_PREFIXES
    assert "/api/v1/docs" in EXCLUDED_PREFIXES

def test_rate_limiter_reset_mechanism():
    """Verify rate limiter storage can be purged cleanly."""
    key = "auth_login:127.0.0.1"
    # Exhaust limit
    for _ in range(10):
        limiter.is_allowed(key, max_requests=10, window_seconds=60)

    # Confirm blocked
    allowed, retry_after, _ = limiter.is_allowed(key, max_requests=10, window_seconds=60)
    assert allowed is False
    assert retry_after > 0

    # Reset
    limiter.reset()

    # Confirm allowed again
    allowed_again, _, remaining = limiter.is_allowed(key, max_requests=10, window_seconds=60)
    assert allowed_again is True
    assert remaining == 9

def test_path_traversal_validator():
    """Verify path traversal prevention helper."""
    base = os.path.abspath("storage/evidence")
    safe_target = os.path.join(base, "legit_file.dat")
    unsafe_traversal_1 = os.path.join(base, "..", "secret.env")
    unsafe_traversal_2 = os.path.join(base, "..", "..", "Windows", "System32")
    unsafe_traversal_3 = "C:\\Windows\\System32\\cmd.exe"

    assert validate_safe_path(base, safe_target) is True
    assert validate_safe_path(base, unsafe_traversal_1) is False
    assert validate_safe_path(base, unsafe_traversal_2) is False
    assert validate_safe_path(base, unsafe_traversal_3) is False
    assert validate_safe_path("", safe_target) is False

def test_input_sanitizer_removes_null_bytes_and_controls():
    """Verify input sanitizer strips null bytes and dangerous unprintable controls."""
    malicious_input = "Hello\x00World!\x01\x02\x08Secure\tString\nWithNewlines\r"
    cleaned = sanitize_text(malicious_input)
    assert "\x00" not in cleaned
    assert "\x01" not in cleaned
    assert "\x02" not in cleaned
    assert "\x08" not in cleaned
    assert "Hello" in cleaned
    assert "World!" in cleaned
    assert "Secure\tString\nWithNewlines" in cleaned

def test_input_sanitizer_max_length_bound():
    """Verify input sanitizer enforces strict length bound."""
    long_input = "A" * 15000
    cleaned = sanitize_text(long_input, max_length=256)
    assert len(cleaned) == 256

def test_sqli_anomaly_detector():
    """Verify heuristic SQL injection signature audit."""
    assert check_sqli_anomaly("admin' OR '1'='1") is True
    assert check_sqli_anomaly("1; DROP TABLE users;--") is True
    assert check_sqli_anomaly("UNION SELECT username, password FROM users") is True
    assert check_sqli_anomaly("Normal legitimate search query for SBI bank fraud") is False

def test_sqlite_foreign_keys_strictly_enforced():
    """Verify SQLite foreign key pragma rejects orphan relational inserts."""
    from sqlalchemy.exc import IntegrityError
    db = SessionLocal()
    fake_user_id = "non-existent-user-id-" + secrets.token_hex(4)
    orphan_report = Report(
        report_code=f"SUR-REP-ORPHAN-{secrets.randbelow(10000)}",
        user_id=fake_user_id,
        threat_type="URL",
        target_value="http://fake-orphan.xyz",
        description="Testing foreign key constraint"
    )
    db.add(orphan_report)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()
