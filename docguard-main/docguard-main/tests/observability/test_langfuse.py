from unittest.mock import MagicMock

from docguard.config import settings
from docguard.services.query import _should_trace, execute_query


def test_langfuse_disabled_mode(mocker):
    mocker.patch.object(settings, "langfuse_public_key", "")
    mocker.patch.object(settings, "langfuse_secret_key", "")

    # Assert langfuse_enabled property logic is correct
    assert not settings.langfuse_enabled
    assert not _should_trace()

def test_langfuse_enabled_mocked(mocker):
    mocker.patch.object(settings, "langfuse_public_key", "pk")
    mocker.patch.object(settings, "langfuse_secret_key", "sk")

    assert settings.langfuse_enabled
    assert _should_trace()

    mock_client = MagicMock()
    mocker.patch("docguard.services.query.get_client", return_value=mock_client)
    mocker.patch("docguard.agent.graph.graph.invoke", return_value={"answer": "mock"})
    mocker.patch("docguard.services.query._cache.get", return_value=None)

    result = execute_query("test query", session_id="session-1")

    # Called twice: once for input, once for output
    assert mock_client.update_current_span.call_count == 2
    call_kwargs = mock_client.update_current_span.call_args_list[0].kwargs
    assert call_kwargs["input"] == "test query"

    assert result["answer"] == "mock"

def test_langfuse_failure_does_not_break_query(mocker):
    mocker.patch.object(settings, "langfuse_public_key", "pk")
    mocker.patch.object(settings, "langfuse_secret_key", "sk")

    mock_client = MagicMock()
    mock_client.update_current_span.side_effect = Exception("Langfuse down")
    mocker.patch("docguard.services.query.get_client", return_value=mock_client)

    mock_invoke = mocker.patch("docguard.agent.graph.graph.invoke", return_value={"answer": "mock"})
    mocker.patch("docguard.services.query._cache.get", return_value=None)

    # Should not raise exception
    result = execute_query("test query")

    assert result["answer"] == "mock"
    mock_invoke.assert_called_once()
