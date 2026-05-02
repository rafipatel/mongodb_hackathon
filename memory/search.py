import voyageai

from config import ATLAS_SEARCH_INDEX, VOYAGE_API_KEY, VOYAGE_MODEL
from memory.client import get_collection

_voyage: voyageai.AsyncClient | None = None


def _client() -> voyageai.AsyncClient:
    global _voyage
    if _voyage is None:
        _voyage = voyageai.AsyncClient(api_key=VOYAGE_API_KEY)
    return _voyage


async def embed(text: str) -> list[float]:
    result = await _client().embed([text], model=VOYAGE_MODEL, input_type="query")
    return result.embeddings[0]


async def embed_document(text: str) -> list[float]:
    result = await _client().embed([text], model=VOYAGE_MODEL, input_type="document")
    return result.embeddings[0]


async def embed_and_search(text: str, top_k: int = 3) -> list[dict]:
    embedding = await embed(text)

    pipeline = [
        {
            "$vectorSearch": {
                "index": ATLAS_SEARCH_INDEX,
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k,
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "name": 1,
                "code": 1,
                "description": 1,
                "trigger_conditions": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    cursor = get_collection("skills").aggregate(pipeline)
    return await cursor.to_list(top_k)
