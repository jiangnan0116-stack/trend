"""Trends API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Trend

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("")
def get_trends(db: Session = Depends(get_db)):
    trends = db.execute(select(Trend).order_by(desc(Trend.last_update))).scalars().all()
    return [
        {
            "id": t.id,
            "category": t.category,
            "trend_score": t.trend_score,
            "trend_heat": t.trend_heat,
            "momentum": t.momentum,
            "event_count": t.event_count,
            "start_date": t.start_date,
            "last_update": t.last_update,
        }
        for t in trends
    ]
