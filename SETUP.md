# MediMind — local setup

## 1. Prereqs

- Python ≥ 3.11
- `uv` (or `pip`) for installs
- A MongoDB Atlas cluster with the **Vector Search** option enabled (the hackathon sandbox already has this)

## 2. Install

```bash
uv sync
# or, with pip:
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## 3. Fill `.env`

Copy `.env.example` to `.env` and fill in every key. Hard blockers:

- `MONGODB_URI` — point at the **hackathon sandbox** cluster
- `VOYAGE_API_KEY`
- `FIREWORKS_API_KEY`
- `LIVEKIT_URL` + key + secret (optional if you only use `/transcript`)
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` (optional for first end-to-end)
- `LANGCHAIN_API_KEY` (optional — enables tracing)
- AWS keys (optional — falls back to local validator if unset)

## 4. Atlas — create the vector index

In the Atlas UI for the `MediMind` database, open the `skills` collection → Search Indexes → Create Search Index → JSON editor:

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

Index name: **`skill_index`**. Wait ~1–2 min until the status is *Active*.

## 5. Seed the skills collection

```bash
uv run python seed_skills.py
```

Should print 5 upserts and a final count.

## 6. Smoke-test the agent (no voice)

```bash
uv run uvicorn server:app --reload --port 8000
```

Then in another shell:

```bash
# health
curl http://localhost:8000/health

# known workflow → should hit a seeded skill
curl -X POST http://localhost:8000/transcript \
  -H 'content-type: application/json' \
  -d '{"text":"Bed 12 discharge signed, pharmacy not notified yet."}'

# novel workflow → should forge a new skill
curl -X POST http://localhost:8000/transcript \
  -H 'content-type: application/json' \
  -d '{"text":"Patient in bed 6 needs emergency inter-site transfer to UCLH with ambulance, records, and bed confirmation simultaneously."}'

# count goes up
curl http://localhost:8000/skills/count

# repeat the novel one — it now hits the freshly-stored skill
curl -X POST http://localhost:8000/transcript \
  -H 'content-type: application/json' \
  -d '{"text":"Patient in bed 6 needs emergency inter-site transfer to UCLH with ambulance, records, and bed confirmation simultaneously."}'
```

## 7. Voice in/out

Get a join token:

```bash
curl 'http://localhost:8000/livekit/token?identity=clinician'
```

Use that token in the LiveKit Agents Playground (https://agents-playground.livekit.io) or the LiveKit JS sample to connect to the room and speak. The server-side gateway joins automatically on startup if `LIVEKIT_URL` is set.

## 8. AWS Lambda validator (optional)

If the local validator (`forge/validator.py:_local_validate`) is acceptable for the demo, skip this. Otherwise:

1. Package `forge/validator.py`'s scoring logic plus the synthetic cases as a Lambda
2. Set `AWS_LAMBDA_FUNCTION` and AWS keys in `.env`
3. The validator auto-detects AWS keys and uses Lambda when present
