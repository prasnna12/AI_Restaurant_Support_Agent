"""Health check endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.core.config import settings
from app.rag.pipeline import is_index_available
from app.schemas.schemas import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc), version=settings.APP_VERSION)


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness(db: Session = Depends(get_db)):
    # DB check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # AI provider check
    ai_status = "configured" if settings.is_ai_configured else f"not configured ({settings.AI_PROVIDER})"
    if settings.AI_PROVIDER == "mock":
        ai_status = "mock/fallback mode"

    # RAG index check
    rag_status = "available" if is_index_available() else "not built (use /api/knowledge/reindex)"

    overall = "ready" if db_status == "ok" else "degraded"
    return ReadinessResponse(
        status=overall, database=db_status, ai_provider=ai_status,
        rag_index=rag_status, timestamp=datetime.now(timezone.utc)
    )
