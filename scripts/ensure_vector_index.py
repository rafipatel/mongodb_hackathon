"""Create the Atlas Vector Search index on MediMind.skills.embedding if missing.

Idempotent. Safe to run before every `seed_skills.py`.

Usage:
    uv run python scripts/ensure_vector_index.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import ATLAS_SEARCH_INDEX, MONGODB_DB, MONGODB_URI, VOYAGE_DIM  # noqa: E402


INDEX_DEFINITION = {
    "mappings": {
        "dynamic": True,
        "fields": {
            "embedding": {
                "type": "knnVector",
                "dimensions": VOYAGE_DIM,
                "similarity": "cosine",
            }
        },
    }
}


def _find_index(collection, name: str) -> dict | None:
    for idx in collection.list_search_indexes():
        if idx.get("name") == name:
            return idx
    return None


def ensure_index(wait_for_ready: bool = True, timeout_s: int = 180) -> None:
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db["skills"]

    existing = _find_index(collection, ATLAS_SEARCH_INDEX)
    if existing is None:
        print(f"[ensure_vector_index] Creating search index '{ATLAS_SEARCH_INDEX}' on {MONGODB_DB}.skills ...")
        model = SearchIndexModel(definition=INDEX_DEFINITION, name=ATLAS_SEARCH_INDEX)
        collection.create_search_indexes([model])
    else:
        status = existing.get("status", "UNKNOWN")
        queryable = existing.get("queryable", False)
        print(f"[ensure_vector_index] Index '{ATLAS_SEARCH_INDEX}' already present (status={status}, queryable={queryable})")
        if queryable:
            return

    if not wait_for_ready:
        return

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        idx = _find_index(collection, ATLAS_SEARCH_INDEX)
        if idx and idx.get("queryable"):
            print(f"[ensure_vector_index] Index is now queryable.")
            return
        print(f"[ensure_vector_index] Waiting for build... status={idx.get('status') if idx else 'missing'}")
        time.sleep(5)

    print("[ensure_vector_index] Timed out waiting for index to become queryable. It may still finish in the background.")


if __name__ == "__main__":
    ensure_index()
