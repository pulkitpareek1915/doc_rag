import time
from collections.abc import Callable
from typing import Any

from docguard.eval.models import BenchmarkResult


class EvalHarness:
    def __init__(self, live: bool = False):
        self.live = live

    def run_single_case(self, case: Any, evaluator: Callable) -> BenchmarkResult:
        start_time = time.perf_counter()

        try:
            result = evaluator(case, self.live)
            if not isinstance(result, BenchmarkResult):
                raise TypeError("evaluator must return BenchmarkResult")
            result.latency_ms = (time.perf_counter() - start_time) * 1000
            return result
        except Exception as e:
            return BenchmarkResult(
                case_id=case.id if hasattr(case, "id") else "unknown",
                success=False,
                error=str(e),
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

    def run_dataset(
        self, dataset: list[Any], evaluator: Callable
    ) -> list[BenchmarkResult]:
        return [self.run_single_case(case, evaluator) for case in dataset]

    def aggregate_results(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        if not results:
            return {"count": 0}

        successes = sum(1 for r in results if r.success)
        total = len(results)

        aggregate: dict[str, Any] = {
            "total_cases": total,
            "success_rate": successes / total,
            "average_latency_ms": sum(r.latency_ms or 0 for r in results) / total,
        }

        # Merge metrics specifically if they exist across results
        metric_types = ["retrieval_metrics", "grading_metrics", "security_metrics", "generation_metrics"]
        for mt in metric_types:
            has_metric = [getattr(r, mt) for r in results if getattr(r, mt) is not None]
            if has_metric:
                aggregate[mt] = {}
                keys = has_metric[0].keys()
                for key in keys:
                    values = [m[key] for m in has_metric if key in m and isinstance(m[key], (int, float))]
                    if values:
                        aggregate[mt][key] = sum(values) / len(values)

        return aggregate
