<!-- Язык: 🇷🇺 Русский · английская версия не требуется (служебный docs-файл) -->

# HOW TO DEPLOY — Content-hub Showcase

Локальный запуск и продакшен-деплой. Быстрый старт также продублирован в [README](../README.md).

## Требования

- Python 3.12+
- Node.js 20+
- Docker (для Redis 8 — чекпоинтер LangGraph)

## Локальный запуск

### 0. Redis 8

```bash
# из каталога showcase/
docker compose -f docker-compose.dev.yml up -d
```

### 1. Backend (FastAPI + LangGraph)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows (source .venv/bin/activate на unix)
pip install -e ".[dev]"
copy .env.example .env            # cp на unix; ключи LLM опциональны
alembic upgrade head
python scripts/build_demo_db.py   # первый запуск качает Qwen3-Embedding-0.6B (~1.2 GB)
uvicorn content_hub_showcase.main:app --port 8000
```

Health check: `GET http://localhost:8000/api/v1/health`

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

## LLM-ключи

| Переменная | Роль |
|---|---|
| `GROQ_API_KEY` | основной провайдер (бесплатный tier) |
| `OPENROUTER_API_KEY` | фолбэк |

Без ключей backend работает в **fake-LLM dev-режиме** — весь флоу, включая живой граф, доступен локально без единого внешнего вызова.

## Продакшен

| Компонент | Платформа |
|---|---|
| Frontend | Vercel |
| Backend | HuggingFace Spaces (Docker) |
| Redis | Upstash (managed, с RediSearch) |

## Тесты

```bash
# backend (из showcase/backend)
pytest                            # 66 тестов, 93% coverage; ключи не нужны (LLM/эмбеддинги замоканы)
# frontend (из showcase/frontend)
npm run test                      # vitest, 22 теста
# e2e (нужны оба сервера: backend :8000 + frontend :3000)
npx playwright test
```
