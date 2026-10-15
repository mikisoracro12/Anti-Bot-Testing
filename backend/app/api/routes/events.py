"""Request event history API with pagination and filtering."""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EventListResponse, RequestEventOut
from app.services.event_logger import event_to_dict, query_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    outcome: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    detection_reason: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    sort_by: Literal["timestamp", "risk_score", "outcome"] = "timestamp",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
) -> EventListResponse:
    """List sanitized request events with filters and pagination."""
    items, total, pages = query_events(
        db,
        page=page,
        page_size=page_size,
        outcome=outcome,
        classification=classification,
        detection_reason=detection_reason,
        start_time=start_time,
        end_time=end_time,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return EventListResponse(
        items=[RequestEventOut(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{event_id}", response_model=RequestEventOut)
def get_event(event_id: str, db: Session = Depends(get_db)) -> RequestEventOut:
    from app.models.event import RequestEvent

    event = db.get(RequestEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return RequestEventOut(**event_to_dict(event))
