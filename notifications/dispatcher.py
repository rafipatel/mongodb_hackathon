"""Notification dispatcher.

When a skill is confirmed for execution, we:
 1. Execute the skill's ``coordinate()`` function (sandboxed to a scratch namespace)
    to get a structured list of steps.
 2. Fan each step out in parallel to:
      - the local Atlas ``notifications`` collection (audit + live dashboard feed)
      - Discord (if ``DISCORD_WEBHOOK_URL`` is set): a text message plus the TTS
        audio rendering of the message as an MP3 attachment.

The Discord audio attachment uses ElevenLabs ``speak()``; Discord renders the MP3
inline with a play button, which is exactly what we want for the demo: a real
voice message that "went to pharmacy" is one click away.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from config import DISCORD_WEBHOOK_URL
from memory.client import get_collection
from voice.speak import is_configured as tts_configured
from voice.speak import speak as tts_speak

logger = logging.getLogger("medimind.notify")

# Per-channel emoji so the Discord feed reads at a glance.
_CHANNEL_ICON = {
    "bleep": "📟",
    "pager": "📟",
    "app": "📱",
    "dashboard": "🖥️",
    "secure_app": "🔒",
    "urgent_radio": "📡",
    "phone": "☎️",
    "email": "✉️",
    "sms": "💬",
}


# ---------------------------------------------------------------------------
# Skill execution
# ---------------------------------------------------------------------------

def _exec_coordinate(code: str) -> Any:
    """Compile a skill module and return its ``coordinate`` callable."""
    ns: dict[str, Any] = {"__name__": "medimind_skill"}
    try:
        exec(code, ns)  # noqa: S102 - trusted: seeded or validator-passed
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"skill failed to load: {exc}") from exc
    fn = ns.get("coordinate")
    if fn is None:
        raise RuntimeError("skill has no coordinate() function")
    return fn


async def run_skill(code: str, *, patient_id: str, ward: str, **kwargs) -> dict:
    """Execute the skill and return its output dict."""
    fn = _exec_coordinate(code)
    result = fn(patient_id=patient_id, ward=ward, **kwargs)
    if asyncio.iscoroutine(result):
        result = await result
    if not isinstance(result, dict):
        raise RuntimeError("skill returned non-dict")
    return result


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------

def _pretty_step(step: dict, skill_id: str | None, patient_id: str, ward: str) -> str:
    role = step.get("role", "unknown")
    channel = step.get("channel", "app")
    icon = _CHANNEL_ICON.get(channel, "🔔")
    message = step.get("message", "")
    sk = f"`{skill_id}` " if skill_id else ""
    return (
        f"{icon} **{role}** via *{channel}* — {sk}"
        f"(patient `{patient_id}`, ward `{ward}`)\n"
        f"> {message}"
    )


async def _post_to_discord(
    client: httpx.AsyncClient, *, content: str, audio: bytes | None, filename: str
) -> bool:
    if not DISCORD_WEBHOOK_URL:
        return False
    try:
        if audio:
            data = {"payload_json": json.dumps({"content": content})}
            files = {"files[0]": (filename, audio, "audio/mpeg")}
            r = await client.post(DISCORD_WEBHOOK_URL, data=data, files=files)
        else:
            r = await client.post(DISCORD_WEBHOOK_URL, json={"content": content})
        if r.status_code // 100 != 2:
            logger.warning("discord webhook %s: %s", r.status_code, r.text[:200])
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("discord webhook error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Per-step dispatch
# ---------------------------------------------------------------------------

async def _dispatch_step(
    client: httpx.AsyncClient,
    *,
    step: dict,
    session_id: str,
    skill_id: str | None,
    patient_id: str,
    ward: str,
    include_audio: bool,
) -> dict:
    role = step.get("role", "unknown")
    channel = step.get("channel", "app")
    message = step.get("message", "")

    audio: bytes | None = None
    if include_audio and tts_configured():
        try:
            # Make the voice message sound natural: "Pharmacy — discharge meds ready for..."
            spoken = f"{role.replace('_', ' ')}. {message}"
            audio = await tts_speak(spoken)
            if not audio:
                audio = None
        except Exception as exc:  # noqa: BLE001
            logger.warning("TTS failed for %s: %s", role, exc)
            audio = None

    content = _pretty_step(step, skill_id, patient_id, ward)
    filename = f"{role}-{uuid.uuid4().hex[:6]}.mp3"
    discord_ok = await _post_to_discord(client, content=content, audio=audio, filename=filename)

    record = {
        "session_id": session_id,
        "skill_id": skill_id,
        "role": role,
        "channel": channel,
        "message": message,
        "patient_id": patient_id,
        "ward": ward,
        "discord_posted": discord_ok,
        "audio_available": audio is not None,
        "timestamp": datetime.now(timezone.utc),
    }
    try:
        await get_collection("notifications").insert_one(record.copy())
    except Exception as exc:  # noqa: BLE001
        logger.warning("notification write failed: %s", exc)

    # Strip the BSON ObjectId for cleaner return (insert_one mutates in place).
    record.pop("_id", None)
    return record


# ---------------------------------------------------------------------------
# Public entrypoints
# ---------------------------------------------------------------------------

async def execute_and_notify(
    *,
    skill_code: str,
    skill_id: str | None,
    session_id: str,
    patient_id: str = "unknown",
    ward: str = "ward",
    include_audio: bool = True,
    extra_kwargs: dict | None = None,
) -> dict:
    """Run the skill, fan out each step, return {summary, steps:[...]}.

    Steps are dispatched concurrently. The whole thing is best-effort: per-step
    failures are logged and do not abort the batch.
    """
    try:
        result = await run_skill(
            skill_code, patient_id=patient_id, ward=ward, **(extra_kwargs or {})
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("skill execution failed")
        return {
            "ok": False,
            "error": str(exc),
            "steps": [],
            "summary": None,
        }

    steps = result.get("steps_initiated") or []

    # Header so the Discord channel clearly marks the start of a new batch.
    if DISCORD_WEBHOOK_URL and steps:
        async with httpx.AsyncClient(timeout=10) as client:
            await _post_to_discord(
                client,
                content=(
                    f"🟢 **MediMind initiating protocol** "
                    f"{'`' + skill_id + '`' if skill_id else ''} "
                    f"— {len(steps)} step{'s' if len(steps) != 1 else ''}. "
                    f"_{result.get('protocol_summary', '')}_"
                ),
                audio=None,
                filename="",
            )

    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [
            _dispatch_step(
                client,
                step=s,
                session_id=session_id,
                skill_id=skill_id,
                patient_id=patient_id,
                ward=ward,
                include_audio=include_audio,
            )
            for s in steps
        ]
        records = await asyncio.gather(*tasks, return_exceptions=True)

    out_records = [r for r in records if isinstance(r, dict)]

    return {
        "ok": True,
        "steps": out_records,
        "summary": result.get("protocol_summary"),
        "expected_confirmations": result.get("expected_confirmations", []),
        "escalation_after_minutes": result.get("escalation_after_minutes"),
    }


async def fetch_skill_code(skill_id: str) -> str | None:
    doc = await get_collection("skills").find_one({"id": skill_id}, {"code": 1, "_id": 0})
    return (doc or {}).get("code")
