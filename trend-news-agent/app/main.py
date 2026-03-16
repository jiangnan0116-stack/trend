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

app.include_router(news_router)
app.include_router(events_router)
app.include_router(trends_router)
app.include_router(keywords_router)


@app.get("/")
def healthcheck():
    return {"service": settings.PROJECT_NAME, "status": "ok"}


@app.on_event("startup")
def startup_event():
    setup_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown(wait=False)
