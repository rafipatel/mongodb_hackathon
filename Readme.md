# MediMind ![Honourable Mention — MongoDB Hackathon, London](https://img.shields.io/badge/MongoDB_Hackathon_London-Honourable_Mention-FFD700?style=flat-square&logo=mongodb&logoColor=white&labelColor=13AA52)

## Demo (click the image below to view video)

[![MediMind demo](https://img.youtube.com/vi/Gq2BRdwdMVs/maxresdefault.jpg)](https://youtu.be/Gq2BRdwdMVs)


## MediMind

Imagine coordinating a ward **hands-free**: you speak, the system listens, remembers, and acts—routing reminders, protocols, and staff-facing workflows without touching a keyboard. That is MediMind: a voice-first ops coordinator for clinical operations only (**never** diagnosis or medical advice). It was forged for the MongoDB Agentic Evolution Hackathon as a story about **Prolonged Coordination** and **Adaptive Retrieval**—an agent that survives real shifts, not just tidy demos.

The friction MediMind bites into is older than software:

> Hospitals are giant async distributed systems run by humans on phones.
>
> When something off-script happens, the senior nurse becomes a manual message broker — calling 5 different teams in the right order, from memory, while also caring for the patient.
>
> There's no service registry, no event bus, no retry logic. Just a bleep and good luck.

MediMind is a small rebellion against that pattern. After you confirm a protocol, it **fans out coordination in parallel**: every step can hit the channels your workflow defines—bleeps, secure apps, dashboards, radios, **Discord** alerts, and more—so associated staff get signal **at the same time**, not chained through one exhausted human acting as the only bus.

MediMind treats memory as infrastructure. Speech rides **LiveKit**; **LangGraph** keeps reasoning alive with checkpoints written to **MongoDB Atlas**. **Atlas Vector Search**, fed by **Voyage** embeddings, finds the nearest matching skill in milliseconds—muscle memory for the ward. When nothing in the library fits, the stack does something bolder: **Fireworks** drafts a new coordination skill, **AWS Lambda** stress-tests it, Atlas stores it, and the next nurse asking the same question gets an instant hit—no redeploy, no midnight engineer—just an agent that gets sharper every time reality throws a curveball.



MongoDB
AWS lambda 
voyage AI

https://github.com/livekit-examples/mongodb-hacker-starter
https://github.com/livekit/agent-skills

Langchain ecosystem

- deepagents
- langchain
- langgraph


MongoDB x LangChain
- Atlas vector search
- MongDV checkpointer in Langsmits
- Text to MQL


---
Quick Start for Hackathon

- Setup
- Templates
- deploy
- Iterate


## 🧠 Partner Services Overview

## 🔹 MongoDB Atlas

* **Operational Data**
  Stores skills, sessions, notifications using async Motor clients
  → `memory/client.py`, `memory/store.py`, `seed_skills.py`

* **Vector Search**
  Uses Atlas Search index (`ATLAS_SEARCH_INDEX`, default: `skill_index`)
  for semantic retrieval of skill embeddings
  → `memory/search.py`, `scripts/ensure_vector_index.py`

* **LangGraph Checkpoints**
  Persists agent state using `MongoDBSaver`
  → `agent/orchestrator.py`

* **Health Monitoring**
  `/health` endpoint checks index status
  → `server.py`

---

## 🔹 Voyage AI

* **Embeddings**

  * Query embeddings for semantic search
  * Document embeddings for stored skills
    → `memory/search.py`

* Uses:

  * `voyageai.AsyncClient`
  * Config: `VOYAGE_MODEL`, `VOYAGE_DIM`

---

## 🔹 Fireworks AI

* **Speech-to-Text (Gateway Path)**
  Whisper-style transcription
  → `voice/transcribe.py`
  (`FIREWORKS_WHISPER_MODEL`)

* **Code Generation (Forge)**
  Generates new skill code using chat completions
  → `forge/forge.py`
  (`FIREWORKS_CODE_MODEL`)

---

## 🔹 AWS Lambda

* **Skill Validation**

  * Remote validation of generated code via `boto3`
  * Uses:

    * `AWS_LAMBDA_FUNCTION`
    * `AWS_REGION`

* **Fallback Mode**

  * If AWS credentials not set → local syntax validation
    → `forge/validator.py`

---

## 🔹 LiveKit

* **Realtime Voice Room**

  * Browser connects via JWT (`/livekit/token`)
  * Handles room + agent dispatch
    → `voice/gateway.py`, `server.py`

* **Agent Worker**

  * Full-duplex voice pipeline:

    * Silero VAD
    * ElevenLabs STT/TTS
    * LangGraph via LangChain adapter
      → `voice/medimind_agent.py`

* **Optional Gateway**

  * Separate participant handling:

    * Audio → Fireworks Whisper → callbacks

---

## 🔹 ElevenLabs

* **Voice Agent**

  * STT + TTS inside LiveKit worker
    → `voice/medimind_agent.py`

* **Audio Output**

  * Streams MP3 for:

    * UI playback
    * Discord notifications
      → `voice/speak.py`, `/speak`, `notifications/dispatcher.py`

---

## 🔹 Discord

* **Outbound Alerts**

  * Sends webhook notifications for protocol runs
  * Includes:

    * Text updates
    * Optional TTS MP3 attachment
      → `notifications/dispatcher.py`

---

# ⚡ Quick Mental Model

| Service           | Role in Product                             |
| ----------------- | ------------------------------------------- |
| **MongoDB Atlas** | Data storage + vector search + agent memory |
| **Voyage AI**     | Embeddings → “What protocol fits this?”     |
| **Fireworks AI**  | Transcription + code generation             |
| **AWS Lambda**    | Validation layer for generated code         |
| **LiveKit**       | Real-time voice + agent runtime             |
| **ElevenLabs**    | Speech input/output                         |
| **Discord**       | Notifications for staff                     |




#run command
uv run python voice/medimind_agent.py dev 
