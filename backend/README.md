---
title: Content-hub Showcase
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Content-hub Showcase — Backend

FastAPI + LangGraph 1.1.6 backend for the public Content-hub demo.
Frontend lives in `../frontend` (Next.js, deployed to Vercel).

## Quick start (local)

```bash
# 1. Redis for the LangGraph checkpointer (from showcase/):
docker compose -f ../docker-compose.dev.yml up -d

# 2. Install:
python -m venv .venv
.venv\Scripts\activate            # Windows (source .venv/bin/activate on unix)
pip install -e ".[dev]"

# 3. Configure:
copy .env.example .env            # fill GROQ_API_KEY when available

# 4. Migrate + run:
alembic upgrade head
uvicorn content_hub_showcase.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/v1/health`

## Tests

```bash
pytest
ruff check .
mypy
```

No real API keys are required for the test suite — all LLM/embedding calls are mocked.

## Environment

See `.env.example`. `LANGGRAPH_STRICT_MSGPACK=true` is **mandatory** (ADR-009) —
the app refuses to start without it.
