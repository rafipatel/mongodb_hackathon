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
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.orchestrator import build_app
from config import (
    ATLAS_SEARCH_INDEX,
    DISCORD_WEBHOOK_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_ROOM,
    LIVEKIT_URL,
    SKILL_MATCH_THRESHOLD,
)
from memory.client import get_collection, get_db, ping
from notifications.dispatcher import execute_and_notify, fetch_skill_code
from voice.gateway import generate_join_token, run_voice_gateway
from voice.speak import is_configured as tts_configured, speak_stream

STATIC_DIR = Path(__file__).resolve().parent / "static"

_state = {"agent": None, "mongo_client": None, "voice_task": None}


async def _handle_transcript(text: str, *, execute: bool = True) -> dict:
    """Run a transcript through the LangGraph agent, then (optionally) execute the skill."""
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

    matched_skill_id = (result.get("matched_skills") or [{}])[0].get("id")
    new_skill_id = result.get("new_skill_id")
    matched_code = (result.get("matched_skills") or [{}])[0].get("code")
    forge_triggered = bool(result.get("forge_triggered"))

    payload = {
        "session_id": session_id,
        "response": result.get("response_text"),
        "matched_skill_id": matched_skill_id,
        "best_score": result.get("best_score"),
        "forge_triggered": forge_triggered,
        "new_skill_id": new_skill_id,
        "notifications": None,
    }

    if execute:
        skill_id = new_skill_id or matched_skill_id
        code = matched_code
        if new_skill_id:
            code = await fetch_skill_code(new_skill_id)

        if skill_id and code:
            payload["notifications"] = await execute_and_notify(
                skill_code=code,
                skill_id=skill_id,
                session_id=session_id,
                patient_id=_extract_patient_hint(text),
                ward=_extract_ward_hint(text),
            )

    return payload


_PATIENT_RE = re.compile(r"\bbed\s+(\w+)\b", re.IGNORECASE)
_WARD_RE = re.compile(r"\bward\s+([\w-]+)\b", re.IGNORECASE)


def _extract_patient_hint(text: str) -> str:
    m = _PATIENT_RE.search(text or "")
    return f"bed-{m.group(1)}" if m else "unknown"


def _extract_ward_hint(text: str) -> str:
    m = _WARD_RE.search(text or "")
    return m.group(1) if m else "ward"


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

    # The full LiveKit voice pipeline (VAD + STT + LLMAdapter + TTS) runs as a
    # dedicated worker: ``uv run python voice/medimind_agent.py dev``.
    # The legacy fallback gateway (voice/gateway.py) is no longer auto-started
    # here, but can still be run standalone if needed.

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
        "tts": tts_configured(),
        "discord": bool(DISCORD_WEBHOOK_URL),
        "vector_index_ready": idx["queryable"],
        "vector_index_status": idx["status"],
        "match_threshold": SKILL_MATCH_THRESHOLD,
    }


@app.post("/transcript")
async def transcript(body: TranscriptIn):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="empty transcript")
    return await _handle_transcript(body.text)


class SpeakIn(BaseModel):
    text: str


def _stream_tts(text: str) -> StreamingResponse:
    return StreamingResponse(
        speak_stream(text),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/speak")
async def speak_get(text: str):
    """Stream ElevenLabs TTS via a plain URL — so `<audio src="/speak?text=...">` works."""
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="missing text")
    if not tts_configured():
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")
    return _stream_tts(text)


@app.post("/speak")
async def speak_post(body: SpeakIn):
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="missing text")
    if not tts_configured():
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")
    return _stream_tts(text)


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


@app.get("/notifications/recent")
async def notifications_recent(limit: int = 20):
    cursor = (
        get_collection("notifications")
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return {"notifications": await cursor.to_list(limit)}


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
    return {
        "room": LIVEKIT_ROOM,
        "url": LIVEKIT_URL,
        "token": generate_join_token(identity=identity),
    }


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def root():
        return FileResponse(STATIC_DIR / "index.html")
