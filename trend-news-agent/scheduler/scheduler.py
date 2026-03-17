"""APScheduler orchestrator for periodic pipeline runs."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from fetcher.rss_fetcher import fetch_rss_news
from llm.event_extractor import extract_events_from_news
from scraper.article_scraper import scrape_pending_articles
from trends.trend_engine import update_trends

logger = logging.getLogger(__name__)

# 使用后台调度器，在 FastAPI 主线程之外执行周期性任务。
scheduler = BackgroundScheduler()


def fetch_news_every_hour() -> None:
    """抓取 RSS 源中的最新新闻并记录新增数量。"""
    count = fetch_rss_news()
    logger.info("Fetched %s new RSS records", count)


def scrape_articles() -> None:
    """补全文章正文内容，优先处理尚未抓取正文的新闻。"""
    count = scrape_pending_articles(limit=200)
    logger.info("Scraped %s articles", count)


def extract_events() -> None:
    """调用 LLM 从新闻正文中提取结构化事件候选。"""
    count = extract_events_from_news(limit=200)
    logger.info("Extracted %s event candidates", count)


def run_update_trends() -> None:
    """根据事件聚合结果刷新趋势分值。"""
    count = update_trends()
    logger.info("Updated %s trend rows", count)


def setup_scheduler() -> None:
    """Register all jobs with a 60-minute interval."""
    # 统一使用 replace_existing=True，避免应用热重启时重复注册同名任务。
    scheduler.add_job(fetch_news_every_hour, "interval", minutes=60, id="fetch_news", replace_existing=True)
    scheduler.add_job(scrape_articles, "interval", minutes=60, id="scrape_articles", replace_existing=True)
    scheduler.add_job(extract_events, "interval", minutes=60, id="extract_events", replace_existing=True)
    scheduler.add_job(run_update_trends, "interval", minutes=60, id="update_trends", replace_existing=True)
    scheduler.start()
