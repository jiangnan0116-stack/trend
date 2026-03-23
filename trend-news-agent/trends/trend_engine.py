"""Backward-compatible wrapper for trend heat updates."""
from __future__ import annotations

from trends.heat_engine import update_trends

__all__ = ["update_trends"]
from sqlalchemy import select

from database.db import SessionLocal
from database.models import Event, Keyword, Trend

# 当天没有任何事件时，仍会为这些默认分类保留趋势行，方便前端固定展示。
DEFAULT_CATEGORIES = ["AI", "Semiconductor", "Macro", "Cloud", "Energy", "Finance"]


def update_trends() -> int:
    """Aggregate event impact and keyword weights by category into trends table."""
    db = SessionLocal()
    updated = 0
    try:
        # 仅加载启用中的关键词：停用关键词不应影响权重计算。
        keywords = db.execute(select(Keyword).where(Keyword.status == "active")).scalars().all()

        # 默认权重为 1.0；若同类目存在多个关键词，取最大权重以体现该类目最强信号。
        weights = defaultdict(lambda: 1.0)
        for kw in keywords:
            weights[kw.category] = max(weights[kw.category], kw.weight)

        # 读取事件后按 category 聚合：
        # score = Σ(impact_score * category_weight)
        # count = 事件数量
        events = db.execute(select(Event)).scalars().all()
        agg = defaultdict(lambda: {"score": 0.0, "count": 0})

        for event in events:
            weight = weights[event.category]
            agg[event.category]["score"] += float(event.impact_score) * weight
            agg[event.category]["count"] += 1

        today = date.today()
        # 覆盖“默认分类 + 实际出现分类”，确保趋势表每天维度齐全。
        for category in set(DEFAULT_CATEGORIES) | set(agg.keys()):
            info = agg.get(category, {"score": 0.0, "count": 0})
            trend = db.execute(
                select(Trend).where(Trend.category == category, Trend.start_date == today)
            ).scalar_one_or_none()
            if trend is None:
                # 当天首条记录：新建趋势行。
                trend = Trend(
                    category=category,
                    trend_score=info["score"],
                    event_count=info["count"],
                    start_date=today,
                    last_update=datetime.utcnow(),
                )
                db.add(trend)
            else:
                # 当天已有记录：覆盖分值并更新时间戳。
                trend.trend_score = info["score"]
                trend.event_count = info["count"]
                trend.last_update = datetime.utcnow()
            updated += 1

        db.commit()
    finally:
        # 无论成功/失败都释放连接，避免连接泄漏。
        db.close()
    return updated
