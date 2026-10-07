
from docguard.services.query import _cache, execute_query


def test_cache_hit_skips_graph(mocker):
    # Mock cache hit
    mocker.patch.object(_cache, "get", return_value={"answer": "Cached!", "citations": ["doc-1"]})
    mock_invoke = mocker.patch("docguard.agent.graph.graph.invoke")

    result = execute_query("What is the speed of light?")

    # Graph should not be invoked
    mock_invoke.assert_not_called()
    assert result["answer"] == "Cached!"

def test_cache_miss_executes_graph(mocker):
    # Mock cache miss
    mocker.patch.object(_cache, "get", return_value=None)
    mock_set = mocker.patch.object(_cache, "set")

    mock_invoke = mocker.patch("docguard.agent.graph.graph.invoke", return_value={
        "answer": "Graph result",
        "citations": ["doc-2"],
        "refusal_reason": None,
        "raw_secret": "hidden"
    })

    result = execute_query("What is the speed of light?")

    # Graph should be invoked once
    mock_invoke.assert_called_once_with({"query": "What is the speed of light?"})

    # Expected output should be sanitized
    assert result["answer"] == "Graph result"
    assert "raw_secret" not in result

    # Value should be cached
    mock_set.assert_called_once()
