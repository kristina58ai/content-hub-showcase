<!-- Язык: 🇷🇺 Русский · английская версия не требуется (служебный docs-файл) -->

# BUILD REPORT — Content-hub Showcase

Что построено, как и на чём — с честными заметками о процессе. Портфолио-версия Content-hub для роли AI Agent Engineer.

## Идентичность

- Продукт: публичная веб-демонстрация мультиагентной системы генерации контента с живым графом агентов.
- Собран: spec-driven (plan → Architectural Specification → Product TS), pair programming с Claude Code.
- Статус: код и тесты готовы; live-demo — деплой в процессе (Vercel + HF Spaces).

## Тесты

| Слой | Инструмент | Покрытие |
|---|---|---|
| Backend | pytest | 66 тестов, 93% coverage |
| Frontend | vitest | 22 теста |
| E2E | Playwright | полный сценарий рекрутёра |

Ключи не нужны: LLM и эмбеддинги замоканы в тестах.

## Тройное доказательство глубины

1. **17 ADR** в [DECISIONS](../DECISIONS.md) — каждое решение с контекстом, альтернативами, последствиями и защитой на собесе.
2. **Скриншоты** ключевых экранов (`docs/screenshots/`) + GIF основного флоу (`docs/demo-flow.gif`).
3. **Behind the Scenes** — честные заметки о процессе (ниже).

## Находки процесса (Behind the Scenes)

- **Sync vs async Redis-чекпоинтер.** ShallowRedisSaver в синхронном варианте блокировал event loop FastAPI — граф «замирал» на живом SSE-стриме. Исправлено переходом на async-чекпоинтер. Открытие есть в истории коммитов.
- **Redis 8 и `FT.*`.** Чекпоинтер LangGraph требует модули RediSearch — обычный Redis 7 не подходит. Dev поднимает Redis 8 через `docker-compose.dev.yml`, прод — Upstash.
- **SQLite STRICT и TIMESTAMP.** Тип `TIMESTAMP` невалиден в STRICT — «привычные» схемы из туториалов падают на `CREATE TABLE`. Схема переписана под TEXT + ISO-8601.
- **Пины версий, которых не было на PyPI.** Часть версий из спеки отсутствовала в индексе. Решение: сверка с реальным PyPI, фиксация ближайших существующих версий, явная запись расхождений.
- **TDD.** Тесты писались вместе с кодом, не «потом».

## AI-collaboration disclosure

Claude Code был pair programmer. Пользователь отвечал за архитектурные и продуктовые решения (см. DECISIONS), debugging, testing; Claude — за implementation details, boilerplate, черновики документации. Это не AI-generated проект, а collaboration.
