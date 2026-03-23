"""Database schema models for Trend News Agent."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class NewsRaw(Base):
    """原始新闻表：保存抓取到的标题、链接、摘要与正文。"""

    __tablename__ = "news_raw"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # URL 唯一，避免同一新闻重复入库。
    url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # content 由正文抓取步骤补全，初次抓取时可能为空。
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # title_hash 用于近似去重（同标题不同 URL 的镜像内容）。
    title_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)


class Event(Base):
    """结构化事件表：由 LLM 从新闻内容抽取后落库。"""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    impact_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    # source_count 表示该事件被多少新闻源共同印证。
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    event_heat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    sources: Mapped[list["EventSource"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class EventSource(Base):
    """事件来源关联表：记录事件与新闻之间的多对多关系。"""

    __tablename__ = "event_sources"
    __table_args__ = (UniqueConstraint("event_id", "news_id", name="uq_event_news"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news_raw.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    event: Mapped[Event] = relationship(back_populates="sources")


class Keyword(Base):
    """关键词配置表：用于调节不同分类的趋势权重。"""

    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    # status 通常为 active / inactive。
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)


class Trend(Base):
    """趋势结果表：按“分类 + 日期”记录聚合后的趋势得分。"""

    __tablename__ = "trends"
    __table_args__ = (UniqueConstraint("category", "start_date", name="uq_trend_category_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trend_heat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    momentum: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    last_update: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
