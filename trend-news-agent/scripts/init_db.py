"""Initialize PostgreSQL schema and seed initial keyword data."""
from __future__ import annotations

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


def main() -> None:
    Base.metadata.create_all(bind=engine)

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
