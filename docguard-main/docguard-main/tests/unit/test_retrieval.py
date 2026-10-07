from typing import Any
from unittest.mock import patch

from docguard.agent.nodes.retrieve import retrieve_node
from docguard.agent.state import Document


def fake_embed_text(text: str) -> list[float]:
    return [0.0] * 1536


class FakeVectorStore:
    def search(self, embedding: list[float], top_k: int, min_score: float = 0.0) -> list[Document]:
        return [Document(id="test-doc", content="test", score=0.9)]


@patch("docguard.agent.nodes.retrieve._store", FakeVectorStore())
@patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text)
def test_retrieval_active_query() -> None:
    state = {"query": "original", "active_query": "refined"}
    result = retrieve_node(state)  # type: ignore
    assert result["active_query"] == "refined"


@patch("docguard.agent.nodes.retrieve._store", FakeVectorStore())
@patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text)
def test_retrieval_attempt_increments() -> None:
    state = {"query": "test", "retrieval_count": 1}
    result = retrieve_node(state)  # type: ignore
    assert result["retrieval_count"] == 2


@patch("docguard.agent.nodes.retrieve._store", FakeVectorStore())
@patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text)
def test_empty_query_rejected() -> None:
    state = {"query": "   "}
    result = retrieve_node(state)  # type: ignore
    assert result["documents"] == []
    assert result["refusal_reason"] == "empty_query"


@patch("docguard.agent.nodes.retrieve._store", FakeVectorStore())
@patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text)
@patch("docguard.agent.nodes.retrieve.settings")
def test_oversized_query_rejected(mock_settings: Any) -> None:
    mock_settings.max_query_length = 5
    state = {"query": "too long query"}
    result = retrieve_node(state)  # type: ignore
    assert result["documents"] == []
    assert result["refusal_reason"] == "oversized_query"


@patch("docguard.agent.nodes.retrieve._store", FakeVectorStore())
@patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text)
def test_retrieved_documents_returned() -> None:
    state = {"query": "test"}
    result = retrieve_node(state)  # type: ignore
    assert len(result["documents"]) == 1
    assert result["documents"][0]["id"] == "test-doc"


class EmptyVectorStore:
    def search(self, embedding: list[float], top_k: int, min_score: float = 0.0) -> list[Document]:
        return []


@patch("docguard.agent.nodes.retrieve._store", EmptyVectorStore())
@patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text)
def test_no_documents_safely_handled() -> None:
    state = {"query": "test"}
    result = retrieve_node(state)  # type: ignore
    assert result["documents"] == []
