import argparse
import json
import os

from docguard.eval.harness import EvalHarness
from docguard.eval.metrics import hit_at_k, precision_at_k, recall_at_k
from docguard.eval.models import BenchmarkResult, RetrievalCase


def retrieval_evaluator(case: RetrievalCase, live: bool) -> BenchmarkResult:
    # We use a mocked or actual execution here.
    # For now this is just a structure that simulates the evaluation call.
    # In live mode we would call the docguard retriever directly.
    return BenchmarkResult(
        case_id=case.id,
        success=True,
        retrieval_metrics={
            "precision_at_5": precision_at_k([], case.relevant_document_ids, 5),
            "recall_at_5": recall_at_k([], case.relevant_document_ids, 5),
            "hit_at_5": float(hit_at_k([], case.relevant_document_ids, 5))
        }
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Retrieval Benchmarks")
    parser.add_argument("--live", action="store_true", help="Run against real vectors/APIs")
    args = parser.parse_args()

    harness = EvalHarness(live=args.live)

    data_path = os.path.join(os.path.dirname(__file__), "../src/docguard/eval/datasets/retrieval_cases.json")
    with open(data_path) as f:
        data = json.load(f)

    dataset = [RetrievalCase(**item) for item in data]
    results = harness.run_dataset(dataset, retrieval_evaluator)

    agg = harness.aggregate_results(results)
    print(json.dumps(agg, indent=2))

if __name__ == "__main__":
    main()
