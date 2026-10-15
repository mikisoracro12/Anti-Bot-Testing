"""Request event ORM model — stores sanitized request telemetry."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class RequestEvent(Base):
    """A single observed request event for analytics and auditing.

    Intentionally omits passwords, tokens, cookies, and auth headers.
    """

    __tablename__ = "request_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True, nullable=False
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # outcome values: allowed | blocked | rate_limited | captcha_failed | captcha_required
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    classification: Mapped[str] = mapped_column(
        String(32), default="normal", nullable=False, index=True
    )
    # classification: normal | suspicious | high_risk
    detection_reasons: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    rate_limited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    captcha_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # captcha_status: not_required | passed | failed | missing | error | None
    client_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False, default="/")
