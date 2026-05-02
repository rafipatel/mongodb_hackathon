from agent.state import MediMindState


async def ingest(state: MediMindState) -> MediMindState:
    """Normalise the inbound transcript and seed default state fields."""
    transcript = (state.get("transcript") or "").strip()
    return {
        **state,
        "transcript": transcript,
        "matched_skills": state.get("matched_skills", []),
        "best_score": state.get("best_score", 0.0),
        "forge_triggered": state.get("forge_triggered", False),
        "forge_retries": state.get("forge_retries", 0),
        "spoken": False,
    }
