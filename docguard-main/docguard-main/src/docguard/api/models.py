from typing import Any

from pydantic import BaseModel, Field

from docguard.config import settings


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_query_length,
        description="The user's question to answer using document context.",
    )


class QueryResponse(BaseModel):
    answer: str | None
    citations: list[str]
    refusal_reason: str | None


class IngestRequest(BaseModel):
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    dependencies: dict[str, str]


class ErrorResponse(BaseModel):
    detail: str
