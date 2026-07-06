# Content-hub Showcase

**A public web demo of a multi-agent AI content system — with a live, real-time agent graph.**

[Русская версия → README.md](README.md)

![Next.js](https://img.shields.io/badge/Next.js-16.2.6-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1.6-1C3C3C)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Chroma](https://img.shields.io/badge/Chroma-embedded-FF6B35)
![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)

**Live demo:** *(deploy pending)*

---

## What this is

Content-hub Showcase is a portfolio project for an AI Agent Engineer role: a public demo of a multi-agent system that generates content for a chosen author archetype (AI Engineer / Growth Marketer / Physician Educator) and adapts it for 5 platforms — Telegram, X, LinkedIn, Medium, Threads.

The headline feature is a **live agent graph built on React Flow**: while the LangGraph orchestration runs on the backend, every pipeline step (retrieval → generation → adaptation → learning) streams over SSE and animates in the browser in real time. You don't read *about* a multi-agent system — you watch it work.

On top of that: a visible **Data Ingestion** panel (instead of hidden scrapers — ADR-016) and a demo **learning cycle** (event-triggered learning from feedback).

**Stack:** FastAPI + LangGraph 1.1.6, local Qwen3-Embedding-0.6B embeddings (1024-dim), Chroma (precomputed at build time), ShallowRedisSaver checkpointer over Redis/Upstash, SQLite STRICT, Groq → OpenRouter LLM fallback. Frontend: Next.js 16.2.6, React 19, React Flow, Zustand + TanStack Query, Tailwind v4. Deployment: Vercel (frontend) + HuggingFace Spaces Docker (backend).

---

## Triple proof of depth

This project was built in a short timeframe — and I know how that looks. So the depth of the work is proven in three independent ways.

### 1. Architecture decisions — [DECISIONS.md](DECISIONS.md)

17 ADRs (Architecture Decision Records): every decision comes with context, considered alternatives, consequences, and an interview defense. From choosing LangGraph 1.1.6 with ShallowRedisSaver (ADR-009) to replacing Gemini embeddings with local Qwen3-Embedding-0.6B (ADR-017) and deliberately removing the observability stack (ADR-015).

### 2. Screenshots

| | |
|---|---|
| ![Home: archetype selection](docs/screenshots/01-home-archetypes.png) | ![Live graph and result](docs/screenshots/02-live-graph-result.png) |
| *Home: 3 demo archetypes* | *Live React Flow graph + per-platform result* |
| ![Data Ingestion](docs/screenshots/03-data-ingest.png) | ![Learning cycle](docs/screenshots/04-learning-cycle.png) |
| *Data Ingestion panel* | *Demo learning cycle* |

### 3. Behind the Scenes — honest process notes

- **Spec-driven development.** Code was written against a finalized plan and architectural specification (plan → Architectural Specification → Product TS), not improvised. Every task had acceptance criteria used as a checklist.
- **TDD.** Tests were written alongside the code, not afterwards: pytest — 66 tests, 93% coverage; vitest — 22 tests; Playwright e2e covers the full recruiter flow.
- **Version pins that didn't exist on PyPI.** Some versions in the spec were pinned "forward" and were absent from the index at install time. The fix: verify against real PyPI at install, pin the nearest existing versions, and record the deviations explicitly — instead of blindly copying the spec.
- **Sync vs async Redis checkpointer.** The synchronous ShallowRedisSaver blocked the FastAPI event loop. Discovered on the live SSE stream (the graph "froze"), fixed by switching to the async checkpointer variant. This discovery lives in the commit history, not just in this paragraph.
- **Redis 8 and FT.\*.** The LangGraph Redis checkpointer requires the RediSearch modules (`FT.*` commands) — plain Redis 7 won't do. So the dev environment brings up Redis 8 via `docker-compose.dev.yml`, and production uses Upstash.
- **SQLite STRICT and TIMESTAMP.** In STRICT mode, SQLite rejects the `TIMESTAMP` column type (STRICT accepts only INT/INTEGER/REAL/TEXT/BLOB/ANY) — the "usual" tutorial schemas fail at `CREATE TABLE`. The schema was rewritten as TEXT + ISO-8601 with application-level validation.

---

## AI-collaboration disclosure

> Claude Code was the pair programmer for this project. I was responsible for: architecture decisions (see [DECISIONS.md](DECISIONS.md)), product decisions, debugging, testing. Claude was responsible for: implementation details, boilerplate, documentation drafts. This is **not** an AI-generated project — it's a collaboration. See the Behind the Scenes section above for process details.

---

## Quick start

Requirements: Python 3.12+, Node.js 20+, Docker (for Redis 8).

### 0. Redis 8 (LangGraph checkpointer)

```bash
# from the showcase/ directory
docker compose -f docker-compose.dev.yml up -d
```

### 1. Backend (FastAPI + LangGraph)

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate            # Windows (source .venv/bin/activate on unix)
pip install -e ".[dev]"

copy .env.example .env            # cp on unix; LLM keys are optional, see below

alembic upgrade head
python scripts/build_demo_db.py   # first run downloads Qwen3-Embedding-0.6B (~1.2 GB)

uvicorn content_hub_showcase.main:app --port 8000
```

Health check: `GET http://localhost:8000/api/v1/health`

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

### 3. Tests

```bash
# backend (from showcase/backend)
pytest                            # 66 tests, 93% coverage; no API keys needed — LLM/embeddings are mocked

# frontend (from showcase/frontend)
npm run test                      # vitest, 22 tests

# e2e (needs both servers running: backend :8000 + frontend :3000)
npx playwright test
```

### LLM keys

| Variable | Role |
|---|---|
| `GROQ_API_KEY` | primary provider (free tier) |
| `OPENROUTER_API_KEY` | fallback |

Without keys, the backend runs in **fake-LLM dev mode** — the whole flow, including the live graph, works locally without a single external call.

---

## If the live demo is down

[EXAMPLES.md](EXAMPLES.md) — the visual fallback: a GIF of the main flow plus screenshots of the key screens. If the live demo is broken, these materials show what should happen.

---

## Project portfolio (distinct positioning)

| Project | Focus |
|---|---|
| **Content-hub** (this repository) | Multi-agent **visible** orchestration + production deployment (Vercel + HF Spaces) |
| [Learning-hub](https://github.com/USERNAME/learning-hub) | RAG stack: retrieval pipelines, embeddings, quality evaluation |
| [DEV-HUB V.6](https://github.com/USERNAME/dev-hub-v6) | LangGraph migration + observability |

The three projects deliberately split the technical domains — no stack duplication.

---

## Commit convention

Conventional Commits: `feat:` / `fix:` / `chore:` / `docs:` / `refactor:` / `test:`. Natural dev traces (`wip:`, `fix typo`) are allowed — this is a real history, not a staged one.
