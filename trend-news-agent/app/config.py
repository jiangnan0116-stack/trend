"""Application configuration for Trend News Agent."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "trend-news-agent"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/trend_news_agent"
    OPENAI_API_KEY: str = "replace-me"
    GLM_API_KEY: str = "replace-me"
    KIMI_API_KEY: str = "replace-me"
    MINIMAX_API_KEY: str = "replace-me"
    QWEN_API_KEY: str = "replace-me"

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = ""

    RSS_SOURCES: dict[str, str] = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "Reuters Technology": "https://www.reutersagency.com/feed/?best-topics=technology",
        "VentureBeat": "https://venturebeat.com/category/ai/feed/",
        "Wired": "https://www.wired.com/feed/rss",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index",
    }

    FETCH_WINDOW_HOURS: int = 48
    SIMILARITY_THRESHOLD: float = 0.90


settings = Settings()
