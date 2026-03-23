"""Heat scoring engine for events and trends."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import Event, EventSource, Trend

SOURCE_WEIGHTS: dict[str, float] = {
    "Reuters": 1.0,
    "Bloomberg": 1.0,
    "CNBC": 0.8,
    "TechCrunch": 0.7,
    "VentureBeat": 0.6,
}
DEFAULT_SOURCE_WEIGHT = 0.5


def _source_weight_sum(sources: list[str]) -> float:
    return sum(SOURCE_WEIGHTS.get(source, DEFAULT_SOURCE_WEIGHT) for source in sources)


def _recency_score(first_seen: datetime, now: datetime) -> float:
    age = now - first_seen
    if age < timedelta(hours=24):
        return 1.0
    if age < timedelta(days=3):
        return 0.7
    if age < timedelta(days=7):
        return 0.4
    return 0.1


def _calculate_event_heat(source_weight_sum: float, impact_score: int, recency_score: float) -> float:
    return (source_weight_sum * 0.5) + (float(impact_score) * 0.3) + (recency_score * 0.2)


def update_event_heat(event_id: int, db: Session | None = None, now: datetime | None = None) -> float | None:
    """Update a single event's heat score by event id."""
    owns_session = db is None
    db = db or SessionLocal()
    now = now or datetime.utcnow()

    try:
        event = db.get(Event, event_id)
        if event is None:
            return None

        sources = db.execute(select(EventSource.source).where(EventSource.event_id == event_id)).scalars().all()
        source_weight_sum = _source_weight_sum(sources)
        recency_score = _recency_score(event.first_seen, now)

        event.event_heat = _calculate_event_heat(source_weight_sum, event.impact_score, recency_score)

        if owns_session:
            db.commit()
        return event.event_heat
    finally:
        if owns_session:
            db.close()


def update_event_heats(limit: int | None = None) -> int:
    """Update event heat in batch and skip old unchanged rows."""
    db = SessionLocal()
    updated = 0
    now = datetime.utcnow()
    recalc_cutoff = now - timedelta(days=14)

    try:
        query = select(Event.id).where((Event.event_heat.is_(None)) | (Event.first_seen >= recalc_cutoff))
        query = query.order_by(Event.first_seen.desc())
        if limit:
            query = query.limit(limit)

        event_ids = db.execute(query).scalars().all()

        for event_id in event_ids:
            if update_event_heat(event_id=event_id, db=db, now=now) is not None:
                updated += 1

        db.commit()
    finally:
        db.close()

    return updated


def _fetch_window_stats(db: Session, start: datetime, end: datetime) -> dict[str, dict[str, float]]:
    rows = db.execute(
        select(
            Event.category,
            func.count(Event.id).label("event_count"),
            func.coalesce(func.sum(Event.event_heat), 0.0).label("heat_sum"),
        )
        .where(Event.first_seen >= start, Event.first_seen < end)
        .group_by(Event.category)
    ).all()

    stats: dict[str, dict[str, float]] = {}
    for category, event_count, heat_sum in rows:
        stats[category] = {"event_count": int(event_count), "heat_sum": float(heat_sum or 0.0)}
    return stats


def update_trends() -> int:
    """Compute momentum and trend heat per category."""
    db = SessionLocal()
    now = datetime.utcnow()
    today = date.today()

    current_start = now - timedelta(days=7)
    previous_start = now - timedelta(days=14)

    updated = 0
    try:
        current_stats = _fetch_window_stats(db, current_start, now)
        previous_counts = {
            category: values["event_count"]
            for category, values in _fetch_window_stats(db, previous_start, current_start).items()
        }

        all_categories = set(current_stats.keys()) | set(previous_counts.keys())

        for category in all_categories:
            current_count = int(current_stats.get(category, {}).get("event_count", 0))
            heat_sum = float(current_stats.get(category, {}).get("heat_sum", 0.0))
            previous_count = int(previous_counts.get(category, 0))

            if previous_count == 0:
                momentum = 1.5
            else:
                momentum = current_count / previous_count

            trend_heat = heat_sum * momentum

            trend = db.execute(
                select(Trend).where(Trend.category == category, Trend.start_date == today)
            ).scalar_one_or_none()
            if trend is None:
                trend = Trend(
                    category=category,
                    trend_score=trend_heat,
                    trend_heat=trend_heat,
                    momentum=momentum,
                    event_count=current_count,
                    start_date=today,
                    last_update=now,
                )
                db.add(trend)
            else:
                trend.trend_score = trend_heat
                trend.trend_heat = trend_heat
                trend.momentum = momentum
                trend.event_count = current_count
                trend.last_update = now
            updated += 1

        db.commit()
    finally:
        db.close()

    return updated
