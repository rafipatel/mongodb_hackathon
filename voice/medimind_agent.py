"""LiveKit voice agent for MediMind.

Pipeline:
    user speaks  →  Silero VAD  →  ElevenLabs STT  →  LLMAdapter(medimind_voice_graph)
                                                   →  ElevenLabs TTS  →  user hears

The wrapper graph (``medimind_voice_graph``) uses LangGraph's ``add_messages`` reducer,
so each turn receives the full chat history from LiveKit. A single node looks at:
 1. the last user message, and
 2. the most recent assistant message,
to decide whether we're in *scan* or *confirmation* state, and emits a short voice-friendly
reply as an ``AIMessage``.

State machine:
    SCAN                      — run embedding + vector search
      ├── match ≥ threshold   → "I can run <skill>. Shall I initiate?"   → PENDING_MATCH
      └── miss                → "I don't recognise that. Shall I build a new protocol?" → PENDING_FORGE

    PENDING_MATCH + yes       → record session, increment usage, "Initiating <skill>."
    PENDING_MATCH + no        → "Okay, standing by."
    PENDING_FORGE  + yes      → run forge + validate + store, "Built <new id>. Initiating."
    PENDING_FORGE  + no       → "Understood, no new protocol created."

Run:
    # In-terminal mic/speaker loop, no LiveKit server:
    uv run python voice/medimind_agent.py console

    # Full LiveKit worker, connect via https://agents-playground.livekit.io
    uv run python voice/medimind_agent.py dev
"""

from __future__ import annotations

import logging
import re
import sys
import uuid
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph, add_messages
from typing_extensions import TypedDict

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
)
from livekit.plugins import elevenlabs, langchain, silero

# Make sure the project root is importable when this file is run as a script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

load_dotenv(_PROJECT_ROOT / ".env")

from config import (  # noqa: E402
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    FORGE_PASS_SCORE,
    LIVEKIT_AGENT_NAME,
    SKILL_MATCH_THRESHOLD,
)
from forge.forge import forge_skill  # noqa: E402
from forge.validator import validate_skill  # noqa: E402
from memory.search import embed_and_search  # noqa: E402
from memory.store import increment_skill_usage, store_session, store_skill  # noqa: E402
from notifications.dispatcher import execute_and_notify, fetch_skill_code  # noqa: E402

logger = logging.getLogger("medimind-voice")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Instructions — voice-agent side only. Operational coordination, no medical advice.
# ---------------------------------------------------------------------------

AGENT_INSTRUCTIONS = """You are MediMind, an always-on clinical operations coordinator.

Rules:
- You only coordinate operational tasks (notifications, handovers, traces, retrievals).
- You NEVER give medical advice, diagnosis, or treatment recommendations.
- You always ask for confirmation before initiating a protocol.
- You keep every reply under two sentences. Voice interaction — no markdown, no emojis.
"""

_PATIENT_RE = re.compile(r"\bbed\s+(\w+)\b", re.IGNORECASE)
_WARD_RE = re.compile(r"\bward\s+([\w-]+)\b", re.IGNORECASE)


def _patient_hint(text: str) -> str:
    m = _PATIENT_RE.search(text or "")
    return f"bed-{m.group(1)}" if m else "unknown"


def _ward_hint(text: str) -> str:
    m = _WARD_RE.search(text or "")
    return m.group(1) if m else "ward"


# Short yes/no classifiers — spoken English, be generous.
_YES_RE = re.compile(
    r"\b(yes|yeah|yep|yup|sure|ok|okay|go|proceed|do it|do that|"
    r"initiate|please|confirm(ed)?|affirmative|sounds good|that's right|right)\b",
    re.IGNORECASE,
)
_NO_RE = re.compile(
    r"\b(no|nope|nah|cancel|stop|abort|never mind|nevermind|don't|do not|negative|hold off|wait)\b",
    re.IGNORECASE,
)

# Markers we stash in assistant messages so we can recognise state on the next turn.
# The LLMAdapter rebuilds state from LiveKit chat history, so we can't keep a side-channel
# state field — we embed the marker in the message and strip it before TTS… except the
# adapter speaks whatever message we return. So we keep the marker *invisible* by using
# a zero-width character suffix. It survives re-serialisation but isn't pronounced.
_MARK_MATCH = "\u200b\u200c"   # pending match confirmation
_MARK_FORGE = "\u200b\u200d"   # pending forge confirmation


def _strip_markers(text: str) -> str:
    return text.replace(_MARK_MATCH, "").replace(_MARK_FORGE, "")


# ---------------------------------------------------------------------------
# Wrapper graph state
# ---------------------------------------------------------------------------

class VoiceState(TypedDict):
    messages: Annotated[list, add_messages]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last_user_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return (m.content or "").strip()
    return ""


def _last_assistant_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            return (m.content or "").strip()
    return ""


def _pending_matched_from_history(messages: list) -> dict | None:
    """Find the most recent assistant turn that is still awaiting yes/no confirmation.

    LiveKit may insert filler turns (reprompt, greeting) without markers — scan backward
    past those instead of stopping at the first marker-less AIMessage (that bug dropped
    pending state after 'Sorry, should I proceed?' so 'Yes' ran embed_and_search on 'yes').
    """
    for m in reversed(messages):
        if not isinstance(m, AIMessage):
            continue
        text = m.content or ""
        if _MARK_MATCH in text:
            ctx = getattr(m, "additional_kwargs", {}) or {}
            return ctx.get("medimind_context") or {"mode": "match"}
        if _MARK_FORGE in text:
            ctx = getattr(m, "additional_kwargs", {}) or {}
            return ctx.get("medimind_context") or {"mode": "forge"}
        # Resolved / terminal replies — do not look further back for stale markers
        if any(
            hint in text
            for hint in (
                "Understood, standing by",
                "Initiating ",
                "Built and validated",
                "I couldn't build a safe protocol",
                "I had trouble reaching memory",
                "Escalating to the duty coordinator",
            )
        ):
            break
        # Greeting or clarification — keep scanning for an older confirmation question
        if "Sorry, should I proceed?" in text or "MediMind online" in text:
            continue
        break
    return None


def _is_yes(text: str) -> bool:
    return bool(_YES_RE.search(text)) and not _NO_RE.search(text)


def _is_no(text: str) -> bool:
    return bool(_NO_RE.search(text))


def _skill_name_for_voice(skill: dict) -> str:
    name = skill.get("name") or skill.get("id") or "the matched protocol"
    # Make "PT-0001" pronounce naturally
    if name.upper().startswith("PT-"):
        return f"protocol {name}"
    return name


# ---------------------------------------------------------------------------
# The one node — called on every user turn by the LLMAdapter
# ---------------------------------------------------------------------------

async def route_turn(state: VoiceState) -> dict:
    messages = state.get("messages", [])
    user_text = _last_user_text(messages)

    if not user_text:
        reply = AIMessage(
            content="MediMind online. Describe an operational gap and I will check my protocols."
        )
        return {"messages": [reply]}

    pending = _pending_matched_from_history(messages)

    # --- confirmation branch -------------------------------------------------
    if pending:
        if _is_no(user_text):
            reply = AIMessage(content="Understood, standing by.")
            return {"messages": [reply]}
        if _is_yes(user_text):
            if pending.get("mode") == "match":
                skill_id = pending.get("skill_id")
                name = pending.get("skill_name", skill_id)
                transcript = pending.get("transcript", "")
                session_id = f"voice-{uuid.uuid4().hex[:8]}"

                if skill_id:
                    await increment_skill_usage(skill_id)
                await store_session({
                    "session_id": session_id,
                    "transcript": transcript,
                    "matched_skills": [skill_id] if skill_id else [],
                    "forge_triggered": False,
                    "forge_skill_id": None,
                    "response_text": f"voice: initiated {skill_id}",
                    "timestamp": __import__("datetime").datetime.utcnow(),
                })

                # Actually fan out the notifications to Discord + dashboard feed
                notify_summary = None
                if skill_id:
                    code = await fetch_skill_code(skill_id)
                    if code:
                        try:
                            notify_summary = await execute_and_notify(
                                skill_code=code,
                                skill_id=skill_id,
                                session_id=session_id,
                                patient_id=_patient_hint(transcript),
                                ward=_ward_hint(transcript),
                                include_audio=False,  # voice channel already carries audio
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("notify on match failed: %s", exc)

                steps_n = len(notify_summary.get("steps", [])) if notify_summary else 0
                tail = f" I've paged {steps_n} role{'s' if steps_n != 1 else ''}." if steps_n else ""
                reply = AIMessage(
                    content=f"Initiating {name} now.{tail} I'll track confirmations and escalate if anyone's late."
                )
                return {"messages": [reply]}

            if pending.get("mode") == "forge":
                transcript = pending.get("transcript", "")
                matched = pending.get("matched_skills", [])
                session_id = f"voice-{uuid.uuid4().hex[:8]}"

                # Build the MediMind state for forge → validate → store
                forge_state = {
                    "session_id": session_id,
                    "transcript": transcript,
                    "matched_skills": matched,
                    "forge_retries": 0,
                }
                forge_state = await forge_skill(forge_state)
                forge_state = await validate_skill(forge_state)

                if (forge_state.get("forge_validation_score") or 0.0) >= FORGE_PASS_SCORE \
                        and forge_state.get("forged_code"):
                    stored = await store_skill(forge_state)
                    new_id = stored.get("new_skill_id")
                    await store_session({
                        "session_id": session_id,
                        "transcript": transcript,
                        "matched_skills": [m.get("id") for m in matched if m.get("id")],
                        "forge_triggered": True,
                        "forge_skill_id": new_id,
                        "response_text": f"voice: forged and initiated {new_id}",
                        "timestamp": __import__("datetime").datetime.utcnow(),
                    })

                    notify_summary = None
                    if new_id and forge_state.get("forged_code"):
                        try:
                            notify_summary = await execute_and_notify(
                                skill_code=forge_state["forged_code"],
                                skill_id=new_id,
                                session_id=session_id,
                                patient_id=_patient_hint(transcript),
                                ward=_ward_hint(transcript),
                                include_audio=False,
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("notify on forge failed: %s", exc)

                    steps_n = len(notify_summary.get("steps", [])) if notify_summary else 0
                    tail = f" {steps_n} role{'s' if steps_n != 1 else ''} paged." if steps_n else ""
                    reply = AIMessage(
                        content=(
                            f"Built and validated {new_id}. It's stored for next time, "
                            f"and I'm initiating it now.{tail}"
                        )
                    )
                    return {"messages": [reply]}

                reply = AIMessage(
                    content=(
                        "I couldn't build a safe protocol for that in time. "
                        "Escalating to the duty coordinator."
                    )
                )
                return {"messages": [reply]}

        # Neither yes nor no — re-prompt but KEEP marker + context so the next turn still
        # resolves pending (otherwise STT noise loses confirmation state entirely).
        mark = _MARK_MATCH if pending.get("mode") == "match" else _MARK_FORGE
        reply = AIMessage(
            content="Sorry, should I proceed? Please say yes or no." + mark,
            additional_kwargs={"medimind_context": pending},
        )
        return {"messages": [reply]}

    # --- scan branch ---------------------------------------------------------
    logger.info("[medimind-voice] SCAN transcript=%r", user_text)
    try:
        matches = await embed_and_search(user_text, top_k=3)
    except Exception as exc:  # noqa: BLE001
        logger.exception("embed_and_search failed")
        reply = AIMessage(
            content=f"I had trouble reaching memory. {exc}. Please try again."
        )
        return {"messages": [reply]}

    best_score = float(matches[0]["score"]) if matches else 0.0

    if matches and best_score >= SKILL_MATCH_THRESHOLD:
        top = matches[0]
        name = _skill_name_for_voice(top)
        context_blob = {
            "mode": "match",
            "skill_id": top.get("id"),
            "skill_name": top.get("name"),
            "transcript": user_text,
        }
        reply_text = (
            f"I have a protocol for this: {name}. "
            f"It covers {', '.join(top.get('trigger_conditions', []) or [])[:200]}. "
            f"Shall I initiate?"
        ) + _MARK_MATCH
        reply = AIMessage(content=reply_text, additional_kwargs={"medimind_context": context_blob})
        return {"messages": [reply]}

    # No good match → offer to forge
    context_blob = {
        "mode": "forge",
        "transcript": user_text,
        "matched_skills": matches,
    }
    reply_text = (
        "I don't have a protocol that fits that situation. "
        "Shall I build a new coordination protocol and store it for next time?"
    ) + _MARK_FORGE
    reply = AIMessage(content=reply_text, additional_kwargs={"medimind_context": context_blob})
    return {"messages": [reply]}


def _build_voice_graph():
    builder = StateGraph(VoiceState)
    builder.add_node("route_turn", route_turn)
    builder.add_edge(START, "route_turn")
    builder.add_edge("route_turn", END)
    return builder.compile()


_voice_graph = _build_voice_graph()


# ---------------------------------------------------------------------------
# LiveKit agent wiring
# ---------------------------------------------------------------------------

server = AgentServer()


def prewarm(proc: JobProcess):
    """Preload Silero so first connect is fast."""
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class MediMindVoiceAgent(Agent):
    """Voice agent with lifecycle hooks aligned with LiveKit's voice examples."""

    def __init__(self) -> None:
        super().__init__(instructions=AGENT_INSTRUCTIONS)

    async def on_enter(self) -> None:
        # Fire-and-forget like examples/voice_agents/basic_agent.py — registers speech on the session.
        self.session.generate_reply(
            instructions=(
                "Greet the user in one short sentence as MediMind, and invite them to "
                "describe an operational gap on the ward."
            )
        )


@server.rtc_session(agent_name=LIVEKIT_AGENT_NAME or "")
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    if not (ELEVENLABS_API_KEY or "").strip():
        logger.error(
            "ELEVENLABS_API_KEY is missing or empty — ElevenLabs STT/TTS will not produce audio."
        )
    if not (ELEVENLABS_VOICE_ID or "").strip():
        logger.error(
            "ELEVENLABS_VOICE_ID is missing or empty — TTS publish will fail."
        )

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=elevenlabs.STT(api_key=ELEVENLABS_API_KEY),
        llm=langchain.LLMAdapter(graph=_voice_graph),
        tts=elevenlabs.TTS(
            voice_id=ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
            api_key=ELEVENLABS_API_KEY,
        ),
    )

    # session.start() schedules ctx.connect() when room IO is used — do not call connect() again.
    await session.start(agent=MediMindVoiceAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
