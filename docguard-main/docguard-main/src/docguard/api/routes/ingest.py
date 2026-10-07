import logging

from fastapi import APIRouter, HTTPException

from docguard.api.models import IngestRequest, IngestResponse
from docguard.clients import embed_text
from docguard.config import settings
from docguard.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter()
store = VectorStore()


@router.post("", response_model=IngestResponse)
def ingest_endpoint(request: IngestRequest) -> dict:
    content_size_mb = len(request.content.encode("utf-8")) / (1024 * 1024)
    if content_size_mb > settings.max_document_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"Document exceeds maximum size of {settings.max_document_size_mb} MB",
        )

    try:
        embedding = embed_text(request.content)
        doc_id = store.add(request.content, embedding, request.metadata)
        return {
            "document_id": doc_id,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Internal ingestion error") from e
