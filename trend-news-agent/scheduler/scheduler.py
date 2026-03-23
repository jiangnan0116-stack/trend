"""APScheduler orchestrator for periodic pipeline runs."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from fetcher.rss_fetcher import fetch_rss_news
from llm.event_extractor import extract_events_from_news
from scraper.article_scraper import scrape_pending_articles
from trends.heat_engine import update_event_heats, update_trends

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def fetch_news_every_hour() -> None:
    count = fetch_rss_news()
    logger.info("Fetched %s new RSS records", count)


def scrape_articles() -> None:
    count = scrape_pending_articles(limit=200)
    logger.info("Scraped %s articles", count)


def extract_events() -> None:
    count = extract_events_from_news(limit=200)
    logger.info("Extracted %s event candidates", count)


def run_update_event_heat() -> None:
    count = update_event_heats()
    logger.info("Updated %s event heat rows", count)


def run_update_trends() -> None:
    count = update_trends()
    logger.info("Updated %s trend rows", count)


def setup_scheduler() -> None:
    """Register all jobs with a 60-minute interval."""
    scheduler.add_job(fetch_news_every_hour, "interval", minutes=60, id="fetch_news", replace_existing=True)
    scheduler.add_job(scrape_articles, "interval", minutes=60, id="scrape_articles", replace_existing=True)
    scheduler.add_job(extract_events, "interval", minutes=60, id="extract_events", replace_existing=True)
    scheduler.add_job(run_update_event_heat, "interval", minutes=60, id="update_event_heat", replace_existing=True)
    scheduler.add_job(run_update_trends, "interval", minutes=60, id="update_trends", replace_existing=True)
    scheduler.start()
