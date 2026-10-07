from __future__ import annotations

from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from docguard.agent.state import Document
from docguard.config import settings


class VectorStore:
    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or settings.database_url

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._dsn)
        register_vector(conn)
        return conn

    def add(
        self,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> str:
        if len(embedding) != settings.embedding_dims:
            raise ValueError(
                f"Embedding dimension mismatch: expected {settings.embedding_dims}, got {len(embedding)}"
            )

        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO documents (content, metadata, embedding)
                VALUES (%s, %s, %s)
                RETURNING id::text
                """,
                (
                    content,
                    Jsonb(metadata or {}),
                    embedding,
                ),
            ).fetchone()

        if row is None:
            raise RuntimeError("Failed to insert document")
        return str(row[0])

    def search(
        self,
        embedding: list[float],
        top_k: int,
        min_score: float = 0.0,
        metadata_filter: dict | None = None,
    ) -> list[Document]:
        if len(embedding) != settings.embedding_dims:
            raise ValueError(
                f"Embedding dimension mismatch: expected {settings.embedding_dims}, got {len(embedding)}"
            )

        if self.count() == 0:
            return []

        query = """
            SELECT
                id::text,
                content,
                metadata,
                1 - (embedding <=> %s) AS score
            FROM documents
        """

        params: list[Any] = [embedding]

        if metadata_filter:
            query += " WHERE metadata @> %s"
            params.append(Jsonb(metadata_filter))

        query += " ORDER BY embedding <=> %s LIMIT %s"
        params.extend([embedding, top_k])

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        documents = []
        for row in rows:
            score = float(row[3])
            if score >= min_score:
                documents.append(
                    Document(
                        id=str(row[0]),
                        content=str(row[1]),
                        metadata=dict(row[2]) if row[2] else {},
                        score=score,
                        grade="pending",
                        security="pending",
                    )
                )

        return documents

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT count(*) FROM documents"
            ).fetchone()

            if row is None:
                return 0
            return int(row[0])

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM quarantine")
            conn.execute("DELETE FROM documents")
            conn.commit()

    def quarantine_document(self, doc_id: str, content: str, reason: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO quarantine (doc_id, content, reason)
                VALUES (%s, %s, %s)
                """,
                (doc_id, content, reason),
            )
            conn.commit()
