import argparse
import json
import sys


def check_regression(current_path, baseline_path, thresholds_path=None):
    with open(baseline_path) as f:
        baseline = json.load(f)

    if baseline.get("status") == "pending":
        print("Baseline is dormant/pending. Skipping regression check.")
        return True

    with open(current_path) as f:
        current = json.load(f)

    thresholds = {}
    if thresholds_path:
        with open(thresholds_path) as f:
            thresholds = json.load(f)

    passed = True
    print("=== Regression Check ===")

    def flatten(d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    curr_flat = flatten(current)
    base_flat = flatten(baseline)
    thresh_flat = flatten(thresholds) if thresholds else {}

    for key, base_val in base_flat.items():
        if key not in curr_flat:
            print(f"❌ Metric missing in current: {key}")
            passed = False
            continue

        curr_val = curr_flat[key]
        if not isinstance(base_val, (int, float)) or not isinstance(curr_val, (int, float)):
            continue

        threshold = thresh_flat.get(key, 0.05) # 5% default max regression

        lower_is_better = any(term in key for term in ['unsafe', 'false_positive', 'latency', 'error'])

        if lower_is_better:
            if curr_val > base_val + threshold:
                print(f"❌ Regression on {key}: {curr_val} > {base_val} + {threshold}")
                passed = False
            else:
                print(f"✅ {key}: {curr_val} (baseline: {base_val})")
        else:
            if curr_val < base_val - threshold:
                print(f"❌ Regression on {key}: {curr_val} < {base_val} - {threshold}")
                passed = False
            else:
                print(f"✅ {key}: {curr_val} (baseline: {base_val})")

    return passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--thresholds", required=False)
    args = parser.parse_args()

    if not check_regression(args.current, args.baseline, args.thresholds):
        sys.exit(1)
