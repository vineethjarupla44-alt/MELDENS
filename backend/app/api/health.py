from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.health import HealthResponse
from app.db.session import get_db
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint returning system status, database connectivity,
    and MedLens core capabilities.
    """
    db_status = "connected"
    try:
        # Check database connectivity with a lightweight ping
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service=settings.PROJECT_NAME,
        version="1.0.0-phase1",
        environment=settings.ENVIRONMENT,
        database=db_status
    )
