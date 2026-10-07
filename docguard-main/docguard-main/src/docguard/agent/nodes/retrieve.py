from langfuse import observe

from docguard.agent.state import AgentState
from docguard.clients import embed_text
from docguard.config import settings
from docguard.storage.vector_store import VectorStore

_store = VectorStore()


@observe(as_type="span", name="retrieve", capture_input=False, capture_output=False)
def retrieve_node(state: AgentState) -> dict:
    query = state.get("active_query") or state.get("query", "")

    if not query.strip():
        return {
            "documents": [],
            "refusal_reason": "empty_query",
        }

    if len(query) > settings.max_query_length:
        return {
            "documents": [],
            "refusal_reason": "oversized_query",
        }

    embedding = embed_text(query)

    documents = _store.search(
        embedding=embedding,
        top_k=settings.retrieval_top_k,
        min_score=settings.retrieval_min_score,
    )

    retrieval_count = state.get("retrieval_count", 0) + 1

    return {
        "documents": documents,
        "active_query": query,
        "retrieval_count": retrieval_count,
    }
