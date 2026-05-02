# MediMind — Agent Flow

## Full system flow

```mermaid
flowchart TD
    A["🎙️ Voice input\nLiveKit real-time audio"]
    B["📝 Transcribe\nFireworks AI Whisper"]
    C["🧠 Agent orchestrator\nLangGraph · MongoDB checkpointer"]
    D["🔍 Atlas vector search\nVoyage AI embeddings"]
    E{"Skill match?"}
    F["✅ Execute skill\nRun stored protocol"]
    G["⚡ Forge new skill\nFireworks AI code gen"]
    H["🧪 Sandbox test\nAWS Lambda · validate"]
    I["💾 Store protocol\nMongoDB Atlas · persist"]
    J["🔊 Voice response\nElevenLabs · speech out"]

    A --> B --> C --> D --> E
    E -- skill found --> F
    E -- skill gap --> G
    G --> H --> I
    F --> J
    I --> J

    style G fill:#a78bfa,color:#1e0a4a
    style H fill:#a78bfa,color:#1e0a4a
    style I fill:#a78bfa,color:#1e0a4a
    style A fill:#1d9e75,color:#04342c
    style B fill:#1d9e75,color:#04342c
    style J fill:#1d9e75,color:#04342c
    style C fill:#888780,color:#f1efe8
    style D fill:#888780,color:#f1efe8
```

---

## What each node does

| Node | Service | What it actually does |
|---|---|---|
| Voice input | LiveKit | Opens a websocket, streams audio chunks from the clinician's mic in real time |
| Transcribe | Fireworks AI Whisper | Converts audio chunks to a transcript string, word-level timestamps |
| Agent orchestrator | LangGraph | State machine with 4 nodes: ingest → memory_lookup → route → respond. State persisted to MongoDB Atlas via LangSmith checkpointer — survives server restarts mid-shift |
| Atlas vector search | Voyage AI + MongoDB | Embeds the transcript, runs cosine similarity search against the skills collection. Returns top matches with scores |
| Skill match? | — | If best match score ≥ 0.78 → execute. If below → forge |
| Execute skill | — | Runs the stored Python coordination function. Sends notifications to the right people |
| Forge new skill | Fireworks AI | Generates a new Python coordination function from a structured prompt describing the gap |
| Sandbox test | AWS Lambda | Packages the forged function, runs it against 10 synthetic test cases stored in Atlas, scores outputs. Retries forge up to 3 times if score too low |
| Store protocol | MongoDB Atlas | Commits the validated function as a new skill document with Voyage AI embedding. Immediately available to all connected hospitals |
| Voice response | ElevenLabs | Converts response text to speech, streams back through LiveKit to the clinician |

---

## State machine detail

```mermaid
stateDiagram-v2
    [*] --> ingest
    ingest --> memory_lookup
    memory_lookup --> route
    route --> execute_skill : score ≥ 0.78
    route --> forge_skill : score < 0.78
    execute_skill --> respond
    forge_skill --> validate
    validate --> store : pass
    validate --> forge_skill : fail (retry ≤ 3)
    store --> respond
    respond --> [*]
```

---

## MongoDB Atlas — data model

```mermaid
erDiagram
    SKILLS {
        string id PK
        string name
        string description
        string code
        array embedding
        array trigger_conditions
        float validation_score
        int usage_count
        datetime created_at
        string trust_origin
    }

    SESSIONS {
        string session_id PK
        string transcript
        array matched_skills
        bool forge_triggered
        string response_text
        datetime timestamp
    }

    TASKS {
        string task_id PK
        string type
        string bed
        string ward
        array steps
        object confirmations
        int escalate_after_minutes
        datetime created_at
    }

    SESSIONS ||--o{ TASKS : creates
    SESSIONS }o--o{ SKILLS : matches
```

---

## Who communicates with MediMind

```mermaid
graph LR
    N["👩‍⚕️ Nurse\nvoice, hands-free"] -->|speaks| P["🔥 MediMind"]
    D["🩺 On-call doctor\nvoice, on the move"] -->|speaks| P
    C["📋 Coordinator\nvoice or text"] -->|speaks or types| P

    P -->|bleep| BL["📟 Bleep system"]
    P -->|SMS / app| PH["📱 Pharmacy\nPorters\nRadiology"]
    P -->|voice| SP["🔊 LiveKit speaker"]
    P -->|dashboard| DB["🖥️ Coordinator screen"]
```

---

## The forge pipeline (detail)

```
Transcript: "Patient in bed 6 needs emergency inter-site transfer
             with equipment, records, transport, and receiving
             bed confirmation — all simultaneously"
        │
        ▼
Atlas search: no match above threshold
        │
        ▼
Forge prompt to Fireworks AI:
  "Given this gap: [description]
   Write a Python async function that coordinates:
   - Ambulance transport booking
   - Receiving hospital notification
   - Medical records transfer
   - Next-of-kin contact
   - Bed confirmation at destination
   Return only valid Python. No explanations."
        │
        ▼
Fireworks returns: def coordinate_inter_site_transfer(patient_id, destination): ...
        │
        ▼
AWS Lambda: run against 10 synthetic patient transfer cases
  Score: 0.91 ✓
        │
        ▼
MongoDB Atlas: new document written
  id: "PT-0001"
  available to all connected NHS trusts immediately
        │
        ▼
ElevenLabs speaks:
  "No existing protocol for this transfer type.
   I've built and validated a new coordination workflow.
   Initiating now — ambulance, UCLH, records, and
   next-of-kin all contacted simultaneously."
```

---

## Always-on architecture

MediMind runs as a persistent process across the entire 12-hour hospital shift.

- **NemoClaw** keeps the agent alive with a single command, handling restarts automatically
- **MongoDB Atlas checkpointer** (via LangSmith) saves full agent state after every node — if the process crashes at step 3 of a 5-step coordination, it resumes from step 3
- **LangGraph** state machine recovers from partial failures without replaying completed steps
- **AWS Lambda** is stateless — forge validation is idempotent, safe to retry

The system starts the shift with however many protocols are in Atlas. It ends the shift with more. Every novel situation it handles becomes a permanent capability.
