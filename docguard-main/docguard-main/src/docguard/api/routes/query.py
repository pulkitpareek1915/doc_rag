import logging

from fastapi import APIRouter

from docguard.api.models import QueryRequest, QueryResponse
from docguard.services.query import execute_query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=QueryResponse)
def query_endpoint(request: QueryRequest) -> dict:
    # Delegate to the shared query service which handles caching and tracing
    return execute_query(query=request.query, source="api")
