import hashlib
import json
import logging
from typing import Any, cast

import redis

from docguard.config import settings

logger = logging.getLogger(__name__)

class DocGuardCache:
    def __init__(self, redis_url: str = settings.redis_url):
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl_seconds
        self.redis: redis.Redis | None = None

        if self.enabled:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client. Caching disabled. {e}")
                self.enabled = False
        else:
            self.redis = None

    def _generate_key(self, query: str) -> str:
        """Generates a deterministic cache key omitting all secrets."""
        normalized_query = query.strip().lower()

        # Include configurations that materially affect generation
        payload = {
            "query": normalized_query,
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "retrieval_top_k": settings.retrieval_top_k,
            "retrieval_min_score": settings.retrieval_min_score,
            "enable_security_scan": settings.enable_security_scan,
        }

        payload_str = json.dumps(payload, sort_keys=True)
        key_hash = hashlib.md5(payload_str.encode("utf-8")).hexdigest()
        return f"docguard:query:{key_hash}"

    def get(self, query: str) -> dict[str, Any] | None:
        if not self.enabled or not self.redis:
            return None

        key = self._generate_key(query)
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                return cast(dict[str, Any], json.loads(cached_data))
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}. Bypassing cache. Error: {e}")
            return None

    def set(self, query: str, result: dict[str, Any]) -> None:
        if not self.enabled or not self.redis:
            return

        key = self._generate_key(query)
        try:
            # Only cache safe values
            safe_value = {
                "answer": result.get("answer"),
                "citations": result.get("citations", []),
                "refusal_reason": result.get("refusal_reason")
            }
            self.redis.setex(key, self.ttl, json.dumps(safe_value))
        except Exception as e:
            logger.warning(f"Redis set failed for {key}. Error: {e}")

    def delete(self, query: str) -> None:
        if not self.enabled or not self.redis:
            return

        key = self._generate_key(query)
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed for {key}. Error: {e}")
