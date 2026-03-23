"""Initialize database schema and seed initial keyword data."""
from __future__ import annotations

from sqlalchemy import inspect, text

from database.db import SessionLocal, engine
from database.models import Base, Keyword

INITIAL_KEYWORDS = [
    {"keyword": "AI chip", "category": "Semiconductor", "weight": 1.4},
    {"keyword": "GPU demand", "category": "Semiconductor", "weight": 1.3},
    {"keyword": "data center expansion", "category": "Cloud", "weight": 1.2},
    {"keyword": "cloud capex", "category": "Cloud", "weight": 1.2},
    {"keyword": "AI infrastructure", "category": "AI", "weight": 1.5},
    {"keyword": "semiconductor equipment", "category": "Semiconductor", "weight": 1.3},
]


def apply_schema_updates() -> None:
    """Add newly introduced columns/indexes for existing deployments."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        event_columns = {col["name"] for col in inspector.get_columns("events")}
        if "event_heat" not in event_columns:
            conn.execute(text("ALTER TABLE events ADD COLUMN event_heat FLOAT NOT NULL DEFAULT 0"))
            conn.execute(text("CREATE INDEX ix_events_event_heat ON events (event_heat)"))

        trend_columns = {col["name"] for col in inspector.get_columns("trends")}
        if "trend_heat" not in trend_columns:
            conn.execute(text("ALTER TABLE trends ADD COLUMN trend_heat FLOAT NOT NULL DEFAULT 0"))
        if "momentum" not in trend_columns:
            conn.execute(text("ALTER TABLE trends ADD COLUMN momentum FLOAT NOT NULL DEFAULT 1"))

        event_source_columns = {col["name"] for col in inspector.get_columns("event_sources")}
        event_source_indexes = {idx["name"] for idx in inspector.get_indexes("event_sources")}
        if "event_id" in event_source_columns and "ix_event_sources_event_id" not in event_source_indexes:
            conn.execute(text("CREATE INDEX ix_event_sources_event_id ON event_sources (event_id)"))
        if "news_id" in event_source_columns and "ix_event_sources_news_id" not in event_source_indexes:
            conn.execute(text("CREATE INDEX ix_event_sources_news_id ON event_sources (news_id)"))


def main() -> None:
    Base.metadata.create_all(bind=engine)
    apply_schema_updates()

    db = SessionLocal()
    try:
        for item in INITIAL_KEYWORDS:
            exists = db.query(Keyword).filter(Keyword.keyword == item["keyword"]).first()
            if exists:
                continue
            db.add(Keyword(**item, status="active"))
        db.commit()
    finally:
        db.close()

    print("Database initialized and seed keywords inserted.")


if __name__ == "__main__":
    main()
