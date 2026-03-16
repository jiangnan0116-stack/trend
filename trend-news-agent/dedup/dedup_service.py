"""Deduplication helpers for incoming RSS records."""
from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import NewsRaw


def title_hash(title: str) -> str:
    """Generate deterministic SHA256 hash for title deduplication."""
    normalized = " ".join(title.lower().strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def is_duplicate(db: Session, url: str, hash_value: str) -> bool:
    """Check duplicate news by URL or title hash."""
    stmt = select(NewsRaw.id).where((NewsRaw.url == url) | (NewsRaw.title_hash == hash_value)).limit(1)
    return db.execute(stmt).scalar_one_or_none() is not None
