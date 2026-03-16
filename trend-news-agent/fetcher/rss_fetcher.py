"""RSS fetcher module for pulling raw news into storage."""
from __future__ import annotations

from datetime import datetime

import feedparser

from app.config import settings
from database.db import SessionLocal
from database.models import NewsRaw
from dedup.dedup_service import is_duplicate, title_hash


def _to_datetime(struct_time) -> datetime | None:
    if not struct_time:
        return None
    return datetime(*struct_time[:6])


def fetch_rss_news() -> int:
    """Fetch and store RSS entries while preventing duplicates."""
    inserted = 0
    db = SessionLocal()
    try:
        for source_name, feed_url in settings.RSS_SOURCES.items():
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                if not title or not url:
                    continue

                h = title_hash(title)
                if is_duplicate(db, url, h):
                    continue

                news = NewsRaw(
                    title=title,
                    url=url,
                    source=source_name,
                    published_at=_to_datetime(entry.get("published_parsed") or entry.get("updated_parsed")),
                    summary=entry.get("summary", ""),
                    title_hash=h,
                )
                db.add(news)
                inserted += 1

        db.commit()
    finally:
        db.close()
    return inserted
