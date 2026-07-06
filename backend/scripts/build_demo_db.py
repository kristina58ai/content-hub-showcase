"""Build-time precomputation of the demo Chroma DB (ADR-011 + ADR-017).

Reads archetype JSON sources from data/demo_archetypes/, embeds personality
facts + exemplars with the local Qwen3-Embedding-0.6B model (1024 dim, no API
keys) and persists Chroma collections under data/chroma_demo/.

Run from showcase/backend/:  python scripts/build_demo_db.py
VS-1 fills data/demo_archetypes/ with the 3 archetypes; with no JSON files the
script still creates empty collections so `docker build` stays green.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from content_hub_showcase.shared.config import get_settings  # noqa: E402
from content_hub_showcase.shared.embeddings import build_embedding_provider  # noqa: E402
from content_hub_showcase.shared.vector_db import (  # noqa: E402
    COLLECTION_EXEMPLARS,
    COLLECTION_PERSONALITY,
    ChromaClient,
)


def load_archetypes(source_dir: Path) -> list[dict[str, Any]]:
    archetypes: list[dict[str, Any]] = []
    for json_file in sorted(source_dir.glob("*.json")):
        with json_file.open(encoding="utf-8") as fh:
            archetypes.append(json.load(fh))
    return archetypes


def main() -> int:
    settings = get_settings()
    source_dir = BACKEND_ROOT / "data" / "demo_archetypes"
    persist_dir = BACKEND_ROOT / settings.chroma_demo_dir

    provider = build_embedding_provider(settings)
    chroma = ChromaClient(persist_dir)
    # Touch both collections so the backend can open them even with no data.
    chroma.collection(COLLECTION_PERSONALITY)
    chroma.collection(COLLECTION_EXEMPLARS)

    archetypes = load_archetypes(source_dir)
    if not archetypes:
        print(f"[build_demo_db] no archetype JSON in {source_dir} — created empty collections")
        return 0

    total_facts = 0
    total_exemplars = 0
    for archetype in archetypes:
        archetype_id = archetype["archetype_id"]

        facts = archetype.get("personality", [])
        if facts:
            texts = [f["fact"] for f in facts]
            embeddings = provider.embed_documents(texts)
            chroma.add(
                COLLECTION_PERSONALITY,
                ids=[f"{archetype_id}-fact-{i}" for i in range(len(facts))],
                documents=texts,
                embeddings=embeddings,
                metadatas=[
                    {
                        "archetype": archetype_id,
                        "category": fact.get("category", ""),
                        "subcategory": fact.get("subcategory", ""),
                        "confidence": float(fact.get("confidence", 0.8)),
                        "embedding_model": provider.model_tag,
                    }
                    for fact in facts
                ],
            )
            total_facts += len(facts)

        exemplars = archetype.get("exemplars", [])
        if exemplars:
            texts = [e["text"] for e in exemplars]
            embeddings = provider.embed_documents(texts)
            chroma.add(
                COLLECTION_EXEMPLARS,
                ids=[f"{archetype_id}-exemplar-{i}" for i in range(len(exemplars))],
                documents=texts,
                embeddings=embeddings,
                metadatas=[
                    {
                        "archetype": archetype_id,
                        "platform": exemplar.get("platform", ""),
                        "topic": exemplar.get("topic", ""),
                        "engagement_score": float(exemplar.get("engagement_score", 0.0)),
                        "views": int(exemplar.get("views", 0)),
                        "likes": int(exemplar.get("likes", 0)),
                        "comments": int(exemplar.get("comments", 0)),
                        "shares": int(exemplar.get("shares", 0)),
                        "embedding_model": provider.model_tag,
                    }
                    for exemplar in exemplars
                ],
            )
            total_exemplars += len(exemplars)

        print(f"[build_demo_db] {archetype_id}: {len(facts)} facts, {len(exemplars)} exemplars")

    print(
        f"[build_demo_db] done: {len(archetypes)} archetypes, "
        f"{total_facts} facts, {total_exemplars} exemplars -> {persist_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
