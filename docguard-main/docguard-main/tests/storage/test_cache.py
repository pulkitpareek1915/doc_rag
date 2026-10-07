from unittest.mock import MagicMock

import pytest

from docguard.config import settings
from docguard.storage.cache import DocGuardCache


@pytest.fixture
def fake_redis(mocker):
    import fakeredis
    fake = fakeredis.FakeRedis(decode_responses=True)
    mocker.patch("redis.from_url", return_value=fake)
    return fake

def test_cache_miss(fake_redis, mocker):
    mocker.patch.object(settings, "cache_enabled", True)
    cache = DocGuardCache()
    assert cache.get("What is DocGuard?") is None

def test_cache_hit(fake_redis, mocker):
    mocker.patch.object(settings, "cache_enabled", True)
    cache = DocGuardCache()

    result = {
        "answer": "DocGuard is a secure agent.",
        "citations": ["doc-1"],
        "refusal_reason": None,
        "extra_secret_junk": "should-not-be-cached"
    }

    cache.set("What is DocGuard?", result)

    cached = cache.get("What is DocGuard?")
    assert cached is not None
    assert cached["answer"] == "DocGuard is a secure agent."
    assert cached["citations"] == ["doc-1"]
    assert "extra_secret_junk" not in cached

def test_cache_disabled(fake_redis, mocker):
    mocker.patch.object(settings, "cache_enabled", False)
    cache = DocGuardCache()

    cache.set("test query", {"answer": "test"})
    assert cache.get("test query") is None

def test_cache_key_deterministic(fake_redis, mocker):
    mocker.patch.object(settings, "cache_enabled", True)
    cache = DocGuardCache()
    key1 = cache._generate_key("  HELLO WORLD  ")
    key2 = cache._generate_key("hello world")
    assert key1 == key2

def test_cache_key_changes_for_relevant_config(fake_redis, mocker):
    mocker.patch.object(settings, "cache_enabled", True)
    cache = DocGuardCache()
    key1 = cache._generate_key("hello world")

    mocker.patch.object(settings, "llm_model", "different-model")
    key2 = cache._generate_key("hello world")

    assert key1 != key2

def test_redis_failure_does_not_break_query(fake_redis, mocker):
    mocker.patch.object(settings, "cache_enabled", True)

    # Mock redis to raise ConnectionError
    fake_redis.get = MagicMock(side_effect=Exception("Connection refused"))
    fake_redis.setex = MagicMock(side_effect=Exception("Connection refused"))

    cache = DocGuardCache()
    # The cache operations should catch the exception, log warning and continue
    assert cache.get("fail query") is None
    cache.set("fail query", {"answer": "test"}) # Should not raise
