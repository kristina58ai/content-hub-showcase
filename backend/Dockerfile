# Content-hub Showcase backend — HuggingFace Spaces (sdk: docker).
# HF Spaces routes traffic to app_port declared in README.md (7860).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache

WORKDIR /app

# Install dependencies first for layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY data/demo_archetypes ./data/demo_archetypes

# ADR-011: build-time precomputation of the demo Chroma DB.
# Embeddings are local Qwen3-Embedding-0.6B (ADR-017) — no API keys needed at build.
# The model (~1.2GB) is downloaded during build and cached in the image.
RUN python scripts/build_demo_db.py

EXPOSE 7860

# Migrations run at container start (HF Spaces storage is ephemeral — showcase.db
# is recreated on every boot; durable state lives in Upstash Redis, ADR-009).
CMD ["sh", "-c", "alembic upgrade head && uvicorn content_hub_showcase.main:app --host 0.0.0.0 --port 7860"]
