"""Schemas for demo endpoints, CAPTCHA, and simulation."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class DemoRequestBody(BaseModel):
    """Optional payload for the protected demo endpoint."""

    message: str = Field(default="hello", max_length=500)
    captcha_token: str | None = Field(default=None, max_length=2048)


class DemoResponse(BaseModel):
    status: str
    message: str
    risk_score: float
    classification: str
    detection_reasons: list[dict[str, Any]] = Field(default_factory=list)
    captcha_required: bool = False
    captcha_status: str | None = None
    rate_limited: bool = False
    event_id: str | None = None


class CaptchaVerifyRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=2048)


class CaptchaVerifyResponse(BaseModel):
    success: bool
    provider: str
    error_codes: list[str] = Field(default_factory=list)
    message: str


class SimulationRequest(BaseModel):
    mode: Literal["normal", "burst", "repeat"] = "normal"
    request_count: int = Field(default=10, ge=1, le=100)
    interval_ms: int = Field(default=200, ge=50, le=60000)
    endpoint: Literal["demo", "health"] = "demo"


class SimulationResultItem(BaseModel):
    index: int
    status_code: int
    outcome: str
    risk_score: float | None = None
    error: str | None = None


class SimulationResponse(BaseModel):
    mode: str
    total: int
    successful: int
    rejected: int
    failed: int
    cancelled: bool = False
    results: list[SimulationResultItem] = Field(default_factory=list)
    message: str


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    version: str = "1.0.0"
