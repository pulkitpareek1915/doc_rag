from unittest.mock import patch

from docguard.agent.state import Document


def fake_embed_text(text: str) -> list[float]:
    return [0.0] * 1536


class FakeVectorStore:
    def __init__(self, *args, **kwargs):
        pass

    def search(self, embedding: list[float], top_k: int, min_score: float = 0.0, metadata_filter: dict | None = None) -> list[Document]:
        return [
            Document(
                id="doc-1",
                content="DocGuard scans retrieved documents for prompt injection before generation.",
                metadata={},
                score=0.9,
                grade="pending",
                security="pending"
            ),
            Document(
                id="doc-2",
                content="Quarantined documents are isolated and logged as security events.",
                metadata={},
                score=0.8,
                grade="pending",
                security="pending"
            ),
        ]

    def add(self, *args, **kwargs):
        return "fake-id"

    def count(self):
        return 2


def run_smoke_test():
    # Patch the global _store instance in retrieve.py
    with patch("docguard.agent.nodes.retrieve._store", FakeVectorStore()), \
         patch("docguard.agent.nodes.retrieve.embed_text", fake_embed_text):

        from docguard.agent.graph import graph

        result = graph.invoke({"query": "How does DocGuard handle security?"})
        print(f"ORIGINAL QUERY: {result.get('query')}")
        print(f"ACTIVE QUERY: {result.get('active_query')}")
        print(f"REWRITE COUNT: {result.get('rewrite_count')}")
        print(f"REFUSAL: {result.get('refusal_reason')}")
        print(f"CITATIONS: {result.get('citations')}")


if __name__ == "__main__":
    run_smoke_test()
