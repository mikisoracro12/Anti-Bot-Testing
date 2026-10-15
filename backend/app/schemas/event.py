"""Schemas for request events."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DetectionReason(BaseModel):
    rule: str
    score: float
    explanation: str


class RequestEventCreate(BaseModel):
    endpoint: str
    http_method: str
    outcome: str
    risk_score: float = 0.0
    classification: str = "normal"
    detection_reasons: list[DetectionReason] = Field(default_factory=list)
    rate_limited: bool = False
    captcha_status: str | None = None
    client_id: str
    user_agent_hash: str | None = None
    status_code: int = 200
    path: str = "/"


class RequestEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    endpoint: str
    http_method: str
    outcome: str
    risk_score: float
    classification: str
    detection_reasons: list[Any] = Field(default_factory=list)
    rate_limited: bool
    captcha_status: str | None = None
    client_id: str
    user_agent_hash: str | None = None
    status_code: int
    path: str


class EventListResponse(BaseModel):
    items: list[RequestEventOut]
    total: int
    page: int
    page_size: int
    pages: int


class EventFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    outcome: str | None = None
    classification: str | None = None
    detection_reason: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    sort_by: Literal["timestamp", "risk_score", "outcome"] = "timestamp"
    sort_order: Literal["asc", "desc"] = "desc"
