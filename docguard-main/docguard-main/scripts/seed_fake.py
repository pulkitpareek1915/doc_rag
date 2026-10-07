from docguard.config import settings
from docguard.storage.vector_store import VectorStore


def fake_embedding(seed: int) -> list[float]:
    vector = [0.0] * settings.embedding_dims
    vector[seed % settings.embedding_dims] = 1.0
    return vector


docs = [
    (
        "DocGuard scans retrieved documents for prompt injection.",
        {"source": "manual", "topic": "security"},
    ),
    (
        "Quarantined documents are isolated from the generation context.",
        {"source": "manual", "topic": "security"},
    ),
    (
        "Corrective RAG rewrites a query when retrieval quality is low.",
        {"source": "architecture", "topic": "rag"},
    ),
]


def main():
    store = VectorStore()
    inserted = []
    for i, (content, metadata) in enumerate(docs):
        doc_id = store.add(content=content, embedding=fake_embedding(i), metadata=metadata)
        inserted.append(doc_id)
        print(f"Inserted: {doc_id}")
    print(f"{len(inserted)} inserted")


if __name__ == "__main__":
    main()
