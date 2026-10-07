import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from docguard.api.routes import health, ingest, query
from docguard.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocGuard API",
    description="Secure Document Intelligence Agent API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


from fastapi import Depends

from docguard.api.auth import check_rate_limit

app.include_router(health.router, prefix="/health", tags=["System"])
app.include_router(
    ingest.router,
    prefix="/documents/ingest",
    tags=["Ingestion"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    query.router,
    prefix="/query",
    tags=["Query"],
    dependencies=[Depends(check_rate_limit)]
)
