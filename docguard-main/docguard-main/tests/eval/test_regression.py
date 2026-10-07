import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.check_regression import check_regression


@pytest.fixture
def temp_json_files(tmp_path):
    def _create_files(current_data, baseline_data, threshold_data=None):
        c_path = tmp_path / "current.json"
        b_path = tmp_path / "baseline.json"

        with open(c_path, "w") as f:
            json.dump(current_data, f)
        with open(b_path, "w") as f:
            json.dump(baseline_data, f)

        t_path = None
        if threshold_data is not None:
            t_path = tmp_path / "thresholds.json"
            with open(t_path, "w") as f:
                json.dump(threshold_data, f)

        return str(c_path), str(b_path), str(t_path) if t_path else None
    return _create_files

def test_regression_passes_when_metrics_unchanged(temp_json_files):
    metrics = {"retrieval": {"hit_at_5": 0.82}}
    c_path, b_path, t_path = temp_json_files(metrics, metrics)
    assert check_regression(c_path, b_path, t_path) is True

def test_regression_fails_when_retrieval_regresses(temp_json_files):
    base = {"retrieval": {"hit_at_5": 0.82}}
    curr = {"retrieval": {"hit_at_5": 0.50}}
    c_path, b_path, t_path = temp_json_files(curr, base)
    assert check_regression(c_path, b_path, t_path) is False

def test_regression_fails_when_security_recall_drops(temp_json_files):
    base = {"security": {"recall": 0.95}}
    curr = {"security": {"recall": 0.80}}
    c_path, b_path, t_path = temp_json_files(curr, base)
    assert check_regression(c_path, b_path, t_path) is False

def test_regression_fails_when_unsafe_answer_rate_rises(temp_json_files):
    base = {"generation": {"unsafe_answer_rate": 0.01}}
    curr = {"generation": {"unsafe_answer_rate": 0.10}}
    c_path, b_path, t_path = temp_json_files(curr, base)
    assert check_regression(c_path, b_path, t_path) is False

def test_regression_handles_missing_metric(temp_json_files):
    base = {"retrieval": {"hit_at_5": 0.82, "precision": 0.9}}
    curr = {"retrieval": {"hit_at_5": 0.82}}
    c_path, b_path, t_path = temp_json_files(curr, base)
    assert check_regression(c_path, b_path, t_path) is False

def test_regression_handles_empty_baseline(temp_json_files):
    base = {"status": "pending"}
    curr = {"retrieval": {"hit_at_5": 0.82}}
    c_path, b_path, t_path = temp_json_files(curr, base)
    assert check_regression(c_path, b_path, t_path) is True
