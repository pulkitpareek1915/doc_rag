from typing import Any

from pydantic import BaseModel


class RetrievalCase(BaseModel):
    id: str
    query: str
    relevant_document_ids: list[str]

class GradingCase(BaseModel):
    id: str
    query: str
    document_content: str
    expected_grade: str  # "relevant" or "irrelevant"

class SecurityCase(BaseModel):
    id: str
    category: str  # e.g., "clean", "prompt_injection", "pii", "secret"
    content: str
    expected_action: str # e.g. "quarantine" or "pass"

class GenerationCase(BaseModel):
    id: str
    query: str
    context_documents: list[dict[str, str]]  # list of {"id": "...", "content": "..."}
    expected_behavior: str # "answer" or "refuse"
    expected_refusal_reason: str | None = None

class BenchmarkResult(BaseModel):
    case_id: str
    success: bool
    retrieval_metrics: dict[str, float] | None = None
    grading_metrics: dict[str, float] | None = None
    security_metrics: dict[str, float] | None = None
    generation_metrics: dict[str, Any] | None = None
    refusal: str | None = None
    citations: list[str] | None = None
    latency_ms: float | None = None
    error: str | None = None
