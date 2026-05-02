from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import END, StateGraph
from pymongo import MongoClient

from agent.nodes.ingest import ingest
from agent.nodes.memory_lookup import memory_lookup
from agent.nodes.respond import respond
from agent.nodes.route import route
from agent.state import MediMindState
from config import MONGODB_DB, MONGODB_URI, SKILL_MATCH_THRESHOLD
from forge.forge import forge_skill
from forge.validator import validate_skill
from memory.store import store_skill


def _should_forge(state: MediMindState) -> str:
    return "forge" if state.get("best_score", 0.0) < SKILL_MATCH_THRESHOLD else "execute"


def _validation_branch(state: MediMindState) -> str:
    """After validation: store if pass, retry forge if fail and budget remains, else give up."""
    if state.get("forge_validation_score", 0.0) >= 0.0 and state.get("forged_code"):
        # passed validation
        if state.get("forge_validation_score", 0.0) >= 0.80:
            return "store"
    if (state.get("forge_retries", 0) or 0) < 3:
        return "retry"
    return "respond"


def build_graph(checkpointer=None):
    graph = StateGraph(MediMindState)

    graph.add_node("ingest", ingest)
    graph.add_node("memory_lookup", memory_lookup)
    graph.add_node("route", route)
    graph.add_node("forge_skill", forge_skill)
    graph.add_node("validate_skill", validate_skill)
    graph.add_node("store_skill", store_skill)
    graph.add_node("respond", respond)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "memory_lookup")
    graph.add_edge("memory_lookup", "route")

    graph.add_conditional_edges(
        "route",
        _should_forge,
        {"forge": "forge_skill", "execute": "respond"},
    )

    graph.add_edge("forge_skill", "validate_skill")
    graph.add_conditional_edges(
        "validate_skill",
        _validation_branch,
        {"store": "store_skill", "retry": "forge_skill", "respond": "respond"},
    )
    graph.add_edge("store_skill", "respond")
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=checkpointer)


async def build_app():
    """Build the graph wired to a MongoDB checkpointer.

    Use this from FastAPI lifespan, not at import time, so we don't open a
    Mongo connection just because someone imported the module.

    `MongoDBSaver` exposes both sync and async checkpoint methods; LangGraph
    will call the async ones automatically inside `ainvoke`. The underlying
    pymongo client is sync, which is fine for the demo's checkpoint volume.
    """
    client = MongoClient(MONGODB_URI)
    saver = MongoDBSaver(client, db_name=MONGODB_DB)
    return build_graph(checkpointer=saver), client


# Cheap convenience for unit-style invocations without persistence
def build_app_no_checkpoint():
    return build_graph(checkpointer=None)
