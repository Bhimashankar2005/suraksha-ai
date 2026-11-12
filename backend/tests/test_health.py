import pytest
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine
from backend.app.api.endpoints.health import check_health
from backend.app.main import root
from backend.app.models import Role, ModelRegistry, Course

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_root_endpoint():
    """Verify root API returns correct metadata and routes."""
    data = root()
    assert data["platform"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert data["status"] == "online"
    assert "api_documentation" in data
    assert "health_check" in data

def test_health_check_endpoint(db_session):
    """Verify health endpoint successfully connects to the database and reports operational status."""
    health_data = check_health(db=db_session)
    assert health_data.status in ["operational", "healthy"]
    assert health_data.app_name == settings.PROJECT_NAME
    assert health_data.version == settings.VERSION
    assert health_data.database == "healthy"
    assert health_data.services["database_engine"] in ["sqlite", "postgresql"]
    assert health_data.services["storage_vault"] == "active"

def test_database_connectivity(db_session):
    """Verify database execute and basic connectivity."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

def test_seeded_roles(db_session):
    """Verify that default RBAC roles exist in the database."""
    roles = db_session.query(Role).all()
    role_names = [r.name for r in roles]
    assert "USER" in role_names
    assert "ADMIN" in role_names
    assert "COMMUNITY_MODERATOR" in role_names

def test_seeded_models(db_session):
    """Verify that default model registries exist in the database."""
    models = db_session.query(ModelRegistry).all()
    model_names = [m.model_name for m in models]
    assert "SURAKSHA_HEURISTIC_ENGINE" in model_names
    assert "SURAKSHA_SCAM_TFIDF_CLASSIFIER" in model_names

def test_seeded_courses(db_session):
    """Verify that foundation awareness courses exist in the database."""
    courses = db_session.query(Course).all()
    assert len(courses) >= 3
    slugs = [c.slug for c in courses]
    assert "upi-digital-payment-safety" in slugs
