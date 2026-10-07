import os

from docguard.clients import embed_text
from docguard.storage.vector_store import VectorStore

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
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Skipping real seed.")
        return

    store = VectorStore()
    inserted = []
    for content, metadata in docs:
        embedding = embed_text(content)
        doc_id = store.add(content=content, embedding=embedding, metadata=metadata)
        inserted.append(doc_id)
        print(f"Inserted: {doc_id}")
    print(f"{len(inserted)} inserted")


if __name__ == "__main__":
    main()
