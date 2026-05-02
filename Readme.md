# Setup and partner Info

## Demo

[![MediMind demo](https://img.youtube.com/vi/Gq2BRdwdMVs/maxresdefault.jpg)](https://youtu.be/Gq2BRdwdMVs)

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


=====
- Must build project in MongoDB ATlas hackathon sandbox

what i have ready

AWS credits
Langsmith credits
eleven labs - Creator accountcredits
livekit -  $50 credits
MongoDB cluster setup - mongodb+srv://raafi:<db_password>@cluster0.bbhger.mongodb.net/?appName=Cluster0
Fireworks AI $5 credits




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

---

If you want, I can **trim this to exactly match hackathon judging criteria (e.g., MongoDB + LiveKit only)** or turn it into a **1-slide pitch diagram**.



#run command
uv run python voice/medimind_agent.py dev 