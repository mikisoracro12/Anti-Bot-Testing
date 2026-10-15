"""Persist sanitized request events."""

from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.event import RequestEvent
from app.schemas.event import RequestEventCreate


def log_event(db: Session, payload: RequestEventCreate) -> RequestEvent:
    event = RequestEvent(
        endpoint=payload.endpoint,
        http_method=payload.http_method,
        outcome=payload.outcome,
        risk_score=payload.risk_score,
        classification=payload.classification,
        detection_reasons=json.dumps(
            [r.model_dump() if hasattr(r, "model_dump") else r for r in payload.detection_reasons]
        ),
        rate_limited=payload.rate_limited,
        captcha_status=payload.captcha_status,
        client_id=payload.client_id,
        user_agent_hash=payload.user_agent_hash,
        status_code=payload.status_code,
        path=payload.path,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def event_to_dict(event: RequestEvent) -> dict[str, Any]:
    try:
        reasons = json.loads(event.detection_reasons or "[]")
    except json.JSONDecodeError:
        reasons = []
    return {
        "id": event.id,
        "timestamp": event.timestamp,
        "endpoint": event.endpoint,
        "http_method": event.http_method,
        "outcome": event.outcome,
        "risk_score": event.risk_score,
        "classification": event.classification,
        "detection_reasons": reasons,
        "rate_limited": event.rate_limited,
        "captcha_status": event.captcha_status,
        "client_id": event.client_id,
        "user_agent_hash": event.user_agent_hash,
        "status_code": event.status_code,
        "path": event.path,
    }


def query_events(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    outcome: Optional[str] = None,
    classification: Optional[str] = None,
    detection_reason: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> tuple[list[dict[str, Any]], int, int]:
    stmt = select(RequestEvent)
    count_stmt = select(func.count()).select_from(RequestEvent)

    if outcome:
        stmt = stmt.where(RequestEvent.outcome == outcome)
        count_stmt = count_stmt.where(RequestEvent.outcome == outcome)
    if classification:
        stmt = stmt.where(RequestEvent.classification == classification)
        count_stmt = count_stmt.where(RequestEvent.classification == classification)
    if start_time:
        stmt = stmt.where(RequestEvent.timestamp >= start_time)
        count_stmt = count_stmt.where(RequestEvent.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(RequestEvent.timestamp <= end_time)
        count_stmt = count_stmt.where(RequestEvent.timestamp <= end_time)
    if detection_reason:
        like = f'%"{detection_reason}"%'
        stmt = stmt.where(RequestEvent.detection_reasons.like(like))
        count_stmt = count_stmt.where(RequestEvent.detection_reasons.like(like))

    total = db.scalar(count_stmt) or 0
    pages = max(1, math.ceil(total / page_size)) if total else 0

    sort_column = {
        "timestamp": RequestEvent.timestamp,
        "risk_score": RequestEvent.risk_score,
        "outcome": RequestEvent.outcome,
    }.get(sort_by, RequestEvent.timestamp)
    order_fn = desc if sort_order == "desc" else asc
    stmt = stmt.order_by(order_fn(sort_column)).offset((page - 1) * page_size).limit(page_size)

    rows = db.scalars(stmt).all()
    return [event_to_dict(r) for r in rows], total, pages
