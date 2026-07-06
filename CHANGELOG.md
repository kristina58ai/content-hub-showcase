<!-- Язык: 🇷🇺 Русский · служебный файл -->

# Changelog

Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/). Conventional Commits в истории: `feat:` / `fix:` / `chore:` / `docs:` / `refactor:` / `test:`.

## [0.1.0] — 2026-07

### Added
- Backend: FastAPI + LangGraph 1.1.6, живой граф агентов через SSE (retrieval → generation → adaptation → learning).
- Оркестрация с ShallowRedisSaver-чекпоинтером (async) поверх Redis 8 / Upstash.
- Локальные эмбеддинги Qwen3-Embedding-0.6B + Chroma (precomputed); SQLite STRICT.
- LLM-фолбэк Groq → OpenRouter + fake-LLM dev-режим без внешних вызовов.
- Frontend: Next.js 16.2.6, React 19, React Flow, Zustand + TanStack Query, Tailwind v4.
- Видимая панель Data Ingestion (ADR-016), демо learning cycle.
- Тесты: pytest 66 (93% coverage), vitest 22, Playwright e2e.
- 17 ADR в DECISIONS.md.

### In progress
- Live-demo деплой: Vercel (frontend) + HuggingFace Spaces Docker (backend).
