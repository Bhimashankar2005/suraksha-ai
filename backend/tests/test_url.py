import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.scans import UrlScan
from backend.app.models.reports import Report
from backend.app.core.ssrf_guard import validate_url_and_check_ssrf
from backend.app.ml.url_analyzer import url_scanner
from backend.app.services.url_service import (
    process_url_scan, get_user_url_history, convert_url_scan_to_report
)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_ssrf_protection_loopback():
    """Verify SSRF defense blocks loopback addresses."""
    is_safe, domain, err = validate_url_and_check_ssrf("http://127.0.0.1:8000/admin")
    assert is_safe is False
    assert "SSRF Protection" in err

    is_safe_lh, _, err_lh = validate_url_and_check_ssrf("http://localhost/secret")
    assert is_safe_lh is False
    assert "SSRF Protection" in err_lh

def test_ssrf_protection_private_ip():
    """Verify SSRF defense blocks private RFC 1918 addresses."""
    is_safe_10, _, _ = validate_url_and_check_ssrf("http://10.0.0.5/internal")
    assert is_safe_10 is False

    is_safe_192, _, _ = validate_url_and_check_ssrf("http://192.168.1.100/router")
    assert is_safe_192 is False

def test_ssrf_protection_cloud_metadata():
    """Verify SSRF defense blocks link-local cloud metadata endpoint (169.254.169.254)."""
    is_safe, _, err = validate_url_and_check_ssrf("http://169.254.169.254/latest/meta-data/")
    assert is_safe is False
    assert "SSRF Protection" in err

    # Full analyzer should assign 100 risk score
    res = url_scanner.analyze_url("http://169.254.169.254/latest/meta-data")
    assert res.risk_score == 100
    assert res.risk_level == "CRITICAL"

def test_domain_lookalike_bank_impersonation():
    """Verify domain lookalikes targeting banks are detected and flagged."""
    res = url_scanner.analyze_url("http://onlinesbi-pan-kyc.xyz/login.html")
    assert res.risk_score >= 70
    assert res.risk_level in ["HIGH", "CRITICAL"]
    assert res.lookalike_target is not None
    assert "State Bank of India" in res.lookalike_target
    assert any(ind["rule"] == "HOMOGLYPH_LOOKALIKE_DOMAIN" for ind in res.matched_indicators)

def test_raw_ip_phishing_url():
    """Verify raw public IP addresses are flagged as suspicious."""
    res = url_scanner.analyze_url("http://185.199.110.153/update-pan")
    assert res.is_ip_host is True
    assert res.risk_score >= 50
    assert any(ind["rule"] == "RAW_IP_HOST" for ind in res.matched_indicators)

def test_dangerous_tld_and_phishing_keywords():
    """Verify disposable TLDs and credential keywords add penalty points."""
    res = url_scanner.analyze_url("http://secure-account-verification.top/kyc")
    assert res.risk_score >= 50
    assert any(ind["rule"] == "HIGH_RISK_TLD" for ind in res.matched_indicators)

def test_shortened_url_detection():
    """Verify URL shorteners are flagged with appropriate masking caution."""
    res = url_scanner.analyze_url("https://bit.ly/bank-offer-update")
    assert res.is_shortened is True
    assert any(ind["rule"] == "SHORTENED_URL_MASK" for ind in res.matched_indicators)

def test_authentic_official_domain():
    """Verify genuine verified portals get 0 LOW risk."""
    res = url_scanner.analyze_url("https://onlinesbi.sbi/portal")
    assert res.risk_score == 0
    assert res.risk_level == "LOW"
    assert res.lookalike_target is None

    res_gov = url_scanner.analyze_url("https://cybercrime.gov.in/")
    assert res_gov.risk_score == 0
    assert res_gov.risk_level == "LOW"

def test_process_url_scan_persistence(db):
    """Verify URL scan is stored in the database."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    uid = user.id if user else None

    test_url = "http://hdfc-netbanking-verify.xyz/login"
    res = process_url_scan(raw_url=test_url, user_id=uid, db=db)

    assert res.id is not None
    assert res.domain == "hdfc-netbanking-verify.xyz"
    assert res.risk_score >= 60

    db_scan = db.query(UrlScan).filter(UrlScan.id == res.id).first()
    assert db_scan is not None
    assert db_scan.domain == res.domain

def test_convert_url_scan_to_report(db):
    """Verify URL scan escalates into a community threat report."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    uid = user.id if user else None

    scan = db.query(UrlScan).order_by(UrlScan.created_at.desc()).first()
    assert scan is not None

    rep_res = convert_url_scan_to_report(
        user_id=uid,
        scan_id=scan.id,
        target_value=scan.url,
        custom_description="Phishing site sent via SMS",
        region="Maharashtra",
        db=db
    )
    assert rep_res.report_code.startswith("SUR-REP-")
    assert rep_res.status == "PENDING"

    db_rep = db.query(Report).filter(Report.id == rep_res.report_id).first()
    assert db_rep is not None
    assert db_rep.threat_type == "URL"

