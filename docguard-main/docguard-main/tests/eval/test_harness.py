
from docguard.eval.harness import EvalHarness
from docguard.eval.models import BenchmarkResult


class DummyCase:
    id = "dummy-1"

def dummy_evaluator(case, live):
    return BenchmarkResult(
        case_id=case.id,
        success=True,
        retrieval_metrics={"precision_at_k": 0.5}
    )

def test_run_single_case() -> None:
    harness = EvalHarness(live=False)
    case = DummyCase()
    result = harness.run_single_case(case, dummy_evaluator)

    assert result.case_id == "dummy-1"
    assert result.success is True
    assert result.retrieval_metrics == {"precision_at_k": 0.5}
    assert result.latency_ms is not None
    assert result.latency_ms >= 0

def test_run_dataset_and_aggregate() -> None:
    harness = EvalHarness(live=False)
    dataset = [DummyCase(), DummyCase()]
    results = harness.run_dataset(dataset, dummy_evaluator)

    assert len(results) == 2
    agg = harness.aggregate_results(results)

    assert agg["total_cases"] == 2
    assert agg["success_rate"] == 1.0
    assert "average_latency_ms" in agg
    assert agg["retrieval_metrics"]["precision_at_k"] == 0.5

def test_error_handling() -> None:
    harness = EvalHarness(live=False)
    case = DummyCase()

    def failing_eval(c, is_live):
        raise ValueError("Boom")

    result = harness.run_single_case(case, failing_eval)
    assert result.success is False
    assert result.error == "Boom"
    assert result.latency_ms is not None
