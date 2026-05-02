# Graph Report - /Users/rafa/MscAi/mongodb_hackathon  (2026-05-02)

## Corpus Check
- Corpus is ~18,647 words - fits in a single context window. You may not need a graph.

## Summary
- 223 nodes · 300 edges · 22 communities detected
- Extraction: 80% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_AWS hackathon free-tier docs|AWS hackathon free-tier docs]]
- [[_COMMUNITY_MongoDB client getters|MongoDB client getters]]
- [[_COMMUNITY_Respond memory vector lookup|Respond memory vector lookup]]
- [[_COMMUNITY_Checkpoint store Atlas FastAPI|Checkpoint store Atlas FastAPI]]
- [[_COMMUNITY_Ingest route LangGraph state|Ingest route LangGraph state]]
- [[_COMMUNITY_Voice MediMind dialog flow|Voice MediMind dialog flow]]
- [[_COMMUNITY_LiveKit audio gateway|LiveKit audio gateway]]
- [[_COMMUNITY_Discord notification dispatcher|Discord notification dispatcher]]
- [[_COMMUNITY_ElevenLabs TTS layer|ElevenLabs TTS layer]]
- [[_COMMUNITY_Orchestrator graph lifecycle|Orchestrator graph lifecycle]]
- [[_COMMUNITY_Forge Fireworks codegen|Forge Fireworks codegen]]
- [[_COMMUNITY_Fireworks Whisper transcribe|Fireworks Whisper transcribe]]
- [[_COMMUNITY_Atlas vector index setup|Atlas vector index setup]]
- [[_COMMUNITY_Architecture planning docs|Architecture planning docs]]
- [[_COMMUNITY_Task schema model|Task schema model]]
- [[_COMMUNITY_Session schema model|Session schema model]]
- [[_COMMUNITY_Static web MediMind UI|Static web MediMind UI]]
- [[_COMMUNITY_Transcribe file helper|Transcribe file helper]]
- [[_COMMUNITY_Speak configuration helpers|Speak configuration helpers]]
- [[_COMMUNITY_Speak streaming API|Speak streaming API]]
- [[_COMMUNITY_VoiceState types|VoiceState types]]
- [[_COMMUNITY_HANDOVER coordinator notes|HANDOVER coordinator notes]]

## God Nodes (most connected - your core abstractions)
1. `route_turn()` - 16 edges
2. `get_collection()` - 14 edges
3. `LangGraph build_graph / build_app wiring` - 12 edges
4. `MediMindState` - 9 edges
5. `_handle_transcript()` - 7 edges
6. `store_skill()` - 7 edges
7. `speak_stream()` - 7 edges
8. `execute_and_notify()` - 7 edges
9. `store_skill persists forged skill` - 7 edges
10. `route_turn` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Operations dashboard status pills transcript UI` --conceptually_related_to--> `LiveKit entrypoint rtc_session`  [INFERRED]
  static/index.html → voice/medimind_agent.py
- `Planned directory layout and stubs` --conceptually_related_to--> `forge_skill`  [INFERRED]
  claude_sonnet_planned_files/CODE_STRUCTURE.md → forge/forge.py
- `_try_lambda_validate AWS Lambda` --conceptually_related_to--> `Always Free AWS services Lambda S3 CloudWatch`  [INFERRED]
  forge/validator.py → hackathon_docs/AWS_Free_Tier__Hackathon_Participant_Guide.pdf
- `MediMind local setup guide` --conceptually_related_to--> `ensure_index Atlas vector search`  [INFERRED]
  SETUP.md → scripts/ensure_vector_index.py
- `Hackathon partner stack and setup notes` --semantically_similar_to--> `MediMind pitch themes tech stack demo script`  [INFERRED] [semantically similar]
  Readme.md → claude_sonnet_planned_files/README.md

## Hyperedges (group relationships)
- **Per-turn subgraph ingest to lookup to route before forge-or-respond branch** — ingest_node, memory_lookup_node, route_node, orchestrator [EXTRACTED 1.00]
- **Embedding generation plus Mongo skills query/write shared by agent lookup seed and store** — embedding_search, mongo_access_layer, skill_model, env_config [EXTRACTED 0.94]
- **Forge validate conditional loop ending in Atlas skill insert then respond** — forge_skill_node, validate_skill_node, store_skill_node, respond_node, orchestrator [EXTRACTED 0.93]
- **Forge prompt code-gen and validation path** — forge_forge_skill, prompts_build_forge_prompt, validator_validate_skill [EXTRACTED 1.00]
- **Notification fan-out with optional ElevenLabs MP3** — dispatcher_execute_and_notify, dispatcher_post_to_discord, speak_speak [EXTRACTED 1.00]
- **LiveKit audio chunk to Fireworks Whisper transcript** — gateway_run_voice_gateway, gateway_consume_track, transcribe_transcribe_bytes [EXTRACTED 1.00]

## Communities

### Community 0 - "AWS hackathon free-tier docs"
Cohesion: 0.07
Nodes (30): Always Free AWS services Lambda S3 CloudWatch, Billing alerts and zero-spend budget guidance, AWS Free Tier Hackathon Participant Guide, Planned directory layout and stubs, _exec_coordinate, execute_and_notify, fetch_skill_code, _post_to_discord webhook fan-out (+22 more)

### Community 1 - "MongoDB client getters"
Cohesion: 0.11
Nodes (26): BaseModel, get_client(), get_collection(), get_db(), ping(), Verify Atlas connectivity., _extract_patient_hint(), _extract_ward_hint() (+18 more)

### Community 2 - "Respond memory vector lookup"
Cohesion: 0.13
Nodes (16): _client(), embed(), embed_and_search(), embed_document(), increment_skill_usage(), _new_skill_id(), LangGraph node: persist a forged skill to Atlas with a fresh embedding.      Exp, store_session() (+8 more)

### Community 3 - "Checkpoint store Atlas FastAPI"
Cohesion: 0.2
Nodes (21): MongoDBSaver graph checkpoints, store_session store_task increment_skill_usage, Voyage embed + Atlas $vectorSearch pipeline, Environment-backed runtime constants, FastAPI MediMind app and HTTP surface, forge_skill LangGraph node, ingest node normalizes transcript, MediMindState TypedDict (+13 more)

### Community 4 - "Ingest route LangGraph state"
Cohesion: 0.14
Nodes (15): MediMindState, _aws_configured(), _load_synthetic_cases(), _local_validate(), Skill validator.  Real path: invoke an AWS Lambda that runs the forged code agai, Cheap local fallback. Score in [0, 1]., Try the AWS Lambda validator. Return None if it can't run so caller falls back., _try_lambda_validate() (+7 more)

### Community 5 - "Voice MediMind dialog flow"
Cohesion: 0.17
Nodes (12): _is_no(), _is_yes(), _last_user_text(), _patient_hint(), _pending_matched_from_history(), prewarm(), LiveKit voice agent for MediMind.  Pipeline:     user speaks  →  Silero VAD  →, If the previous assistant turn was asking for confirmation, return the stashed c (+4 more)

### Community 6 - "LiveKit audio gateway"
Cohesion: 0.18
Nodes (12): livekit_token(), _safe_voice_gateway(), _consume_track(), _frames_to_wav(), generate_join_token(), LiveKit voice gateway.  Subscribes to the configured room, accumulates ~1s buffe, Concatenate AudioFrames into a single 16-bit PCM WAV blob., Connect to LiveKit and pump every audio track into on_transcript. (+4 more)

### Community 7 - "Discord notification dispatcher"
Cohesion: 0.29
Nodes (10): _dispatch_step(), _exec_coordinate(), execute_and_notify(), _post_to_discord(), _pretty_step(), Notification dispatcher.  When a skill is confirmed for execution, we:  1. Execu, Run the skill, fan out each step, return {summary, steps:[...]}.      Steps are, Compile a skill module and return its ``coordinate`` callable. (+2 more)

### Community 8 - "ElevenLabs TTS layer"
Cohesion: 0.44
Nodes (8): _headers(), is_configured(), _payload(), ElevenLabs TTS — text in, audio bytes out (mp3)., Stream MP3 chunks as ElevenLabs produces them, so the browser starts playing fas, speak(), speak_stream(), _url()

### Community 9 - "Orchestrator graph lifecycle"
Cohesion: 0.28
Nodes (7): build_app(), build_app_no_checkpoint(), build_graph(), After validation: store if pass, retry forge if fail and budget remains, else gi, Build the graph wired to a MongoDB checkpointer.      Use this from FastAPI life, _validation_branch(), lifespan()

### Community 10 - "Forge Fireworks codegen"
Cohesion: 0.5
Nodes (3): _extract_code(), forge_skill(), build_forge_prompt()

### Community 11 - "Fireworks Whisper transcribe"
Cohesion: 0.4
Nodes (5): _consume_track, _frames_to_wav, generate_join_token, run_voice_gateway, transcribe_bytes

### Community 12 - "Atlas vector index setup"
Cohesion: 0.67
Nodes (3): ensure_index(), _find_index(), Create the Atlas Vector Search index on MediMind.skills.embedding if missing.  I

### Community 13 - "Architecture planning docs"
Cohesion: 0.5
Nodes (4): Agent flow mermaid state ER diagrams, Architecture paragraph LiveKit LangGraph Atlas forge, MediMind pitch themes tech stack demo script, Hackathon partner stack and setup notes

### Community 15 - "Task schema model"
Cohesion: 0.67
Nodes (1): Task

### Community 16 - "Session schema model"
Cohesion: 0.67
Nodes (1): Session

### Community 17 - "Static web MediMind UI"
Cohesion: 1.0
Nodes (2): LiveKit browser client voice room join, Landing hero MediMind value proposition

### Community 25 - "Transcribe file helper"
Cohesion: 1.0
Nodes (1): transcribe_file

### Community 26 - "Speak configuration helpers"
Cohesion: 1.0
Nodes (1): is_configured

### Community 27 - "Speak streaming API"
Cohesion: 1.0
Nodes (1): speak_stream

### Community 28 - "VoiceState types"
Cohesion: 1.0
Nodes (1): VoiceState

### Community 29 - "HANDOVER coordinator notes"
Cohesion: 1.0
Nodes (1): MediMind operational coordinator instructions

## Ambiguous Edges - Review These
- `store_session store_task increment_skill_usage` → `Task dataclass schema`  [AMBIGUOUS]
  memory/store.py · relation: store_task_accepts_generic_task_documents

## Knowledge Gaps
- **46 isolated node(s):** `MediMind FastAPI entrypoint.  Endpoints:   GET  /                            — d`, `Run a transcript through the LangGraph agent, then (optionally) execute the skil`, `Best-effort peek at the Atlas Search index status. Non-blocking on failure.`, `Stream ElevenLabs TTS via a plain URL — so `<audio src="/speak?text=...">` works`, `Verify Atlas connectivity.` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Task schema model`** (3 nodes): `task.py`, `Task`, `.to_dict()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Session schema model`** (3 nodes): `session.py`, `Session`, `.to_dict()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Static web MediMind UI`** (2 nodes): `LiveKit browser client voice room join`, `Landing hero MediMind value proposition`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Transcribe file helper`** (1 nodes): `transcribe_file`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Speak configuration helpers`** (1 nodes): `is_configured`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Speak streaming API`** (1 nodes): `speak_stream`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `VoiceState types`** (1 nodes): `VoiceState`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HANDOVER coordinator notes`** (1 nodes): `MediMind operational coordinator instructions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `store_session store_task increment_skill_usage` and `Task dataclass schema`?**
  _Edge tagged AMBIGUOUS (relation: store_task_accepts_generic_task_documents) - confidence is low._
- **Why does `route_turn()` connect `Voice MediMind dialog flow` to `MongoDB client getters`, `Respond memory vector lookup`, `Ingest route LangGraph state`, `Discord notification dispatcher`, `Forge Fireworks codegen`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `get_collection()` connect `MongoDB client getters` to `Respond memory vector lookup`, `Discord notification dispatcher`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `_handle_transcript()` connect `MongoDB client getters` to `Discord notification dispatcher`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `route_turn()` (e.g. with `increment_skill_usage()` and `store_session()`) actually correct?**
  _`route_turn()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `get_collection()` (e.g. with `skill_count()` and `skills_recent()`) actually correct?**
  _`get_collection()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `MediMindState` (e.g. with `After validation: store if pass, retry forge if fail and budget remains, else gi` and `Build the graph wired to a MongoDB checkpointer.      Use this from FastAPI life`) actually correct?**
  _`MediMindState` has 7 INFERRED edges - model-reasoned connections that need verification._