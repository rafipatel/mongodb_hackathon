FORGE_SYSTEM = """You are a clinical operations coordination system.

You write small Python coordination functions that route notifications and track confirmations
between operational hospital staff (porters, pharmacy, bed managers, radiology, anaesthetics).

Hard rules — non-negotiable:
- NEVER make medical decisions, give diagnoses, or recommend treatment.
- ONLY perform operational coordination: who to notify, what to track, when to escalate.
- Return ONLY valid Python, no explanations, no markdown fences.
"""


def build_forge_prompt(transcript: str, partial_matches: list[dict]) -> str:
    partial_context = ""
    if partial_matches:
        partial_context = "\n\nClosest existing protocols (for shape, not content):\n"
        for m in partial_matches[:2]:
            partial_context += f"- {m.get('name')}: {m.get('description')}\n"

    return f"""{FORGE_SYSTEM}

A workflow gap has been detected. No existing protocol covers this situation.

Gap description (verbatim from clinician voice transcript):
{transcript}
{partial_context}

Write a single Python async function with this exact signature:

    async def coordinate(patient_id: str, ward: str, **kwargs) -> dict:

It must:
1. Identify the operational steps implied by the gap description.
2. For each step, build a notification payload (dict with keys: role, message, channel).
3. Return a dict with keys:
   - steps_initiated: list[dict]    # the notifications above
   - expected_confirmations: list[str]  # roles we expect to acknowledge
   - escalation_after_minutes: int      # 5..60
   - protocol_summary: str              # one-line human summary, no medical content

Return only the function body wrapped in ```python ... ``` fences. No prose."""
