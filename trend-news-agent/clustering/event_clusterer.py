"""Event clustering based on embedding similarity."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from database.models import Event, EventSource, NewsRaw
from llm.providers import get_llm_client

embedding_client = get_llm_client()


def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for event summary."""
    resp = embedding_client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding


def cosine_similarity(vec1: Sequence[float], vec2: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def upsert_clustered_event(db: Session, event_payload: dict, news: NewsRaw) -> Event:
    """Merge into similar event or create a new event with source mapping."""
    new_embedding = generate_embedding(event_payload["summary"])

    one_day_ago = datetime.utcnow() - timedelta(days=1)
    existing_events = db.execute(
        select(Event).where(Event.first_seen >= one_day_ago)
    ).scalars().all()

    best_match = None
    best_score = 0.0

    for event in existing_events:
        if not event.embedding:
            continue
        old_embedding = json.loads(event.embedding)
        score = cosine_similarity(new_embedding, old_embedding)
        if score > best_score:
            best_score = score
            best_match = event

    if best_match and best_score >= settings.SIMILARITY_THRESHOLD:
        best_match.source_count += 1
        target_event = best_match
    else:
        target_event = Event(
            title=event_payload["event_title"],
            summary=event_payload["summary"],
            category=event_payload["category"],
            impact_score=int(event_payload["impact_score"]),
            confidence=float(event_payload["confidence"]),
            source_count=1,
            embedding=json.dumps(new_embedding),
        )
        db.add(target_event)
        db.flush()

    exists = db.execute(
        select(EventSource).where(EventSource.event_id == target_event.id, EventSource.news_id == news.id)
    ).scalar_one_or_none()
    if not exists:
        db.add(
            EventSource(
                event_id=target_event.id,
                news_id=news.id,
                url=news.url,
                source=news.source,
            )
        )

    return target_event
