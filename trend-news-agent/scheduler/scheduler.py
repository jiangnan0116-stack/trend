"""APScheduler orchestrator for periodic pipeline runs."""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from fetcher.rss_fetcher import fetch_rss_news
from llm.event_extractor import extract_events_from_news
from scraper.article_scraper import scrape_pending_articles
from trends.trend_engine import update_trends

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

FALLBACK_INTERVAL_MINUTES = 60


def fetch_news_every_hour() -> int:
    """抓取 RSS 源中的最新新闻并记录新增数量。"""
    count = fetch_rss_news()
    logger.info("Fetched %s new RSS records", count)
    return count


def scrape_articles() -> int:
    """补全文章正文内容，优先处理尚未抓取正文的新闻。"""
    count = scrape_pending_articles(limit=200)
    logger.info("Scraped %s articles", count)
    return count


def extract_events() -> int:
    """调用 LLM 从新闻正文中提取结构化事件候选。"""
    count = extract_events_from_news(limit=200)
    logger.info("Extracted %s event candidates", count)
    return count


def run_update_trends() -> int:
    """根据事件聚合结果刷新趋势分值。"""
    count = update_trends()
    logger.info("Updated %s trend rows", count)
    return count


def trigger_next(job_id: str) -> None:
    """触发下一个任务立即执行（链式触发）。"""
    job = scheduler.get_job(job_id)
    if job:
        job.modify(next_run_time=datetime.now())


def fetch_news_wrapper() -> None:
    """抓取新闻后链式触发抓取正文。"""
    fetch_news_every_hour()
    trigger_next("scrape_articles")


def scrape_articles_wrapper() -> None:
    """抓取正文后链式触发提取事件。"""
    scrape_articles()
    trigger_next("extract_events")


def extract_events_wrapper() -> None:
    """提取事件后链式触发更新趋势。"""
    extract_events()
    trigger_next("update_trends")


def setup_scheduler() -> None:
    """Register jobs with chained trigger pattern."""
    trigger = IntervalTrigger(minutes=FALLBACK_INTERVAL_MINUTES)

    scheduler.add_job(
        fetch_news_wrapper,
        trigger=trigger,
        id="fetch_news",
        name="Fetch RSS News",
        replace_existing=True,
    )

    scheduler.add_job(
        scrape_articles_wrapper,
        trigger=trigger,
        id="scrape_articles",
        name="Scrape Article Content",
        replace_existing=True,
    )

    scheduler.add_job(
        extract_events_wrapper,
        trigger=trigger,
        id="extract_events",
        name="Extract Events via LLM",
        replace_existing=True,
    )

    scheduler.add_job(
        run_update_trends,
        trigger=trigger,
        id="update_trends",
        name="Update Trend Scores",
        replace_existing=True,
    )

    scheduler.start()

    trigger_next("fetch_news")
