<!-- Язык: 🇷🇺 Русский · английская версия не требуется (служебный docs-файл) -->

# SPEC — Content-hub Showcase

Техническая спецификация. Расширяет [README](../README.md); архитектурные решения с альтернативами — в [DECISIONS](../DECISIONS.md) (17 ADR).

## Назначение

Публичная веб-демонстрация мультиагентной AI-системы генерации контента с **живым графом агентов в реальном времени**. Система генерирует контент под выбранный архетип автора (AI Engineer / Growth Marketer / Physician Educator) и адаптирует его под 5 платформ: Telegram, X, LinkedIn, Medium, Threads.

Главная фича — пока LangGraph-оркестрация работает на backend, каждый шаг пайплайна (retrieval → generation → adaptation → learning) стримится через SSE и анимируется в браузере на React Flow.

## Стек

| Слой | Технологии |
|---|---|
| Backend | FastAPI (async) + LangGraph 1.1.6 |
| Оркестрация | LangGraph-граф + ShallowRedisSaver-чекпоинтер поверх Redis 8 / Upstash |
| Семантика | локальные эмбеддинги Qwen3-Embedding-0.6B (1024-dim), Chroma (precomputed на build-этапе) |
| Данные | SQLite в STRICT-режиме (TEXT + ISO-8601, валидация на уровне приложения) |
| LLM | фолбэк Groq → OpenRouter; fake-LLM dev-режим без внешних вызовов |
| Frontend | Next.js 16.2.6, React 19, React Flow, Zustand + TanStack Query, Tailwind v4 |
| Стриминг | SSE (шаги графа → анимация в браузере) |
| Деплой | Vercel (frontend) + HuggingFace Spaces Docker (backend) |

## Ключевые инженерные инварианты

- **Redis 8 обязателен:** LangGraph-чекпоинтер требует модули RediSearch (команды `FT.*`) — обычный Redis 7 не подходит.
- **Async-чекпоинтер:** синхронный ShallowRedisSaver блокировал event loop FastAPI (граф «замирал» на SSE) — переведён на async-вариант.
- **SQLite STRICT + TIMESTAMP:** тип `TIMESTAMP` невалиден в STRICT-режиме — схема переписана под TEXT + ISO-8601.
- **Пины версий сверяются с реальным PyPI** при установке (часть версий из спеки не существовала в индексе).

## Видимость (portfolio-first решения)

- **Data Ingestion** — видимая панель вместо скрытых скраперов (ADR-016).
- **Learning cycle** — демонстрационный event-triggered цикл обучения по фидбеку.
- **Живой граф** — зритель смотрит, как система работает, а не читает о ней.

## Структура репозитория

```
backend/     FastAPI + LangGraph: src, tests (pytest), alembic, scripts, Dockerfile
frontend/    Next.js: src, __tests__ (vitest), e2e (Playwright)
docs/        SPEC, HOW_TO_DEPLOY, BUILD_REPORT, screenshots, demo-flow.gif
docker-compose.dev.yml   Redis 8 для локальной разработки
```
