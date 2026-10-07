import json
from typing import Any
from unittest.mock import patch

from docguard.agent.nodes.grade import _parse_grader_response, grade_node
from docguard.agent.state import Document
from docguard.config import settings


def _mock_doc(idx: int, score: float = 0.0) -> Document:
    return Document(
        id=f"doc-{idx}",
        content=f"content {idx}",
        score=score,
        grade="pending",
        security="pending",
        metadata={},
    )


# TEST 1 — RELEVANT FILTERING
@patch("docguard.agent.nodes.grade._call_claude_grader")
def test_relevant_filtering(mock_call: Any) -> None:
    mock_call.return_value = [
        {"index": 0, "grade": "relevant"},
        {"index": 1, "grade": "irrelevant"},
        {"index": 2, "grade": "relevant"},
    ]

    state = {
        "documents": [
            _mock_doc(0),
            _mock_doc(1),
            _mock_doc(2),
        ],
        "query": "test query",
    }

    result = grade_node(state)  # type: ignore

    assert len(result["relevant_docs"]) == 2
    assert result["irrelevant_count"] == 1
    assert result["documents"][0]["grade"] == "relevant"
    assert result["documents"][1]["grade"] == "irrelevant"
    assert result["documents"][2]["grade"] == "relevant"


# TEST 2 — EMPTY DOCUMENTS
@patch("docguard.agent.nodes.grade._call_claude_grader")
def test_empty_documents(mock_call: Any) -> None:
    state = {
        "query": "test",
        "documents": [],
    }
    result = grade_node(state)  # type: ignore

    assert result["relevant_docs"] == []
    assert result["irrelevant_count"] == 0
    mock_call.assert_not_called()


# TEST 3 — CLAUDE API FAILURE
@patch("docguard.agent.nodes.grade.anthropic_client")
def test_claude_api_failure(mock_client: Any) -> None:
    mock_client().messages.create.side_effect = Exception("API error")

    # We will test the whole node to see if fallback is triggered
    settings.anthropic_api_key = "fake_key"
    settings.retrieval_min_score = 0.35

    state = {
        "query": "test query",
        "documents": [
            _mock_doc(0, score=0.90),
            _mock_doc(1, score=0.20),
        ],
    }

    result = grade_node(state)  # type: ignore

    assert result["documents"][0]["grade"] == "relevant"
    assert result["documents"][1]["grade"] == "irrelevant"


# TEST 4 — MALFORMED JSON
def test_malformed_json_fallback() -> None:
    raw = "This is not JSON."
    parsed = _parse_grader_response(raw, 2)
    assert parsed == []


# TEST 5 — INVALID JSON STRUCTURE
def test_invalid_json_structure() -> None:
    raw = json.dumps([{"index": 0, "grade": "maybe"}])
    parsed = _parse_grader_response(raw, 1)
    assert parsed == []


# TEST 6 — DUPLICATE INDEX
def test_duplicate_index() -> None:
    raw = json.dumps(
        [{"index": 0, "grade": "relevant"}, {"index": 0, "grade": "irrelevant"}]
    )
    parsed = _parse_grader_response(raw, 2)
    assert parsed == []


# TEST 7 — MISSING INDEX
def test_missing_index() -> None:
    raw = json.dumps(
        [{"index": 0, "grade": "relevant"}, {"index": 2, "grade": "irrelevant"}]
    )
    parsed = _parse_grader_response(raw, 2)
    assert parsed == []


# TEST 8 — VALID PARSER
def test_valid_parser() -> None:
    raw = json.dumps(
        [{"index": 0, "grade": "relevant"}, {"index": 1, "grade": "irrelevant"}]
    )
    parsed = _parse_grader_response(raw, 2)
    assert parsed == [
        {"index": 0, "grade": "relevant"},
        {"index": 1, "grade": "irrelevant"},
    ]


# TEST 9 — ACTIVE QUERY
@patch("docguard.agent.nodes.grade._call_claude_grader")
def test_active_query(mock_call: Any) -> None:
    mock_call.return_value = [{"index": 0, "grade": "relevant"}]

    state = {
        "query": "original query",
        "active_query": "active query",
        "documents": [_mock_doc(0)],
    }

    grade_node(state)  # type: ignore

    mock_call.assert_called_once_with("active query", state["documents"])


# TEST 10 — DOCUMENT ORDER
@patch("docguard.agent.nodes.grade._call_claude_grader")
def test_document_order(mock_call: Any) -> None:
    mock_call.return_value = [
        {"index": 2, "grade": "relevant"},
        {"index": 0, "grade": "irrelevant"},
        {"index": 1, "grade": "relevant"},
    ]

    state = {
        "query": "test",
        "documents": [
            _mock_doc(0),
            _mock_doc(1),
            _mock_doc(2),
        ],
    }

    result = grade_node(state)  # type: ignore

    assert result["documents"][0]["grade"] == "irrelevant"
    assert result["documents"][1]["grade"] == "relevant"
    assert result["documents"][2]["grade"] == "relevant"
