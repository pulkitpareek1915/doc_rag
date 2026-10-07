import psycopg
from fastapi import APIRouter, Response

from docguard.api.models import HealthResponse
from docguard.config import settings

router = APIRouter()


@router.get("", response_model=HealthResponse)
def liveness() -> dict:
    return {
        "status": "ok",
        "service": "docguard",
        "dependencies": {},
    }


@router.get("/ready", response_model=HealthResponse)
def readiness(response: Response) -> dict:
    from docguard.services.query import _cache

    redis_status = "disabled"
    if _cache.enabled and _cache.redis:
        try:
            _cache.redis.ping()
            redis_status = "ok"
        except Exception:
            redis_status = "unavailable"

    postgres_status = "unknown"
    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        postgres_status = "ok"
    except Exception:
        postgres_status = "unavailable"

    if redis_status == "unavailable" or postgres_status == "unavailable":
        response.status_code = 503
        status = "unavailable"
    else:
        status = "ok"

    return {
        "status": status,
        "service": "docguard",
        "dependencies": {
            "postgres": postgres_status,
            "redis": redis_status,
        },
    }
