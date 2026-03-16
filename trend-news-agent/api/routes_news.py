"""News API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import NewsRaw

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
def get_news(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    rows = db.execute(select(NewsRaw).order_by(desc(NewsRaw.published_at), desc(NewsRaw.created_at)).limit(limit)).scalars()
    return [
        {
            "id": n.id,
            "title": n.title,
            "url": n.url,
            "source": n.source,
            "published_at": n.published_at,
            "summary": n.summary,
        }
        for n in rows
    ]
