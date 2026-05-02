from datetime import datetime, timezone

from memory.client import get_collection
from memory.search import embed_document
from schemas.skill import Skill


def _new_skill_id() -> str:
    return f"PT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


async def store_skill(state: dict) -> dict:
    """LangGraph node: persist a forged skill to Atlas with a fresh embedding.

    Expects state to contain at least `transcript` and `forged_code`.
    Writes the new id back into state under `new_skill_id`.
    """
    code = state.get("forged_code") or ""
    description = state.get("transcript") or ""

    embedding = await embed_document(description)

    skill = Skill(
        id=_new_skill_id(),
        name=f"Auto-forged: {description[:60]}",
        description=description,
        code=code,
        embedding=embedding,
        trigger_conditions=[w for w in description.lower().split() if len(w) > 3][:6],
        validation_score=float(state.get("forge_validation_score", 0.0)),
    )

    await get_collection("skills").insert_one(skill.to_dict())
    return {**state, "new_skill_id": skill.id}


async def store_session(session_doc: dict) -> None:
    await get_collection("sessions").insert_one(session_doc)


async def store_task(task_doc: dict) -> None:
    await get_collection("tasks").insert_one(task_doc)


async def increment_skill_usage(skill_id: str) -> None:
    await get_collection("skills").update_one(
        {"id": skill_id}, {"$inc": {"usage_count": 1}}
    )
