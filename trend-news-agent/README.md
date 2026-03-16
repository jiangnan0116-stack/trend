# trend-news-agent

Production-ready MVP for collecting finance/tech news, extracting structured events, and detecting industry trends.

## Architecture

Pipeline:

RSS Sources → News Fetcher → Deduplication → Article Scraper → LLM Event Extraction → Event Clustering → Trend Engine → API Output

Core stack:
- Python 3.11
- FastAPI
- PostgreSQL + SQLAlchemy ORM
- feedparser
- newspaper3k
- OpenAI API
- APScheduler

## Project structure

```text
trend-news-agent/
  app/
    main.py
    config.py
  database/
    db.py
    models.py
  fetcher/
    rss_fetcher.py
  scraper/
    article_scraper.py
  dedup/
    dedup_service.py
  llm/
    event_extractor.py
  clustering/
    event_clusterer.py
  trends/
    trend_engine.py
  scheduler/
    scheduler.py
  api/
    routes_news.py
    routes_events.py
    routes_trends.py
    routes_keywords.py
  scripts/
    init_db.py
  requirements.txt
  README.md
```

## Setup

1. Use Python 3.11 and create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables (or `.env` file):

```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/trend_news_agent
OPENAI_API_KEY=your-openai-key
```

4. Initialize database and seed initial keywords:

```bash
python -m scripts.init_db
```

Seeded keywords:
- AI chip
- GPU demand
- data center expansion
- cloud capex
- AI infrastructure
- semiconductor equipment

## Run API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Scheduler behavior

On FastAPI startup, APScheduler registers and starts these 60-minute interval jobs:
- `fetch_news_every_hour`
- `scrape_articles`
- `extract_events`
- `update_trends`

The scheduler continuously updates the pipeline so the API serves fresh trend intelligence.

## API endpoints

- `GET /news` → recent raw news
- `GET /events` → extracted/clustered events
- `GET /trends` → trend scores by category
- `GET /keywords` → keyword list
- `POST /keywords` → add keyword
- `DELETE /keywords/{id}` → disable keyword

## Scalability notes

- URL + title hash dedup reduces duplicate writes/processing.
- Pipeline modules are decoupled and can move to queues/workers later.
- Event clustering prevents event table explosion from repeated coverage.
- Trend aggregation is incremental and category-scoped.
- API and scheduler are cleanly separated and can run in independent containers.
