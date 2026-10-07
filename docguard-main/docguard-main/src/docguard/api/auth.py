import hashlib
import logging
import secrets
import time

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from docguard.config import settings
from docguard.services.query import _cache

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """
    Verifies the API key.
    Returns a deterministic hashed identity for the caller to be used in rate limiting.
    """
    if not settings.auth_enabled:
        return "anonymous"

    if not credentials or not credentials.credentials:
        logger.warning("Missing API key.")
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not settings.api_auth_token:
        logger.error("Authentication is enabled but API_AUTH_TOKEN is not configured.")
        raise HTTPException(status_code=500, detail="Server configuration error")

    provided_token = credentials.credentials
    if not secrets.compare_digest(provided_token, settings.api_auth_token):
        logger.warning("Invalid API key provided.")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # Return a hashed identity of the token to use as rate limit key
    token_hash = hashlib.sha256(provided_token.encode("utf-8")).hexdigest()
    return f"identity:{token_hash}"


def check_rate_limit(
    request: Request, identity: str = Depends(verify_api_key)
) -> str:
    """
    Checks rate limit in Redis based on the identity.
    Fails open if Redis is unavailable.
    """
    if not settings.rate_limit_enabled:
        return identity

    if not _cache.enabled or not _cache.redis:
        # Fail open
        return identity

    # Use a fixed window based on the current time chunk
    current_time = int(time.time())
    window_start = current_time // settings.rate_limit_window_seconds
    key = f"rate_limit:{identity}:{window_start}"

    try:
        # Atomic increment and expire
        pipe = _cache.redis.pipeline()
        pipe.incr(key)
        # We expire slightly after the window to ensure cleanup
        pipe.expire(key, settings.rate_limit_window_seconds * 2)
        result = pipe.execute()

        request_count = result[0]
        if request_count > settings.rate_limit_requests:
            logger.warning("Rate limit exceeded.")

            # Calculate retry after
            next_window = (window_start + 1) * settings.rate_limit_window_seconds
            retry_after = next_window - current_time

            raise HTTPException(
                status_code=429,
                detail="Too Many Requests",
                headers={"Retry-After": str(retry_after)},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Redis error during rate limiting. Failing open. Error: {e}")
        # Fail open
        pass

    return identity
