# MediMind 🔥
### Clinical Operations Intelligence — Always On

> An always-on voice agent that coordinates hospital workflows, detects operational gaps in real time, and autonomously forges new coordination protocols when it encounters situations it has never seen before.

Built for the **MongoDB Agentic Evolution Hackathon** · London · May 2026

---

## What it does

MediMind listens to clinical staff by voice throughout a hospital shift. When a coordinator, nurse, or on-call doctor speaks a workflow request — a discharge chain, a missing specimen, a blocked bed — it acts immediately: routing notifications, tracking confirmations, and escalating automatically when something stalls.

When it encounters a workflow it has never handled before, it doesn't fail. It builds a new coordination protocol on the fly, validates it, and stores it permanently in MongoDB Atlas — available to every hospital on the network from that moment on.

**The system never gives medical advice. It coordinates operational people: who needs to act, when, and where.**

---

## Hackathon theme

**Prolonged Coordination** — multi-step workflows lasting an entire 12-hour hospital shift, enduring failures and restarts, with MongoDB Atlas as the persistent context engine.

Secondary: **Adaptive Retrieval** — the skill forge learns and improves over time, retrieval improves with every new protocol stored.

---

## Tech stack

| Layer | Service | Role |
|---|---|---|
| Voice in | LiveKit | Real-time audio capture from clinical staff |
| Transcription | Fireworks AI (Whisper) | Speech to text |
| Orchestration | LangGraph | State machine, conditional routing |
| State persistence | MongoDB Atlas + LangSmith checkpointer | Shift-long memory, survives restarts |
| Memory retrieval | MongoDB Atlas Vector Search | Finds matching protocols by semantic similarity |
| Embeddings | Voyage AI | Encodes workflow descriptions |
| Skill forge | Fireworks AI | Generates new coordination code when gap detected |
| Sandbox validation | AWS Lambda | Tests forged skills before committing |
| Protocol store | MongoDB Atlas | Persists all skills, sessions, state |
| Voice out | ElevenLabs | Speaks responses back to clinical staff |
| Always-on runtime | NVIDIA NemoClaw | Keeps all agents alive across the full shift |

---

## Agent flow

```
Voice input (LiveKit)
        │
        ▼
Transcribe (Fireworks AI Whisper)
        │
        ▼
Agent orchestrator (LangGraph state machine)
        │
        ▼
Atlas vector search (Voyage AI embeddings)
        │
   ┌────┴────┐
skill     skill
found      gap
   │         │
   ▼         ▼
Execute    Forge new skill
skill      (Fireworks AI)
   │         │
   │         ▼
   │    Sandbox test
   │    (AWS Lambda)
   │         │
   │         ▼
   │    Store protocol
   │    (MongoDB Atlas)
   │         │
   └────┬────┘
        │
        ▼
Voice response (ElevenLabs)
```

---

## Real-world use cases

**1. Discharge chain** — Doctor signs discharge. MediMind simultaneously notifies pharmacy, porter, cleaner, and bed manager. Tracks each confirmation. Escalates automatically if any step stalls past its time window.

**2. Missing specimen** — Blood drawn 4 hours ago, lab has no record. MediMind traces every logged handoff, identifies the exact break in the chain, routes a task to the right person to physically check that location.

**3. Shift handover gaps** — Shift ends in 20 minutes. MediMind cross-checks which beds have open tasks against what's been documented. Sends specific messages: "Bed 9 — pending cannula change not handed over."

**4. A&E backlog** — 8 patients waiting over 4 hours. MediMind identifies which are blocked purely on admin steps — bed assignment, a clerk action — and fires those tasks automatically.

**5. Equipment trace** — A specialist IV pump last logged in Ward 4. Ward 6 needs it. MediMind traces the log, sends a retrieval request to the nearest staff member, initiates transport.

**6. Consultant sequencing** — Three departments bleep the same consultant simultaneously. MediMind sequences by urgency, estimates travel time between locations, sends each department a realistic ETA.

**7. Unreviewed critical result** — Lab result came back 3 hours ago, no acknowledgement. MediMind escalates to the duty doctor and logs the escalation.

**8. Pre-op checklist** — Surgery in 2 hours. Consent signed, anaesthetic review missing, blood sample outstanding. MediMind bleeps anaesthetist and night nurse simultaneously, not sequentially.

**9. ITU bed chain** — ITU needs a bed. MediMind maps the full dependency chain across ITU → HDU → ward, monitors the triggering discharge, and fires the step-down sequence the moment the ward bed is confirmed free.

**10. The forge** — A workflow MediMind has never seen: emergency inter-site equipment transfer requiring ambulance, receiving hospital notification, records transfer, next-of-kin contact, and bed confirmation simultaneously. No protocol exists. MediMind builds one live, validates it against synthetic test cases, stores it. Available to every connected hospital instantly.

---

## Who talks to MediMind

**Nurses** — by voice, hands-free, mid-procedure.
*"MediMind, bed 9 cannula change still hasn't been done, chase it."*

**On-call doctors** — by voice, on the move between wards.
*"MediMind, what's outstanding on my list right now?"*

**Ward coordinators / bed managers** — by voice or text, with the fullest picture.
*"Show me everything waiting more than two hours."*

MediMind never speaks directly to patients. It notifies other operational staff (pharmacy, porters, bed managers, radiologists) via bleep integration, SMS, or app notification — they don't need to interact with the system directly.

---

## MongoDB Atlas — what lives there

### Collection: `skills`
```json
{
  "id": "PT-2847",
  "name": "Post-chemo discharge coordination",
  "description": "Coordinates pharmacy, oncology nurse, and transport for post-chemotherapy discharge",
  "code": "def coordinate_discharge(patient_id, ward): ...",
  "embedding": [0.023, -0.187, ...],
  "trigger_conditions": ["discharge", "chemotherapy", "pharmacy"],
  "validation_score": 0.91,
  "usage_count": 14,
  "created_at": "2026-05-02T10:34:00Z",
  "trust_origin": "NHS_UCLH"
}
```

### Collection: `sessions`
```json
{
  "session_id": "shift_20260502_ward7b",
  "transcript": "Bed 12 discharge signed, pharmacy not notified",
  "matched_skills": ["PT-0043"],
  "forge_triggered": false,
  "response_text": "Notifying pharmacy, porter, and bed manager simultaneously.",
  "timestamp": "2026-05-02T14:22:00Z"
}
```

### Collection: `tasks`
```json
{
  "task_id": "T-9921",
  "type": "discharge_chain",
  "bed": "12",
  "ward": "7B",
  "steps": ["pharmacy", "porter", "cleaner", "bed_manager"],
  "confirmations": {"pharmacy": true, "porter": false},
  "created_at": "2026-05-02T14:22:00Z",
  "escalate_after_minutes": 20
}
```

---

## Project structure

```
MediMind/
├── README.md
├── .env.example
├── pyproject.toml
│
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py       # LangGraph state machine — 4 nodes
│   ├── state.py              # TypedDict for agent state
│   └── nodes/
│       ├── ingest.py         # Receives transcript, builds context
│       ├── memory_lookup.py  # Atlas vector search via Voyage AI
│       ├── route.py          # Conditional edge: execute vs forge
│       └── respond.py        # Builds response, triggers voice out
│
├── memory/
│   ├── __init__.py
│   ├── client.py             # MongoDB Atlas connection
│   ├── search.py             # embed_and_search() — Voyage AI + Atlas
│   └── store.py              # store_skill(), store_session()
│
├── forge/
│   ├── __init__.py
│   ├── forge.py              # Fireworks AI code generation
│   ├── validator.py          # AWS Lambda sandbox test
│   └── prompts.py            # Prompt templates for skill generation
│
├── voice/
│   ├── __init__.py
│   ├── gateway.py            # LiveKit audio stream → transcript
│   ├── transcribe.py         # Fireworks AI Whisper endpoint
│   └── speak.py              # ElevenLabs TTS → LiveKit out
│
├── schemas/
│   ├── skill.py              # Skill document schema
│   ├── session.py            # Session document schema
│   └── task.py               # Task document schema
│
├── server.py                 # FastAPI entry point
├── config.py                 # Env vars, constants
└── tests/
    ├── synthetic_cases/      # JSON test cases for Lambda validator
    ├── test_forge.py
    └── test_memory.py
```

---

## Environment variables

```bash
# MongoDB Atlas
MONGODB_URI=mongodb+srv://...
MONGODB_DB=MediMind
ATLAS_SEARCH_INDEX=skill_index

# Voyage AI
VOYAGE_API_KEY=...

# Fireworks AI
FIREWORKS_API_KEY=...
FIREWORKS_MODEL=accounts/fireworks/models/whisper-v3

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_LAMBDA_FUNCTION=MediMind-skill-validator
AWS_REGION=eu-west-2

# LiveKit
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# ElevenLabs
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# LangSmith
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
```

---

## Build order for the day

```
Hour 1  (10:30–11:30)  schemas.py + memory/ — get Atlas talking first
Hour 2  (11:30–12:30)  agent/orchestrator.py — stub all 4 nodes, wire LangGraph
Hour 3  (12:30–13:00)  voice/gateway.py — LiveKit → Fireworks transcription
--- Lunch ---
Hour 4  (13:30–14:30)  forge/forge.py + forge/validator.py — skill forge + Lambda
Hour 5  (14:30–15:30)  voice/speak.py — ElevenLabs response loop
Hour 6  (15:30–16:30)  end-to-end demo test, fix breakages
Hour 7  (16:30–17:00)  demo polish, record 1-min video, submit
```

---

## Demo script (3 minutes)

**0:00–0:30** — Speak a known workflow: *"MediMind, bed 12 discharge signed, pharmacy not notified."* Show Atlas retrieval finding Protocol PT-0043. Show voice response confirming action taken.

**0:30–1:30** — Speak a novel workflow: *"MediMind, patient in bed 6 needs emergency transfer to UCLH with equipment, records, and transport all coordinated."* Show forge triggered. Show Fireworks generating code. Show Lambda validating. Show new protocol committed to Atlas.

**1:30–2:30** — Show the Atlas dashboard: Protocol PT-0001 now exists. Ask the same request again — this time it retrieves instantly. Show the skill growing.

**2:30–3:00** — Pitch line: *"Every hospital using MediMind makes it smarter for every other hospital. The system that starts the shift knowing 800 protocols ends it knowing 850."*

---

## Judging criteria mapping

| Criterion | Weight | How MediMind hits it |
|---|---|---|
| Live demo | 45% | Voice in → forge live on stage → skill stored → retrieved instantly |
| Creativity & originality | 35% | Self-forging clinical coordination agent — not seen before |
| Impact potential | 20% | NHS operational failures cost billions, affect patient outcomes |

**ElevenLabs bonus track** — voice is core, not decorative. Every single response goes through ElevenLabs.

---

## Team

Raafi Riyaz — MSc AI, City University of London · Co-Founder FeedHire · ML Engineer Mercor
[LinkedIn](https://linkedin.com/in/) · [GitHub](https://github.com/) · [Portfolio](https://rafa.works)

---

## Submission checklist

- [ ] Repository is public
- [ ] Built on MongoDB Atlas hackathon sandbox
- [ ] Demo video under 1 minute uploaded
- [ ] All team members added to submission page
- [ ] ElevenLabs project submitted to showcase.elevenlabs.io
- [ ] LangSmith tracing enabled and visible
