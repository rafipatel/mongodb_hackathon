from agent.state import MediMindState


async def route(state: MediMindState) -> MediMindState:
    """No-op node — routing decision happens on the conditional edge that follows."""
    return state
