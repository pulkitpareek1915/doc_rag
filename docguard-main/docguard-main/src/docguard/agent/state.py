from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

Grade = Literal["pending", "relevant", "irrelevant"]
SecurityStatus = Literal["pending", "clean", "quarantined"]


class Document(TypedDict, total=False):
    id: str
    content: str
    metadata: dict[str, Any]
    score: float
    grade: Grade
    security: SecurityStatus
    security_reason: str | None


class SecurityEvent(TypedDict):
    kind: str
    severity: str
    doc_id: str
    detector: str
    detail: str


class AgentState(TypedDict, total=False):
    query: str
    active_query: str

    rewrite_count: int
    retrieval_count: int
    irrelevant_count: int

    documents: list[Document]
    relevant_docs: list[Document]
    quarantined_docs: list[Document]

    security_events: Annotated[
        list[SecurityEvent],
        operator.add,
    ]

    answer: str | None
    citations: list[str]

    refusal_reason: str | None
