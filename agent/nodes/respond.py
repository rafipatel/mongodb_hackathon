from datetime import datetime, timezone

from agent.state import MediMindState
from memory.store import increment_skill_usage, store_session


def _build_response(state: MediMindState) -> str:
    if state.get("forge_triggered"):
        new_id = state.get("new_skill_id")
        if new_id:
            return (
                "No existing protocol matched. I built and validated a new coordination "
                f"workflow ({new_id}) and stored it. Initiating it now."
            )
        return "No existing protocol matched and the forge could not validate a new one in time. Escalating to the duty coordinator."

    matched = state.get("matched_skills") or []
    if not matched:
        return "I could not find a matching protocol. Escalating to the duty coordinator."

    top = matched[0]
    return (
        f"Matched protocol {top.get('id')} — {top.get('name')}. "
        "Initiating the coordination steps now."
    )


async def respond(state: MediMindState) -> MediMindState:
    text = _build_response(state)

    matched = state.get("matched_skills") or []
    matched_ids = [m.get("id") for m in matched if m.get("id")]

    # Persist a session record so the dashboard can replay it
    await store_session(
        {
            "session_id": state.get("session_id"),
            "transcript": state.get("transcript"),
            "matched_skills": matched_ids,
            "forge_triggered": bool(state.get("forge_triggered")),
            "forge_skill_id": state.get("new_skill_id"),
            "response_text": text,
            "timestamp": datetime.now(timezone.utc),
        }
    )

    # Bump usage counter when we hit an existing skill
    if not state.get("forge_triggered") and matched_ids:
        await increment_skill_usage(matched_ids[0])

    return {**state, "response_text": text}
