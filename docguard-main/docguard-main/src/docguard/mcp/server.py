import asyncio
import logging

from mcp.server.fastmcp import FastMCP

from docguard.config import settings
from docguard.services.query import execute_query

logger = logging.getLogger(__name__)

mcp = FastMCP("DocGuard")

@mcp.tool()
async def query_docguard(query: str) -> str:
    """Query the securely guarded DocGuard agent.

    Retrieves verified documents, aggressively scans for prompt injections
    and malicious content, and provides definitively grounded answers with citations.
    Will safely refuse unsupported questions.

    Args:
        query: The user's question to answer using document context.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if len(query) > settings.max_query_length:
        raise ValueError(f"Query exceeds maximum length of {settings.max_query_length}.")

    try:
        # execute_query orchestrates cache lookup and synchronous Graph execution.
        # Run it in a threadpool to avoid blocking Stdio
        result = await asyncio.to_thread(execute_query, query, "mcp")

        import json
        return json.dumps({
            "answer": result.get("answer"),
            "citations": result.get("citations", []),
            "refusal_reason": result.get("refusal_reason"),
        })

    except Exception as e:
        logger.error(f"DocGuard MCP execution failed: {e}")
        # Explicit error result for MCP
        raise ValueError("The DocGuard agent encountered an internal infrastructure error.") from e


if __name__ == "__main__":
    mcp.run()
