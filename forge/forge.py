import re

import httpx

from agent.state import MediMindState
from config import FIREWORKS_API_KEY, FIREWORKS_CODE_MODEL, FORGE_MAX_RETRIES
from forge.prompts import build_forge_prompt

FIREWORKS_CHAT_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

_CODE_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def _extract_code(raw: str | None) -> str:
    if not raw:
        return ""
    match = _CODE_FENCE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


async def forge_skill(state: MediMindState) -> MediMindState:
    retries = state.get("forge_retries", 0) or 0
    if retries >= FORGE_MAX_RETRIES:
        return {**state, "forged_code": None, "forge_triggered": True}

    prompt = build_forge_prompt(
        state.get("transcript", ""), state.get("matched_skills") or []
    )

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                FIREWORKS_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {FIREWORKS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                "model": FIREWORKS_CODE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
                "temperature": 0.2,
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        print(f"[forge] Fireworks call failed: {exc}")
        return {
            **state,
            "forged_code": None,
            "forge_triggered": True,
            "forge_retries": retries + 1,
        }

    try:
        raw = data["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError):
        raw = None
    code = _extract_code(raw)

    return {
        **state,
        "forged_code": code,
        "forge_triggered": True,
        "forge_retries": retries + 1,
    }
