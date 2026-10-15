"""Health check endpoints."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.demo import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness/readiness probe — no secrets exposed."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
    )
