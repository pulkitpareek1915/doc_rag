import argparse
import json
import os

from docguard.eval.harness import EvalHarness
from docguard.eval.models import BenchmarkResult, GenerationCase


def end_to_end_evaluator(case: GenerationCase, live: bool) -> BenchmarkResult:
    # Simulator
    return BenchmarkResult(
        case_id=case.id,
        success=True,
        generation_metrics={
            "faithfulness": 1.0 # Placeholder
        }
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Run End-to-End Benchmarks")
    parser.add_argument("--live", action="store_true", help="Run against real graph APIs")
    args = parser.parse_args()

    harness = EvalHarness(live=args.live)

    data_path = os.path.join(os.path.dirname(__file__), "../src/docguard/eval/datasets/generation_cases.json")
    with open(data_path) as f:
        data = json.load(f)

    dataset = [GenerationCase(**item) for item in data]
    results = harness.run_dataset(dataset, end_to_end_evaluator)

    agg = harness.aggregate_results(results)
    print(json.dumps(agg, indent=2))

if __name__ == "__main__":
    main()
