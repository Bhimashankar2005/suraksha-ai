from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.schemas.health import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="operational" if db_status == "healthy" else "degraded",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
        services={
            "database_engine": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
            "storage_vault": "active",
            "ollama_integration": "enabled"
        }
    )

