import json
from unittest.mock import MagicMock, patch

import pytest

from docguard.config import settings
from docguard.mcp.server import query_docguard


@pytest.mark.asyncio
async def test_query_docguard_success(mocker):
    mock_execute = mocker.patch("docguard.mcp.server.execute_query", return_value={
        "answer": "Grounded answer",
        "citations": ["doc-1"],
        "refusal_reason": None,
    })

    response_json = await query_docguard("What is LangGraph?")
    data = json.loads(response_json)

    mock_execute.assert_called_once_with("What is LangGraph?", "mcp")
    assert data["answer"] == "Grounded answer"
    assert data["citations"] == ["doc-1"]
    assert data["refusal_reason"] is None


@pytest.mark.asyncio
async def test_query_docguard_empty_query() -> None:
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await query_docguard("   ")


@pytest.mark.asyncio
async def test_query_docguard_too_long() -> None:
    long_query = "a" * (settings.max_query_length + 1)
    with pytest.raises(ValueError, match="Query exceeds maximum length"):
        await query_docguard(long_query)


@pytest.mark.asyncio
@patch("docguard.mcp.server.execute_query")
async def test_query_docguard_refusal(mock_execute: MagicMock) -> None:
    mock_execute.return_value = {
        "answer": None,
        "citations": [],
        "refusal_reason": "insufficient_context",
    }

    result_str = await query_docguard("Is this in the context?")
    data = json.loads(result_str)

    assert data["answer"] is None
    assert data["refusal_reason"] == "insufficient_context"


@pytest.mark.asyncio
@patch("docguard.mcp.server.execute_query")
async def test_query_docguard_graph_error_sanitized(
    mock_execute: MagicMock,
) -> None:
    mock_execute.side_effect = Exception("Internal PGVector Error!")

    with pytest.raises(Exception, match="The DocGuard agent encountered an internal infrastructure error."):
        await query_docguard("Crash it")


@pytest.mark.asyncio
async def test_mcp_uses_existing_graph() -> None:
    # We now verify that mcp/server uses the query service
    from docguard.mcp.server import execute_query
    from docguard.services.query import execute_query as actual_execute_query

    assert execute_query is actual_execute_query
