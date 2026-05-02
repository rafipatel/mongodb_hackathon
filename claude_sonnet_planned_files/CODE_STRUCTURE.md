# MediMind — Code Structure & Stubs

## Directory layout

```
MediMind/
├── README.md
├── FLOW.md
├── .env.example
├── pyproject.toml
│
├── server.py                 # FastAPI entry point
├── config.py                 # Env vars and constants
│
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py       # LangGraph graph definition
│   ├── state.py              # Shared TypedDict state
│   └── nodes/
│       ├── ingest.py         # Node 1 — receive + clean transcript
│       ├── memory_lookup.py  # Node 2 — Atlas vector search
│       ├── route.py          # Node 3 — conditional edge
│       └── respond.py        # Node 4 — build + speak response
│
├── memory/
│   ├── __init__.py
│   ├── client.py             # MongoDB Atlas connection singleton
│   ├── search.py             # embed_and_search()
│   └── store.py              # store_skill(), store_session(), store_task()
│
├── forge/
│   ├── __init__.py
│   ├── forge.py              # Fireworks AI code generation
│   ├── validator.py          # AWS Lambda sandbox runner
│   └── prompts.py            # Prompt templates
│
├── voice/
│   ├── __init__.py
│   ├── gateway.py            # LiveKit listener → transcript events
│   ├── transcribe.py         # Fireworks Whisper wrapper
│   └── speak.py              # ElevenLabs TTS → LiveKit out
│
├── schemas/
│   ├── skill.py
│   ├── session.py
│   └── task.py
│
└── tests/
    ├── synthetic_cases/
    │   └── transfer_cases.json
    ├── test_forge.py
    └── test_memory.py
```

---

## config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DB = os.environ.get("MONGODB_DB", "MediMind")
ATLAS_SEARCH_INDEX = os.environ.get("ATLAS_SEARCH_INDEX", "skill_index")

VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
VOYAGE_MODEL = "voyage-3"

FIREWORKS_API_KEY = os.environ["FIREWORKS_API_KEY"]
FIREWORKS_WHISPER = "accounts/fireworks/models/whisper-v3"
FIREWORKS_CODE_MODEL = "accounts/fireworks/models/deepseek-coder-v2-instruct"

AWS_LAMBDA_FUNCTION = os.environ.get("AWS_LAMBDA_FUNCTION", "MediMind-skill-validator")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-2")

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = os.environ["ELEVENLABS_VOICE_ID"]

SKILL_MATCH_THRESHOLD = 0.78
FORGE_MAX_RETRIES = 3
FORGE_PASS_SCORE = 0.80
ESCALATE_AFTER_MINUTES = 20
```

---

## schemas/skill.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class Skill:
    id: str
    name: str
    description: str
    code: str
    embedding: List[float]
    trigger_conditions: List[str]
    validation_score: float
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    trust_origin: str = "MediMind"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "embedding": self.embedding,
            "trigger_conditions": self.trigger_conditions,
            "validation_score": self.validation_score,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "trust_origin": self.trust_origin,
        }
```

---

## schemas/session.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Session:
    session_id: str
    transcript: str
    matched_skills: List[str] = field(default_factory=list)
    forge_triggered: bool = False
    forge_skill_id: Optional[str] = None
    response_text: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return self.__dict__
```

---

## agent/state.py

```python
from typing import TypedDict, List, Optional

class MediMindState(TypedDict):
    session_id: str
    transcript: str
    embedding: List[float]
    matched_skills: List[dict]      # [{id, score, code, name}]
    best_score: float
    forge_triggered: bool
    forged_code: Optional[str]
    forge_retries: int
    new_skill_id: Optional[str]
    response_text: str
    spoken: bool
```

---

## agent/orchestrator.py

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from agent.state import MediMindState
from agent.nodes.ingest import ingest
from agent.nodes.memory_lookup import memory_lookup
from agent.nodes.route import route
from agent.nodes.respond import respond
from forge.forge import forge_skill
from forge.validator import validate_skill
from memory.store import store_skill
from config import MONGODB_URI, MONGODB_DB

def should_forge(state: MediMindState) -> str:
    return "forge" if state["best_score"] < 0.78 else "execute"

def build_graph():
    graph = StateGraph(MediMindState)

    graph.add_node("ingest", ingest)
    graph.add_node("memory_lookup", memory_lookup)
    graph.add_node("route", route)
    graph.add_node("forge_skill", forge_skill)
    graph.add_node("validate_skill", validate_skill)
    graph.add_node("store_skill", store_skill)
    graph.add_node("respond", respond)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "memory_lookup")
    graph.add_edge("memory_lookup", "route")

    graph.add_conditional_edges(
        "route",
        should_forge,
        {
            "forge": "forge_skill",
            "execute": "respond",
        }
    )

    graph.add_edge("forge_skill", "validate_skill")
    graph.add_edge("validate_skill", "store_skill")
    graph.add_edge("store_skill", "respond")
    graph.add_edge("respond", END)

    # MongoDB checkpointer — persists state across restarts
    checkpointer = MongoDBSaver.from_conn_string(MONGODB_URI, db_name=MONGODB_DB)
    return graph.compile(checkpointer=checkpointer)

app = build_graph()
```

---

## agent/nodes/memory_lookup.py

```python
from memory.search import embed_and_search
from agent.state import MediMindState

async def memory_lookup(state: MediMindState) -> MediMindState:
    results = await embed_and_search(state["transcript"])
    best_score = results[0]["score"] if results else 0.0
    return {
        **state,
        "matched_skills": results,
        "best_score": best_score,
    }
```

---

## memory/search.py

```python
import voyageai
from memory.client import get_collection
from config import VOYAGE_API_KEY, VOYAGE_MODEL, ATLAS_SEARCH_INDEX, SKILL_MATCH_THRESHOLD

voyage = voyageai.AsyncClient(api_key=VOYAGE_API_KEY)

async def embed_and_search(text: str, top_k: int = 3) -> list[dict]:
    result = await voyage.embed([text], model=VOYAGE_MODEL)
    embedding = result.embeddings[0]

    collection = get_collection("skills")
    pipeline = [
        {
            "$vectorSearch": {
                "index": ATLAS_SEARCH_INDEX,
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k,
            }
        },
        {
            "$project": {
                "id": 1,
                "name": 1,
                "code": 1,
                "description": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(top_k)
    return results
```

---

## memory/store.py

```python
from datetime import datetime
from memory.client import get_collection
from schemas.skill import Skill
import voyageai
from config import VOYAGE_API_KEY, VOYAGE_MODEL

voyage = voyageai.AsyncClient(api_key=VOYAGE_API_KEY)

async def store_skill(state: dict) -> dict:
    code = state.get("forged_code", "")
    description = state.get("transcript", "")

    emb = await voyage.embed([description], model=VOYAGE_MODEL)
    embedding = emb.embeddings[0]

    skill_id = f"PT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    skill = Skill(
        id=skill_id,
        name=f"Auto-forged: {description[:60]}",
        description=description,
        code=code,
        embedding=embedding,
        trigger_conditions=description.lower().split()[:5],
        validation_score=state.get("forge_validation_score", 0.0),
    )

    collection = get_collection("skills")
    await collection.insert_one(skill.to_dict())

    return {**state, "new_skill_id": skill_id}

async def store_session(session: dict):
    collection = get_collection("sessions")
    await collection.insert_one(session)
```

---

## forge/forge.py

```python
import httpx
from forge.prompts import build_forge_prompt
from agent.state import MediMindState
from config import FIREWORKS_API_KEY, FIREWORKS_CODE_MODEL, FORGE_MAX_RETRIES

async def forge_skill(state: MediMindState) -> MediMindState:
    retries = state.get("forge_retries", 0)
    if retries >= FORGE_MAX_RETRIES:
        return {**state, "forged_code": None}

    prompt = build_forge_prompt(state["transcript"], state["matched_skills"])

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.fireworks.ai/inference/v1/chat/completions",
            headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}"},
            json={
                "model": FIREWORKS_CODE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.2,
            },
            timeout=30,
        )

    code = response.json()["choices"][0]["message"]["content"].strip()
    # Strip markdown fences if present
    code = code.replace("```python", "").replace("```", "").strip()

    return {
        **state,
        "forged_code": code,
        "forge_triggered": True,
        "forge_retries": retries + 1,
    }
```

---

## forge/prompts.py

```python
def build_forge_prompt(transcript: str, partial_matches: list) -> str:
    partial_context = ""
    if partial_matches:
        partial_context = "\n\nClosest existing protocols for context:\n"
        for m in partial_matches[:2]:
            partial_context += f"- {m.get('name')}: {m.get('description')}\n"

    return f"""You are a clinical operations coordination system.

A workflow gap has been detected. No existing protocol covers this situation.

Gap description:
{transcript}
{partial_context}

Write a single Python async function called `coordinate(patient_id: str, ward: str, **kwargs)` that:
1. Coordinates the operational steps implied by the gap description
2. Sends notifications to the correct departments or staff roles
3. Tracks confirmation of each step
4. Returns a dict with keys: steps_initiated, expected_confirmations, escalation_after_minutes

Rules:
- No medical decisions, diagnoses, or clinical recommendations
- Only operational coordination: who to notify, what to track, when to escalate
- Return only valid Python code, no explanations, no markdown fences

```python
async def coordinate(patient_id: str, ward: str, **kwargs) -> dict:
```"""
```

---

## forge/validator.py

```python
import json
import boto3
from agent.state import MediMindState
from config import AWS_LAMBDA_FUNCTION, AWS_REGION, FORGE_PASS_SCORE

lambda_client = boto3.client("lambda", region_name=AWS_REGION)

async def validate_skill(state: MediMindState) -> MediMindState:
    if not state.get("forged_code"):
        return state

    payload = {
        "code": state["forged_code"],
        "test_cases": _load_synthetic_cases(),
    }

    response = lambda_client.invoke(
        FunctionName=AWS_LAMBDA_FUNCTION,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )

    result = json.loads(response["Payload"].read())
    score = result.get("score", 0.0)

    if score >= FORGE_PASS_SCORE:
        return {**state, "forge_validation_score": score}
    else:
        # Retry — route back through forge
        return {**state, "forge_validation_score": score, "forged_code": None}

def _load_synthetic_cases() -> list:
    with open("tests/synthetic_cases/transfer_cases.json") as f:
        return json.load(f)
```

---

## voice/gateway.py

```python
from livekit import rtc
from voice.transcribe import transcribe_audio
from config import LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET

async def run_voice_gateway(on_transcript):
    """
    Connects to LiveKit room, streams audio,
    calls on_transcript(text) for each utterance.
    """
    room = rtc.Room()

    @room.on("track_subscribed")
    async def on_track(track, publication, participant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            audio_stream = rtc.AudioStream(track)
            buffer = []
            async for frame in audio_stream:
                buffer.append(frame)
                if len(buffer) >= 50:  # ~1 second of audio
                    text = await transcribe_audio(buffer)
                    if text.strip():
                        await on_transcript(text)
                    buffer = []

    token = _generate_token()
    await room.connect(LIVEKIT_URL, token)

def _generate_token() -> str:
    from livekit import api
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_grants(api.VideoGrants(room_join=True, room="MediMind-ward"))
    return token.to_jwt()
```

---

## voice/speak.py

```python
import httpx
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

async def speak(text: str) -> bytes:
    """Convert text to speech via ElevenLabs and return audio bytes."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                },
            },
            timeout=15,
        )
        return response.content
```

---

## server.py

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from agent.orchestrator import app as agent
from voice.gateway import run_voice_gateway
import asyncio
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start voice gateway on startup
    asyncio.create_task(run_voice_gateway(handle_transcript))
    yield

app = FastAPI(lifespan=lifespan, title="MediMind Clinical Operations")

async def handle_transcript(text: str):
    session_id = f"shift_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    initial_state = {
        "session_id": session_id,
        "transcript": text,
        "embedding": [],
        "matched_skills": [],
        "best_score": 0.0,
        "forge_triggered": False,
        "forged_code": None,
        "forge_retries": 0,
        "new_skill_id": None,
        "response_text": "",
        "spoken": False,
    }
    await agent.ainvoke(initial_state, config=config)

@app.get("/health")
async def health():
    return {"status": "running", "agent": "MediMind"}

@app.get("/skills/count")
async def skill_count():
    from memory.client import get_collection
    count = await get_collection("skills").count_documents({})
    return {"total_skills": count}
```

---

## .env.example

```bash
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGODB_DB=MediMind
ATLAS_SEARCH_INDEX=skill_index

VOYAGE_API_KEY=
FIREWORKS_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-west-2
AWS_LAMBDA_FUNCTION=MediMind-skill-validator

LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=MediMind
```

---

## pyproject.toml

```toml
[project]
name = "MediMind"
version = "0.1.0"
description = "Clinical operations intelligence — always on"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.111",
    "uvicorn>=0.29",
    "langgraph>=0.1",
    "langchain>=0.2",
    "langchain-mongodb>=0.1",
    "motor>=3.4",
    "pymongo>=4.7",
    "voyageai>=0.2",
    "elevenlabs>=1.0",
    "livekit>=0.11",
    "livekit-api>=0.6",
    "boto3>=1.34",
    "httpx>=0.27",
    "python-dotenv>=1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
]
```

---

## Atlas vector search index

Create this index on the `skills` collection in Atlas:

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "dimensions": 1024,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```

Index name: `skill_index`
Collection: `skills`
Database: `MediMind`
