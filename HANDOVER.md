# MediMind — Hackathon Handover

> **For the next agent / future-me picking this up mid-day.** Read this first. It is the single source of truth for state, decisions, and what to do next. Updated incrementally as work progresses.

---

## TL;DR

- **Event**: MongoDB Agentic Evolution Hackathon — London, **Saturday 2026-05-02**
- **Submissions due**: 17:00 BST (judging 17:15–18:45)
- **Project**: MediMind — always-on clinical operations voice agent
- **Theme**: Prolonged Coordination (primary) + Adaptive Retrieval (secondary)
- **Solo build**. User: Raafi Riyaz (`rafa.works313@gmail.com`)
- **Plan file (read for full context)**: `/Users/rafa/.claude/plans/lests-start-wiht-the-tingly-treehouse.md`

## Source of truth docs

- [Readme.md](Readme.md) — partner credits + raw setup notes
- [hackathon_docs/hackathon_details.md](hackathon_docs/hackathon_details.md) — official rules, schedule, judging criteria, anti-projects
- [claude_sonnet_planned_files/README.md](claude_sonnet_planned_files/README.md) — full project pitch + demo script
- [claude_sonnet_planned_files/CODE_STRUCTURE.md](claude_sonnet_planned_files/CODE_STRUCTURE.md) — **detailed file-by-file code stubs** (we are scaffolding from this)
- [claude_sonnet_planned_files/FLOW.md](claude_sonnet_planned_files/FLOW.md) — agent flow diagrams + state machine

## Architecture (one paragraph)

Voice in via **LiveKit** → transcribe via **Fireworks Whisper** → **LangGraph** state machine (4 nodes: ingest → memory_lookup → route → respond) checkpointed to **MongoDB Atlas** via the LangGraph MongoDB checkpointer. Memory_lookup runs Atlas Vector Search over a `skills` collection embedded with **Voyage AI** (voyage-3, 1024 dim). If `best_score >= 0.78` → execute matched skill → respond. If below → forge new skill via **Fireworks** code-gen → validate in **AWS Lambda** sandbox against synthetic cases → store the new skill back into Atlas → respond. Voice out via **ElevenLabs** streamed back through LiveKit. The whole point of the demo: forge a novel skill live, then re-ask it and watch the cache hit.

## Confirmed user decisions

- Atlas hackathon **sandbox is ready** — use sandbox cluster as `MONGODB_URI` from hour 1, NOT the personal `cluster0.bbhger` cluster. Personal cluster URI is only a fallback.
- **Solo** build. Keep LiveKit and AWS Lambda in scope.
- Sticking with **MediMind** (no pivot).
- Free to deviate from the planned file layout where it speeds things up.

## Critical compliance constraints

- Repo **must be public** before submission ([rules](hackathon_docs/hackathon_details.md#L143))
- Build **must be in the MongoDB Atlas hackathon sandbox** to be eligible for finalist judging ([rules](hackathon_docs/hackathon_details.md#L139-L141))
- Anti-project: "Any project using AI to generate and give medical advice" is banned. **MediMind frames itself as operational coordination only — never medical advice.** This needs one prominent line in README and the demo script's opening.
- Demo video must be ≤1 minute and show *only* what was built today.

## What we have (assets)

- AWS credits (free-tier guide PDF in `hackathon_docs/`)
- LangSmith credits
- ElevenLabs Creator tier
- LiveKit $50 credits
- Fireworks AI $5 credits
- MongoDB personal cluster: `mongodb+srv://raafi:<db_password>@cluster0.bbhger.mongodb.net/`
- Sandbox cluster: **awaiting connection string from user**

## What we need (still missing — ask user if not yet provided)

| Var | Status | Notes |
|---|---|---|
| `MONGODB_URI` (sandbox) | ⏳ awaiting from user | use sandbox, not personal |
| `VOYAGE_API_KEY` | ⏳ | required for embeddings |
| `FIREWORKS_API_KEY` | ⏳ | for Whisper + code-gen |
| `LIVEKIT_URL` | ⏳ | wss://... |
| `LIVEKIT_API_KEY` | ⏳ | |
| `LIVEKIT_API_SECRET` | ⏳ | |
| `ELEVENLABS_API_KEY` | ⏳ | |
| `ELEVENLABS_VOICE_ID` | ⏳ | pick a voice from their library |
| `LANGCHAIN_API_KEY` | ⏳ | for tracing + checkpointer |
| `AWS_ACCESS_KEY_ID` | ⏳ | for Lambda invoke |
| `AWS_SECRET_ACCESS_KEY` | ⏳ | |
| `AWS_REGION` | default `eu-west-2` | confirm with user |

## Build order (from plan §3)

| Hour | Window | Block |
|---|---|---|
| Pre | →10:30 | Setup: keys, repo public, Atlas DB + vector index |
| 1 | 10:30–11:30 | Atlas + memory layer + seed skills |
| 2 | 11:30–12:30 | LangGraph orchestrator + nodes |
| 3 | 12:30–13:00 | Voice in (LiveKit + Fireworks Whisper) |
| — | 13:00–13:30 | Lunch |
| 4 | 13:30–14:30 | Forge + AWS Lambda validator |
| 5 | 14:30–15:30 | Voice out (ElevenLabs through LiveKit) |
| 6 | 15:30–16:30 | End-to-end rehearsal + dashboard endpoints |
| 7 | 16:30–17:00 | Record video, submit |

## Fallback plan if behind

- **14:00 slipping**: drop LiveKit. Take transcripts via `POST /transcript`. Voice = stretch goal.
- **15:30 slipping**: stub `validate_skill` to return fixed `score=0.85`. The "forge → store" demo still works without a real Lambda.
- **16:00 slipping**: skip live voice out, narrate over the dashboard.
- **Always preserve**: forge → store in Atlas → instantly retrievable. That is the whole pitch.

## Atlas setup (do this in the sandbox UI)

1. Database: `MediMind`
2. Collections: `skills`, `sessions`, `tasks`, plus `checkpoints` (LangGraph will create these)
3. Vector search index on `skills.embedding`:
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
   Index name: `skill_index`. Build takes ~1–2 min.

## File layout being built

```
mongodb_hackathon/
├── HANDOVER.md            # ← this file
├── Readme.md              # ← user's setup notes
├── pyproject.toml
├── .env.example
├── .env                   # local only, NEVER commit
├── .gitignore
├── config.py
├── server.py              # FastAPI entrypoint
├── seed_skills.py         # one-shot Atlas seeder
│
├── agent/
│   ├── __init__.py
│   ├── state.py
│   ├── orchestrator.py
│   └── nodes/
│       ├── __init__.py
│       ├── ingest.py
│       ├── memory_lookup.py
│       ├── route.py
│       └── respond.py
│
├── memory/
│   ├── __init__.py
│   ├── client.py
│   ├── search.py
│   └── store.py
│
├── forge/
│   ├── __init__.py
│   ├── forge.py
│   ├── prompts.py
│   └── validator.py
│
├── voice/
│   ├── __init__.py
│   ├── gateway.py
│   ├── transcribe.py
│   └── speak.py
│
├── schemas/
│   ├── __init__.py
│   ├── skill.py
│   ├── session.py
│   └── task.py
│
├── tests/
│   └── synthetic_cases/
│       └── transfer_cases.json
│
├── claude_sonnet_planned_files/   # planning artifacts (don't ship)
└── hackathon_docs/                # rules + AWS guide
```

## Verification gates (don't move on without these passing)

1. After memory layer: `python seed_skills.py` writes ≥3 skills to Atlas with embeddings, then a smoke script returns top-K matches with scores.
2. After agent layer: `python -c "import asyncio; from agent.orchestrator import app; ..."` runs `ainvoke` end-to-end and returns non-empty `response_text`.
3. After voice in: speaking into the LiveKit room produces a transcript event hitting `handle_transcript`.
4. After forge: a never-seen-before transcript creates a new doc in `skills` within ~10s and the second invocation hits it.
5. After voice out: ElevenLabs voice replies in the LiveKit room.
6. End-to-end rehearsal: 3-min demo runs cleanly twice in a row.

## Status log (update in place as we work)

> Newest entries at the top. Write a one-line status when starting AND finishing each major step.

- **Done** — Hour 1 + 2 + (most of) the rest scaffolded in one push: full file tree under [agent/](agent/), [memory/](memory/), [forge/](forge/), [voice/](voice/), [schemas/](schemas/), plus [server.py](server.py), [seed_skills.py](seed_skills.py), [SETUP.md](SETUP.md). All Python parses, all imports resolve, the LangGraph compiles, and `seed_skills.py` ran successfully — **5 seed skills now in Atlas with Voyage embeddings**.
- **Done** — Plan written and approved. Handover doc created. Todos initialised.

## Known issues / next steps (in order)

1. **Atlas vector index** — must be created in the sandbox UI before vector search returns anything. Spec is in [SETUP.md](SETUP.md) §4. Without this the agent will route to forge for everything (zero matches).
2. **ElevenLabs keys** — not in `.env` yet. Voice OUT will fail silently if the agent tries to speak. Submit the form (https://forms.gle/HeTS12ahZPXMvpRT6) and pick a voice ID.
3. **MONGODB_DB / ATLAS_SEARCH_INDEX / LIVEKIT_ROOM** — defaults work via [config.py](config.py), but worth checking they match what's actually in the sandbox.
4. **AWS Lambda validator** — not deployed. The local fallback in [forge/validator.py](forge/validator.py) (`_local_validate`) does an AST + shape check which is enough for the demo. Lambda is a stretch goal.
5. **End-to-end smoke test**: once the vector index is *Active*, run the curl sequence in [SETUP.md](SETUP.md) §6 to verify the full graph.
6. **Public GitHub repo** + first commit — required before submission. Currently the repo is local only.

## Quick commands cheat-sheet

```bash
# Install deps
uv sync

# Seed Atlas (after vector index is Active)
uv run python seed_skills.py

# Run the server (auto-starts the LiveKit voice gateway if LIVEKIT_URL set)
uv run uvicorn server:app --reload --port 8000

# Smoke test without voice
curl http://localhost:8000/health
curl -X POST http://localhost:8000/transcript \
  -H 'content-type: application/json' \
  -d '{"text":"Bed 12 discharge signed, pharmacy not notified yet."}'
```

## How to resume if I'm a new agent

1. Read this file fully.
2. Read the plan: `/Users/rafa/.claude/plans/lests-start-wiht-the-tingly-treehouse.md`
3. Skim [claude_sonnet_planned_files/CODE_STRUCTURE.md](claude_sonnet_planned_files/CODE_STRUCTURE.md) for the file stubs we're working from.
4. Run `git status` and `git log --oneline -20` to see what's already been committed.
5. Check the **Status log** above for the most recent work.
6. Check the user's `.env` (do not commit) — if keys are missing, ask the user before making API calls.
7. Continue from the next unchecked item in the build order.
8. **Time check**: anything past 16:00 BST means switch to the §6 fallback plan (above) and prioritise submission over polish.
