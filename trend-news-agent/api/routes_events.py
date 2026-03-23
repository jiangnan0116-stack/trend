"""Events API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Event

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def get_events(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    events = db.execute(select(Event).order_by(desc(Event.first_seen)).limit(limit)).scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "summary": e.summary,
            "category": e.category,
            "impact_score": e.impact_score,
            "confidence": e.confidence,
            "first_seen": e.first_seen,
            "source_count": e.source_count,
            "event_heat": e.event_heat,
        }
        for e in events
    ]
