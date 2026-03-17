"""FastAPI entrypoint for Trend News Agent."""
from __future__ import annotations

from fastapi import FastAPI

from api.routes_events import router as events_router
from api.routes_keywords import router as keywords_router
from api.routes_news import router as news_router
from api.routes_trends import router as trends_router
from app.config import settings
from scheduler.scheduler import scheduler, setup_scheduler

app = FastAPI(title=settings.PROJECT_NAME)

# 将不同业务域的接口按 router 进行挂载，便于后续模块化扩展。
app.include_router(news_router)
app.include_router(events_router)
app.include_router(trends_router)
app.include_router(keywords_router)


@app.get("/")
def healthcheck():
    # 基础健康检查接口，通常用于容器探针/反向代理存活检测。
    return {"service": settings.PROJECT_NAME, "status": "ok"}


@app.on_event("startup")
def startup_event():
    # 启动时注册并启动定时任务，驱动“抓取 -> 解析 -> 趋势更新”流水线。
    setup_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    # 仅在 scheduler 已运行时关闭，避免重复 shutdown 导致异常日志。
    if scheduler.running:
        scheduler.shutdown(wait=False)
