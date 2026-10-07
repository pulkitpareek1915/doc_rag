import json
from unittest.mock import MagicMock, patch

from docguard.agent.nodes.generate import generate_node
from docguard.agent.state import Document
from docguard.config import settings

settings.anthropic_api_key = "test-key"


def _mock_doc(idx: int) -> Document:
    return Document(
        id=f"doc-{idx}",
        content=f"Content for doc {idx}",
        score=0.9,
        grade="relevant",
        security="clean",
        metadata={},
    )


@patch("docguard.agent.nodes.generate.anthropic_client")
def test_clean_context_grounded_answer(mock_client: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {
                    "answer": "This is the answer.",
                    "citations": ["doc-1"],
                    "refusal_reason": None,
                }
            )
        )
    ]
    mock_client.return_value.messages.create.return_value = mock_response

    state = {
        "query": "What is the answer?",
        "relevant_docs": [_mock_doc(1), _mock_doc(2)],
    }

    result = generate_node(state)  # type: ignore
    assert result["answer"] == "This is the answer."
    assert result["citations"] == ["doc-1"]
    assert result["refusal_reason"] is None


def test_empty_context_refusal() -> None:
    state = {
        "query": "What is the answer?",
        "relevant_docs": [],
    }
    result = generate_node(state)  # type: ignore
    assert result["answer"] is None
    assert result["refusal_reason"] == "insufficient_context"


@patch("docguard.agent.nodes.generate.anthropic_client")
def test_generation_api_failure(mock_client: MagicMock) -> None:
    mock_client.return_value.messages.create.side_effect = Exception("API error")
    state = {
        "query": "What is the answer?",
        "relevant_docs": [_mock_doc(1)],
    }
    result = generate_node(state)  # type: ignore
    assert result["answer"] is None
    assert result["refusal_reason"] == "generation_unavailable"


@patch("docguard.agent.nodes.generate.anthropic_client")
def test_citations_are_valid(mock_client: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {
                    "answer": "Answer",
                    "citations": ["doc-1", "doc-2"],
                    "refusal_reason": None,
                }
            )
        )
    ]
    mock_client.return_value.messages.create.return_value = mock_response

    state = {
        "query": "Q",
        "relevant_docs": [_mock_doc(1), _mock_doc(2)],
    }
    result = generate_node(state)  # type: ignore
    assert result["citations"] == ["doc-1", "doc-2"]


@patch("docguard.agent.nodes.generate.anthropic_client")
def test_invalid_citations_rejected(mock_client: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {
                    "answer": "Answer",
                    "citations": ["doc-1", "doc-999"],
                    "refusal_reason": None,
                }
            )
        )
    ]
    mock_client.return_value.messages.create.return_value = mock_response

    state = {
        "query": "Q",
        "relevant_docs": [_mock_doc(1)],
    }
    result = generate_node(state)  # type: ignore
    # doc-999 should be filtered out
    assert result["citations"] == ["doc-1"]


@patch("docguard.agent.nodes.generate.anthropic_client")
def test_unsupported_question_refusal(mock_client: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {
                    "answer": "I don't know.",
                    "citations": [],
                    "refusal_reason": "insufficient_context",
                }
            )
        )
    ]
    mock_client.return_value.messages.create.return_value = mock_response

    state = {
        "query": "Q",
        "relevant_docs": [_mock_doc(1)],
    }
    result = generate_node(state)  # type: ignore
    assert result["refusal_reason"] == "insufficient_context"


@patch("docguard.agent.nodes.generate.anthropic_client")
def test_original_user_query_preserved(mock_client: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {"answer": "x", "citations": [], "refusal_reason": None}
            )
        )
    ]
    mock_client.return_value.messages.create.return_value = mock_response

    state = {
        "query": "Original question",
        "active_query": "Modified query",
        "relevant_docs": [_mock_doc(1)],
    }
    generate_node(state)  # type: ignore

    # Assert call used 'query', not 'active_query'
    call_args = mock_client.return_value.messages.create.call_args[1]
    prompt = call_args["messages"][0]["content"]
    assert "Original question" in prompt
    assert "Modified query" not in prompt
