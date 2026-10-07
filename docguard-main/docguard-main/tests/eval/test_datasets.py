import json
import os

from docguard.eval.models import GenerationCase, GradingCase, RetrievalCase, SecurityCase

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "../../src/docguard/eval/datasets")

def load_dataset(filename: str) -> list:
    filepath = os.path.join(DATASETS_DIR, filename)
    with open(filepath) as f:
        return list(json.load(f))

def test_retrieval_dataset_schema() -> None:
    data = load_dataset("retrieval_cases.json")
    for item in data:
        # Pydantic will raise ValidationError if schema is wrong
        RetrievalCase(**item)

def test_grading_dataset_schema() -> None:
    data = load_dataset("grading_cases.json")
    for item in data:
        case = GradingCase(**item)
        assert case.expected_grade in ("relevant", "irrelevant")

def test_security_dataset_schema() -> None:
    data = load_dataset("security_cases.json")
    for item in data:
        case = SecurityCase(**item)
        assert case.expected_action in ("pass", "quarantine")
        assert case.category in ("clean", "prompt_injection", "pii", "secret", "hard_negative")

def test_generation_dataset_schema() -> None:
    data = load_dataset("generation_cases.json")
    for item in data:
        case = GenerationCase(**item)
        assert case.expected_behavior in ("answer", "refuse")
