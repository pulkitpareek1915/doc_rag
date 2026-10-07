import pytest

from docguard.eval.metrics import (
    citation_coverage,
    citation_validity,
    classification_metrics,
    hit_at_k,
    precision_at_k,
    recall_at_k,
    rewrite_recovery_rate,
)


def test_precision_at_k() -> None:
    assert precision_at_k(["1", "2", "3"], ["2", "3", "4"], 3) == 2 / 3
    assert precision_at_k(["1", "2", "3"], ["2", "3", "4"], 2) == 1 / 2
    assert precision_at_k([], ["1"], 3) == 0.0
    assert precision_at_k(["1"], [], 3) == 0.0

def test_recall_at_k() -> None:
    assert recall_at_k(["1", "2", "3"], ["2", "3", "4"], 3) == 2 / 3
    assert recall_at_k(["1", "2", "3"], ["2", "4"], 1) == 0.0
    assert recall_at_k([], ["1"], 3) == 0.0
    assert recall_at_k(["1"], [], 3) == 1.0

def test_hit_at_k() -> None:
    assert hit_at_k(["1", "2", "3"], ["3"], 3) is True
    assert hit_at_k(["1", "2", "3"], ["3"], 2) is False
    assert hit_at_k([], ["1"], 3) is False
    assert hit_at_k(["1"], [], 3) is True

def test_classification_metrics() -> None:
    actual = [True, False, True, False]
    expected = [True, True, False, False]
    metrics = classification_metrics(actual, expected)

    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5

    with pytest.raises(ValueError):
        classification_metrics([True], [])

def test_classification_metrics_zero_div() -> None:
    actual = [False, False]
    expected = [True, True]
    metrics = classification_metrics(actual, expected)
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0

def test_citation_validity() -> None:
    assert citation_validity(["doc-1", "doc-2"], ["doc-1", "doc-2", "doc-3"]) == 1.0
    assert citation_validity(["doc-1", "fake-1"], ["doc-1", "doc-2"]) == 0.5
    assert citation_validity([], ["doc-1"]) == 1.0

def test_citation_coverage() -> None:
    assert citation_coverage(["doc-1", "doc-2"], ["doc-1", "doc-2", "doc-3"]) == 2 / 3
    assert citation_coverage(["doc-1", "doc-2"], []) == 1.0
    assert citation_coverage([], ["doc-1"]) == 0.0

def test_rewrite_recovery_rate() -> None:
    assert rewrite_recovery_rate(10, 5) == 0.5
    assert rewrite_recovery_rate(0, 5) == 0.0

def test_false_positive_rate() -> None:
    from docguard.eval.metrics import false_positive_rate
    actual = [True, False, True, False]
    expected = [True, True, False, False]
    assert false_positive_rate(actual, expected) == 0.5
    assert false_positive_rate([True], [True]) == 0.0

def test_percentile() -> None:
    from docguard.eval.metrics import calculate_percentile
    lats = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert calculate_percentile(lats, 0.5) == 30.0
    assert calculate_percentile(lats, 0.95) == 50.0
    assert calculate_percentile([], 0.5) == 0.0
