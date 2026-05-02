from agent.state import MediMindState
from memory.search import embed_and_search


async def memory_lookup(state: MediMindState) -> MediMindState:
    transcript = state.get("transcript") or ""
    if not transcript:
        return {**state, "matched_skills": [], "best_score": 0.0}

    results = await embed_and_search(transcript, top_k=3)
    best_score = float(results[0]["score"]) if results else 0.0
    return {**state, "matched_skills": results, "best_score": best_score}
