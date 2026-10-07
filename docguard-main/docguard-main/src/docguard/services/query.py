import logging
import uuid
from typing import Any

from langfuse import get_client, observe, propagate_attributes

from docguard.agent.graph import graph
from docguard.config import settings
from docguard.storage.cache import DocGuardCache

logger = logging.getLogger(__name__)

# Initialize cache statically for the service
_cache = DocGuardCache()

def _should_trace() -> bool:
    return settings.langfuse_enabled

@observe(as_type="span", name="docguard_query", capture_input=False, capture_output=False)
def execute_query(query: str, source: str = "api", session_id: str | None = None) -> dict[str, Any]:
    """Orchestrates query execution, caching, and observability tracing."""

    if not session_id:
        session_id = str(uuid.uuid4())

    with propagate_attributes(session_id=session_id, tags=["docguard", source]):
        if _should_trace():
            try:
                langfuse = get_client()
                langfuse.update_current_span(
                    input=query,
                    metadata={
                        "source": source,
                        "environment": settings.environment,
                        "llm_model": settings.llm_model,
                        "embedding_model": settings.embedding_model,
                    }
                )
            except Exception as e:
                logger.warning(f"Langfuse trace update failed: {e}")

        # 1. Cache Lookup
        cached_result = _cache.get(query)
        if cached_result:
            if _should_trace():
                try:
                    langfuse = get_client()
                    langfuse.update_current_span(
                        output=cached_result,
                        metadata={"cache_hit": True}
                    )
                except Exception:
                    pass
            return cached_result

        # 2. Graph Execution
        state = {"query": query}
        try:
            # The underlying graph nodes will have their own @observe decorators.
            result = graph.invoke(state)
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            # Graph execution failure is fatal for the request. Let it bubble up.
            raise

        # Format the safe output
        output = {
            "answer": result.get("answer"),
            "citations": result.get("citations", []),
            "refusal_reason": result.get("refusal_reason"),
        }

        if _should_trace():
            try:
                langfuse = get_client()
                langfuse.update_current_span(
                    output=output,
                    metadata={"cache_hit": False}
                )
            except Exception:
                pass

        # 3. Cache Set
        _cache.set(query, output)

        return output
