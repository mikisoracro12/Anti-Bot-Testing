"""Dashboard metrics computed from persisted request events."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import RequestEvent
from app.services.event_logger import event_to_dict


def _parse_reasons(raw: str) -> list[dict]:
    try:
        data = json.loads(raw or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def get_dashboard_metrics(
    db: Session,
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    bucket_minutes: int = 5,
) -> dict[str, Any]:
    stmt = select(RequestEvent)
    if start_time:
        stmt = stmt.where(RequestEvent.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(RequestEvent.timestamp <= end_time)

    events = list(db.scalars(stmt.order_by(RequestEvent.timestamp.asc())).all())

    total = len(events)
    allowed = sum(1 for e in events if e.outcome == "allowed")
    rate_limited = sum(1 for e in events if e.rate_limited or e.outcome == "rate_limited")
    captcha_failures = sum(
        1 for e in events if e.outcome == "captcha_failed" or e.captcha_status == "failed"
    )
    blocked = sum(
        1
        for e in events
        if e.outcome in ("blocked", "rate_limited", "captcha_failed")
    )
    suspected = sum(
        1 for e in events if e.classification in ("suspicious", "high_risk")
    )

    # Activity time series
    if not start_time and events:
        start_time = events[0].timestamp
    if not end_time:
        end_time = datetime.now(timezone.utc)
    if start_time and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    buckets: dict[datetime, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "allowed": 0, "blocked": 0, "rate_limited": 0, "suspected": 0}
    )
    bucket_delta = timedelta(minutes=max(1, bucket_minutes))

    for event in events:
        ts = event.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if start_time:
            offset = ts - start_time
            bucket_index = int(offset.total_seconds() // bucket_delta.total_seconds())
            bucket_ts = start_time + bucket_index * bucket_delta
        else:
            bucket_ts = ts.replace(second=0, microsecond=0)

        b = buckets[bucket_ts]
        b["total"] += 1
        if event.outcome == "allowed":
            b["allowed"] += 1
        if event.outcome in ("blocked", "rate_limited", "captcha_failed"):
            b["blocked"] += 1
        if event.rate_limited or event.outcome == "rate_limited":
            b["rate_limited"] += 1
        if event.classification in ("suspicious", "high_risk"):
            b["suspected"] += 1

    activity = [
        {"timestamp": ts, **counts}
        for ts, counts in sorted(buckets.items(), key=lambda x: x[0])
    ]

    reason_counter: Counter[str] = Counter()
    for event in events:
        for reason in _parse_reasons(event.detection_reasons):
            rule = reason.get("rule") if isinstance(reason, dict) else None
            if rule:
                reason_counter[rule] += 1

    detection_reasons = [
        {"reason": name, "count": count}
        for name, count in reason_counter.most_common(20)
    ]

    recent = [
        event_to_dict(e)
        for e in sorted(events, key=lambda x: x.timestamp, reverse=True)[:10]
    ]

    return {
        "summary": {
            "total_requests": total,
            "allowed_requests": allowed,
            "blocked_requests": blocked,
            "suspected_bot_requests": suspected,
            "rate_limit_violations": rate_limited,
            "captcha_failures": captcha_failures,
        },
        "activity": activity,
        "detection_reasons": detection_reasons,
        "recent_events": recent,
    }


def count_events(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(RequestEvent)) or 0
