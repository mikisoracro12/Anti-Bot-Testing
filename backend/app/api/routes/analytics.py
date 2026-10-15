"""Dashboard metrics and non-sensitive configuration endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.analytics import (
    CaptchaStatusOut,
    DashboardMetrics,
    DetectionConfigOut,
    RateLimitConfigOut,
)
from app.services.analytics import get_dashboard_metrics
from app.services.captcha import get_captcha_service

router = APIRouter(tags=["analytics"])


@router.get("/analytics/dashboard", response_model=DashboardMetrics)
def dashboard_metrics(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    bucket_minutes: int = Query(5, ge=1, le=60),
    db: Session = Depends(get_db),
) -> DashboardMetrics:
    """Return live dashboard metrics from persisted events."""
    data = get_dashboard_metrics(
        db, start_time=start_time, end_time=end_time, bucket_minutes=bucket_minutes
    )
    return DashboardMetrics(**data)


@router.get("/config/detection", response_model=DetectionConfigOut)
def detection_config(settings: Settings = Depends(get_settings)) -> DetectionConfigOut:
    """Expose non-sensitive detection and rate-limit configuration."""
    return DetectionConfigOut(
        window_seconds=settings.detection_window_seconds,
        frequency_threshold=settings.detection_frequency_threshold,
        repeat_endpoint_threshold=settings.detection_repeat_endpoint_threshold,
        suspicious_score_threshold=settings.detection_suspicious_score_threshold,
        high_risk_score_threshold=settings.detection_high_risk_score_threshold,
        captcha_trigger_score=settings.detection_captcha_trigger_score,
        rate_limit_enabled=settings.rate_limit_enabled,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
        rate_limit_storage=settings.rate_limit_storage,
        captcha_enabled=settings.captcha_enabled,
        captcha_provider=settings.captcha_provider,
        turnstile_site_key=settings.turnstile_site_key or None,
        trust_forwarded_headers=settings.trust_forwarded_headers,
        notes=[
            "User-Agent signals alone do not reliably identify bots.",
            "Weak signals never auto-ban legitimate users in this demo.",
            "IP-based identity is unreliable behind proxies; forwarded headers "
            "are only trusted when TRUST_FORWARDED_HEADERS is enabled and the "
            "peer is in TRUSTED_PROXY_IPS.",
            "This demonstration is not production-ready without a security review.",
        ],
    )


@router.get("/config/rate-limits", response_model=RateLimitConfigOut)
def rate_limit_config(settings: Settings = Depends(get_settings)) -> RateLimitConfigOut:
    limitations = [
        "In-memory storage does not share counters across workers or processes.",
        "SQLite stores event history, not rate-limit counters.",
        "Use RATE_LIMIT_STORAGE=redis with REDIS_URL for multi-worker deployments.",
    ]
    return RateLimitConfigOut(
        enabled=settings.rate_limit_enabled,
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
        storage=settings.rate_limit_storage,
        redis_configured=bool(settings.redis_url),
        limitations=limitations,
    )


@router.get("/config/captcha", response_model=CaptchaStatusOut)
def captcha_config() -> CaptchaStatusOut:
    """CAPTCHA status without exposing the secret key."""
    return CaptchaStatusOut(**get_captcha_service().status_payload())
