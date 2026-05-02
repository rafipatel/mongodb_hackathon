# Graph Report - /Users/rafa/MscAi/mongodb_hackathon  (2026-05-02)

## Corpus Check
- Corpus is ~5,815 words - fits in a single context window. You may not need a graph.

## Summary
- 91 nodes · 112 edges · 11 communities detected
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Forge & Skill Storage|Forge & Skill Storage]]
- [[_COMMUNITY_MediMind Vision & Hackathon Themes|MediMind Vision & Hackathon Themes]]
- [[_COMMUNITY_Memory & Vector Search Stack|Memory & Vector Search Stack]]
- [[_COMMUNITY_Hackathon Rules & Judging|Hackathon Rules & Judging]]
- [[_COMMUNITY_AWS Free Tier Constraints|AWS Free Tier Constraints]]
- [[_COMMUNITY_Core System Flows|Core System Flows]]
- [[_COMMUNITY_Voice Ingest Pipeline|Voice Ingest Pipeline]]
- [[_COMMUNITY_Code Structure Overview|Code Structure Overview]]
- [[_COMMUNITY_Session Schema|Session Schema]]
- [[_COMMUNITY_Task Schema|Task Schema]]
- [[_COMMUNITY_Python Dependencies|Python Dependencies]]

## God Nodes (most connected - your core abstractions)
1. `MediMind - Clinical Operations Intelligence` - 23 edges
2. `agent/orchestrator.py - LangGraph Graph Definition` - 11 edges
3. `MongoDB Agentic Evolution Hackathon` - 10 edges
4. `AWS Free Tier Hackathon Participant Guide` - 10 edges
5. `Setup and Partner Info` - 7 edges
6. `MongoDB` - 4 edges
7. `AWS Lambda` - 4 edges
8. `Atlas Vector Search` - 4 edges
9. `memory/search.py - embed_and_search` - 4 edges
10. `forge/forge.py - Fireworks AI Code Generation` - 4 edges

## Surprising Connections (you probably didn't know these)
- `MongoDB Atlas M10 Sandbox Cluster` --semantically_similar_to--> `MongoDB Atlas Hackathon Sandbox Requirement`  [INFERRED] [semantically similar]
  hackathon_docs/AWS_Free_Tier__Hackathon_Participant_Guide.pdf → Readme.md
- `Recommended Hackathon Stacks (AI Agent: Lambda + Bedrock + Atlas Vector Search)` --conceptually_related_to--> `MediMind - Clinical Operations Intelligence`  [INFERRED]
  hackathon_docs/AWS_Free_Tier__Hackathon_Participant_Guide.pdf → claude_sonnet_planned_files/README.md
- `Atlas Sandbox Build Requirement` --semantically_similar_to--> `MongoDB Atlas Hackathon Sandbox Requirement`  [INFERRED] [semantically similar]
  hackathon_docs/hackathon_details.md → Readme.md
- `Theme: Prolonged Coordination` --semantically_similar_to--> `Prolonged Coordination (Hackathon Theme)`  [INFERRED] [semantically similar]
  hackathon_docs/hackathon_details.md → claude_sonnet_planned_files/README.md
- `Theme: Adaptive Retrieval` --semantically_similar_to--> `Adaptive Retrieval (Hackathon Theme)`  [INFERRED] [semantically similar]
  hackathon_docs/hackathon_details.md → claude_sonnet_planned_files/README.md

## Hyperedges (group relationships)
- **Voice I/O Pipeline (LiveKit + Whisper + ElevenLabs)** — readme_livekit, readme_whisper_transcription, readme_elevenlabs, code_structure_voice_gateway, code_structure_voice_speak [EXTRACTED 1.00]
- **Skill Forge Pipeline (Fireworks gen + Lambda validate + Atlas store)** — readme_fireworks_ai, readme_aws_lambda_sandbox, readme_atlas_vector_search, code_structure_forge, code_structure_validator, code_structure_memory_store, readme_skill_forge_concept [EXTRACTED 1.00]
- **LangGraph State Machine Nodes** — code_structure_node_ingest, code_structure_node_memory_lookup, code_structure_node_route, code_structure_node_respond, code_structure_orchestrator, code_structure_state [EXTRACTED 1.00]

## Communities

### Community 0 - "Forge & Skill Storage"
Cohesion: 0.13
Nodes (17): config.py - Env Vars and Constants, forge/forge.py - Fireworks AI Code Generation, FORGE_MAX_RETRIES = 3, FORGE_PASS_SCORE = 0.80, memory/client.py - MongoDB Atlas Connection Singleton, memory/store.py - store_skill, store_session, store_task, Node ingest - receive and clean transcript, Node respond - build and speak response (+9 more)

### Community 1 - "MediMind Vision & Hackathon Themes"
Cohesion: 0.14
Nodes (17): voice/speak.py - ElevenLabs TTS, Always-On Architecture Rationale, Theme: Prolonged Coordination, AWS Lambda - Sandbox Validation, ElevenLabs - Voice Out, Judging Criteria (Live Demo 45%, Creativity 35%, Impact 20%), LangSmith Checkpointer - Shift-long Memory, MediMind - Clinical Operations Intelligence (+9 more)

### Community 2 - "Memory & Vector Search Stack"
Cohesion: 0.13
Nodes (17): Initialize MongoDB Client Outside Lambda Handler Rationale, Recommended Hackathon Stacks (AI Agent: Lambda + Bedrock + Atlas Vector Search), Atlas Vector Search Index (skill_index, knnVector, 1024 dim, cosine), memory/search.py - embed_and_search, Node memory_lookup - Atlas vector search, Atlas Vector Search, AWS Lambda, deepagents (+9 more)

### Community 3 - "Hackathon Rules & Judging"
Cohesion: 0.17
Nodes (12): Banned Anti-Projects (no medical advice AI etc.), Best Use of ElevenLabs Bonus Track, MongoDB Agentic Evolution Hackathon, Judges Panel (Pete Johnson MongoDB, David Asamu LangChain, etc.), Judging Process (3 rounds), Hackathon Prizes (15k cash + credits), Max Team Size 4, Theme: Adaptive Retrieval (+4 more)

### Community 4 - "AWS Free Tier Constraints"
Cohesion: 0.24
Nodes (11): Always Free AWS Services (Lambda, S3, API Gateway, CloudWatch), MongoDB Atlas M10 Sandbox Cluster, Avoid AWS DocumentDB Rationale (no free tier, $60/mo min), Set Billing Alert at $1 (Zero Spend Budget), Cleanup After Hackathon, Choose Free Plan Rationale (account closes vs charges), AWS Free Tier Hackathon Participant Guide, AWS Landmines (NAT Gateway, Elastic IPs, oversized EC2) (+3 more)

### Community 5 - "Core System Flows"
Cohesion: 0.29
Nodes (7): MediMind Communicators (nurse, doctor, coordinator), MongoDB Atlas ER Data Model, Forge Pipeline (transcript -> Fireworks -> Lambda -> Atlas), MediMind Full System Flow, Skill Match Decision (>= 0.78 execute, else forge), LangGraph State Machine (ingest -> memory_lookup -> route -> respond), MongoDB Collection: skills

### Community 6 - "Voice Ingest Pipeline"
Cohesion: 0.4
Nodes (5): server.py - FastAPI Entry Point, voice/gateway.py - LiveKit Listener, voice/transcribe.py - Fireworks Whisper Wrapper, LiveKit - Real-time Audio Capture, Fireworks AI Whisper - Speech to Text

### Community 7 - "Code Structure Overview"
Cohesion: 1.0
Nodes (2): MediMind Directory Layout, MediMind Code Structure

### Community 8 - "Session Schema"
Cohesion: 1.0
Nodes (1): schemas/session.py - Session Dataclass

### Community 9 - "Task Schema"
Cohesion: 1.0
Nodes (1): schemas/task.py - Task Dataclass

### Community 10 - "Python Dependencies"
Cohesion: 1.0
Nodes (1): pyproject.toml - Python Dependencies

## Knowledge Gaps
- **36 isolated node(s):** `deepagents`, `Text to MQL`, `LiveKit MongoDB Hacker Starter Repo`, `LiveKit Agent Skills Repo`, `MediMind Code Structure` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Code Structure Overview`** (2 nodes): `MediMind Directory Layout`, `MediMind Code Structure`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Session Schema`** (1 nodes): `schemas/session.py - Session Dataclass`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Task Schema`** (1 nodes): `schemas/task.py - Task Dataclass`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Python Dependencies`** (1 nodes): `pyproject.toml - Python Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MediMind - Clinical Operations Intelligence` connect `MediMind Vision & Hackathon Themes` to `Forge & Skill Storage`, `Memory & Vector Search Stack`, `Hackathon Rules & Judging`, `Core System Flows`, `Voice Ingest Pipeline`?**
  _High betweenness centrality (0.483) - this node is a cross-community bridge._
- **Why does `agent/orchestrator.py - LangGraph Graph Definition` connect `Forge & Skill Storage` to `Memory & Vector Search Stack`, `Core System Flows`, `Voice Ingest Pipeline`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **Why does `MongoDB Agentic Evolution Hackathon` connect `Hackathon Rules & Judging` to `MediMind Vision & Hackathon Themes`, `AWS Free Tier Constraints`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **What connects `deepagents`, `Text to MQL`, `LiveKit MongoDB Hacker Starter Repo` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Forge & Skill Storage` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._
- **Should `MediMind Vision & Hackathon Themes` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._
- **Should `Memory & Vector Search Stack` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._