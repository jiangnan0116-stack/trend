"""LLM event extraction and persistence pipeline."""
from __future__ import annotations

import json

from sqlalchemy import select

from clustering.event_clusterer import upsert_clustered_event
from database.db import SessionLocal
from database.models import NewsRaw
from llm.providers import get_llm_client, get_llm_model

client = get_llm_client()
model = get_llm_model()

PROMPT = """Extract structured event information from the news article.
Return JSON with fields:
- event_title
- summary
- category
- impact_score (1-5)
- confidence (0-1)
- companies
- keywords
Only return valid JSON."""


def extract_event(title: str, first_paragraph: str) -> dict:
    """Call OpenAI API to extract event structure from article snippet."""
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"Title: {title}\nParagraph: {first_paragraph}"},
        ],
    )
    return json.loads(response.choices[0].message.content)


def extract_events_from_news(limit: int = 50) -> int:
    """Run event extraction for scraped articles and cluster results."""
    db = SessionLocal()
    processed = 0
    try:
        rows = db.execute(
            select(NewsRaw)
            .where(NewsRaw.content.is_not(None), NewsRaw.content != "")
            .where(~NewsRaw.id.in_(select_news_with_event_sources()))
            .limit(limit)
        ).scalars().all()

        for news in rows:
            first_paragraph = news.content.split("\n", 1)[0][:1200]
            try:
                payload = extract_event(news.title, first_paragraph)
                upsert_clustered_event(db, payload, news)
                processed += 1
            except Exception:
                continue

        db.commit()
    finally:
        db.close()
    return processed


def select_news_with_event_sources():
    """Subquery selecting news IDs already mapped to any event source."""
    from sqlalchemy import select
    from database.models import EventSource

    return select(EventSource.news_id)
