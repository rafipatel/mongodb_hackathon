"""MediMind FastAPI entrypoint.

Endpoints:
  GET  /                            — dashboard (static/index.html)
  GET  /health                      — liveness + atlas/livekit/index status
  POST /transcript                  — text-only fallback when LiveKit is offline
  GET  /skills/count                — how many skills currently in Atlas
  GET  /skills/recent               — last N skills (for the live demo dashboard)
  GET  /sessions/recent             — last N sessions
  GET  /livekit/token?identity=...  — issue a join token for the demo room

The voice gateway is started in lifespan if LIVEKIT_URL is set. Failures there
are logged but never prevent the HTTP server from coming up.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.orchestrator import build_app
from config import (
    ATLAS_SEARCH_INDEX,
    LIVEKIT_API_KEY,
    LIVEKIT_ROOM,
    LIVEKIT_URL,
    SKILL_MATCH_THRESHOLD,
)
from memory.client import get_collection, get_db, ping
from voice.gateway import generate_join_token, run_voice_gateway

STATIC_DIR = Path(__file__).resolve().parent / "static"

_state = {"agent": None, "mongo_client": None, "voice_task": None}


async def _handle_transcript(text: str) -> dict:
    """Run a transcript through the LangGraph agent."""
    agent = _state["agent"]
    if agent is None:
        raise RuntimeError("Agent not initialised")

    session_id = f"shift-{uuid.uuid4().hex[:8]}"
    initial = {
        "session_id": session_id,
        "transcript": text,
        "matched_skills": [],
        "best_score": 0.0,
        "forge_triggered": False,
        "forge_retries": 0,
    }
    config = {"configurable": {"thread_id": session_id}}
    result = await agent.ainvoke(initial, config=config)
    return {
        "session_id": session_id,
        "response": result.get("response_text"),
        "matched_skill_id": (result.get("matched_skills") or [{}])[0].get("id"),
        "best_score": result.get("best_score"),
        "forge_triggered": result.get("forge_triggered"),
        "new_skill_id": result.get("new_skill_id"),
    }


async def _safe_voice_gateway(on_transcript):
    try:
        await run_voice_gateway(on_transcript)
    except Exception as exc:  # noqa: BLE001
        print(f"[server] voice gateway exited: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    agent, mongo_client = await build_app()
    _state["agent"] = agent
    _state["mongo_client"] = mongo_client

    if LIVEKIT_URL and LIVEKIT_API_KEY:
        async def _on_transcript(text: str):
            try:
                await _handle_transcript(text)
            except Exception as exc:  # noqa: BLE001
                print(f"[server] handle_transcript error: {exc}")

        _state["voice_task"] = asyncio.create_task(_safe_voice_gateway(_on_transcript))

    try:
        yield
    finally:
        if _state["voice_task"]:
            _state["voice_task"].cancel()
        if _state["mongo_client"]:
            _state["mongo_client"].close()


app = FastAPI(title="MediMind", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscriptIn(BaseModel):
    text: str


async def _vector_index_status() -> dict:
    """Best-effort peek at the Atlas Search index status. Non-blocking on failure."""
    try:
        cursor = get_db()["skills"].list_search_indexes()
        async for idx in cursor:
            if idx.get("name") == ATLAS_SEARCH_INDEX:
                return {
                    "name": idx.get("name"),
                    "status": idx.get("status"),
                    "queryable": bool(idx.get("queryable")),
                }
        return {"name": ATLAS_SEARCH_INDEX, "status": "missing", "queryable": False}
    except Exception as exc:  # noqa: BLE001
        return {"name": ATLAS_SEARCH_INDEX, "status": f"error: {exc}", "queryable": False}


@app.get("/health")
async def health():
    ok = await ping()
    idx = await _vector_index_status()
    return {
        "status": "ok" if ok else "degraded",
        "atlas": ok,
        "livekit": bool(LIVEKIT_URL and LIVEKIT_API_KEY),
        "vector_index_ready": idx["queryable"],
        "vector_index_status": idx["status"],
        "match_threshold": SKILL_MATCH_THRESHOLD,
    }


@app.post("/transcript")
async def transcript(body: TranscriptIn):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="empty transcript")
    return await _handle_transcript(body.text)


@app.get("/skills/count")
async def skill_count():
    n = await get_collection("skills").count_documents({})
    return {"total_skills": n}


@app.get("/skills/recent")
async def skills_recent(limit: int = 10):
    cursor = (
        get_collection("skills")
        .find({}, {"_id": 0, "embedding": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    return {"skills": await cursor.to_list(limit)}


@app.get("/sessions/recent")
async def sessions_recent(limit: int = 20):
    cursor = (
        get_collection("sessions")
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return {"sessions": await cursor.to_list(limit)}


@app.get("/livekit/token")
async def livekit_token(identity: str = "clinician"):
    if not (LIVEKIT_URL and LIVEKIT_API_KEY):
        raise HTTPException(status_code=503, detail="LiveKit not configured")
    return {"room": LIVEKIT_ROOM, "token": generate_join_token(identity=identity)}


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def root():
        return FileResponse(STATIC_DIR / "index.html")
