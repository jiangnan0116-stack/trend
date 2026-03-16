"""Article scraping with newspaper3k."""
from __future__ import annotations

from newspaper import Article
from sqlalchemy import select

from database.db import SessionLocal
from database.models import NewsRaw


def scrape_article(url: str) -> str:
    """Scrape clean article text from a URL."""
    article = Article(url)
    article.download()
    article.parse()
    return article.text


def scrape_pending_articles(limit: int = 50) -> int:
    """Scrape content for news entries that don't have content yet."""
    db = SessionLocal()
    processed = 0
    try:
        pending = db.execute(select(NewsRaw).where(NewsRaw.content.is_(None)).limit(limit)).scalars().all()
        for news in pending:
            try:
                news.content = scrape_article(news.url)
                processed += 1
            except Exception:
                news.content = news.content or ""
        db.commit()
    finally:
        db.close()
    return processed
