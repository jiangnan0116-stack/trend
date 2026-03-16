"""Trend score computation engine."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import select

from database.db import SessionLocal
from database.models import Event, Keyword, Trend

DEFAULT_CATEGORIES = ["AI", "Semiconductor", "Macro", "Cloud", "Energy", "Finance"]


def update_trends() -> int:
    """Aggregate event impact and keyword weights by category into trends table."""
    db = SessionLocal()
    updated = 0
    try:
        keywords = db.execute(select(Keyword).where(Keyword.status == "active")).scalars().all()
        weights = defaultdict(lambda: 1.0)
        for kw in keywords:
            weights[kw.category] = max(weights[kw.category], kw.weight)

        events = db.execute(select(Event)).scalars().all()
        agg = defaultdict(lambda: {"score": 0.0, "count": 0})

        for event in events:
            weight = weights[event.category]
            agg[event.category]["score"] += float(event.impact_score) * weight
            agg[event.category]["count"] += 1

        today = date.today()
        for category in set(DEFAULT_CATEGORIES) | set(agg.keys()):
            info = agg.get(category, {"score": 0.0, "count": 0})
            trend = db.execute(
                select(Trend).where(Trend.category == category, Trend.start_date == today)
            ).scalar_one_or_none()
            if trend is None:
                trend = Trend(
                    category=category,
                    trend_score=info["score"],
                    event_count=info["count"],
                    start_date=today,
                    last_update=datetime.utcnow(),
                )
                db.add(trend)
            else:
                trend.trend_score = info["score"]
                trend.event_count = info["count"]
                trend.last_update = datetime.utcnow()
            updated += 1

        db.commit()
    finally:
        db.close()
    return updated
