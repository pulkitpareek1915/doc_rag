from typing import Any
from unittest.mock import patch

from docguard.agent.nodes.rewrite import rewrite_node
from docguard.agent.state import Document
from docguard.config import settings


def _mock_doc(idx: int, grade: str = "irrelevant") -> Document:
    return Document(
        id=f"doc-{idx}",
        content=f"content {idx}",
        score=0.0,
        grade=grade,  # type: ignore
        security="pending",
        metadata={},
    )


# TEST 1 — SUCCESSFUL REWRITE
@patch("docguard.agent.nodes.rewrite._call_claude_rewriter")
def test_successful_rewrite(mock_call: Any) -> None:
    mock_call.return_value = (
        "How does DocGuard quarantine documents that fail security scanning?"
    )
    state = {
        "query": "What happens to unsafe docs?",
        "rewrite_count": 0,
        "documents": [_mock_doc(1)],
    }
    result = rewrite_node(state)  # type: ignore

    assert (
        result["active_query"]
        == "How does DocGuard quarantine documents that fail security scanning?"
    )
    assert result["rewrite_count"] == 1
    assert state["query"] == "What happens to unsafe docs?"


# TEST 2 — ACTIVE QUERY
@patch("docguard.agent.nodes.rewrite._call_claude_rewriter")
def test_active_query_usage(mock_call: Any) -> None:
    mock_call.return_value = "rewritten query"
    state = {
        "query": "original",
        "active_query": "current retrieval query",
        "rewrite_count": 0,
        "documents": [],
    }
    rewrite_node(state)  # type: ignore

    mock_call.assert_called_once_with("current retrieval query", [])


# TEST 3 — API FAILURE
@patch("docguard.agent.nodes.rewrite.anthropic_client")
def test_api_failure(mock_client: Any) -> None:
    mock_client().messages.create.side_effect = Exception("API failure")
    settings.anthropic_api_key = "fake_key"

    state = {
        "query": "current query",
        "rewrite_count": 0,
        "documents": [],
    }

    result = rewrite_node(state)  # type: ignore

    assert result["active_query"] == "current query"
    assert result["rewrite_count"] == 1


# TEST 4 — EMPTY RESPONSE
@patch("docguard.agent.nodes.rewrite.anthropic_client")
def test_empty_response(mock_client: Any) -> None:
    class FakeContent:
        text = ""

    class FakeResponse:
        content = [FakeContent()]

    mock_client().messages.create.return_value = FakeResponse()
    settings.anthropic_api_key = "fake_key"

    state = {
        "query": "current query",
        "rewrite_count": 0,
        "documents": [],
    }

    result = rewrite_node(state)  # type: ignore

    assert result["active_query"] == "current query"
    assert result["rewrite_count"] == 1


# TEST 5 — SAME QUERY
@patch("docguard.agent.nodes.rewrite.anthropic_client")
def test_same_query(mock_client: Any) -> None:
    class FakeContent:
        text = "same query"

    class FakeResponse:
        content = [FakeContent()]

    mock_client().messages.create.return_value = FakeResponse()
    settings.anthropic_api_key = "fake_key"

    state = {
        "query": "same query",
        "rewrite_count": 0,
        "documents": [],
    }

    result = rewrite_node(state)  # type: ignore

    assert result["active_query"] == "same query"
    assert result["rewrite_count"] == 1


# TEST 6 — LONG RESPONSE
@patch("docguard.agent.nodes.rewrite.anthropic_client")
def test_long_response(mock_client: Any) -> None:
    class FakeContent:
        text = "A" * (settings.max_query_length + 50)

    class FakeResponse:
        content = [FakeContent()]

    mock_client().messages.create.return_value = FakeResponse()
    settings.anthropic_api_key = "fake_key"

    state = {
        "query": "current query",
        "rewrite_count": 0,
        "documents": [],
    }

    result = rewrite_node(state)  # type: ignore

    assert len(result["active_query"]) == settings.max_query_length
    assert result["active_query"] == "A" * settings.max_query_length


# TEST 7 — NO API KEY
@patch("docguard.agent.nodes.rewrite.anthropic_client")
def test_no_api_key(mock_client: Any) -> None:
    settings.anthropic_api_key = ""

    state = {
        "query": "current query",
        "rewrite_count": 0,
        "documents": [],
    }

    result = rewrite_node(state)  # type: ignore

    assert result["active_query"] == "current query"
    assert result["rewrite_count"] == 1
    mock_client.assert_not_called()


# TEST 8 — GRAPH TERMINATION
def test_graph_termination() -> None:
    from docguard.agent.graph import _route_after_grade
    from docguard.config import settings

    state = {
        "query": "test",
        "relevant_docs": [],
        "rewrite_count": settings.max_rewrites,
    }

    route = _route_after_grade(state)  # type: ignore

    assert route == "refuse"


# TEST 9 — ORIGINAL QUERY PRESERVED
@patch("docguard.agent.nodes.rewrite._call_claude_rewriter")
def test_original_query_preserved(mock_call: Any) -> None:
    mock_call.return_value = "new query"
    state = {
        "query": "original intent",
        "rewrite_count": 0,
        "documents": [],
    }

    result = rewrite_node(state)  # type: ignore

    assert state["query"] == "original intent"
    assert result["active_query"] == "new query"
    assert result["rewrite_count"] == 1
