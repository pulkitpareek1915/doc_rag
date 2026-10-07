
def precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if not retrieved_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_retrieved = [doc_id for doc_id in top_k if doc_id in relevant_ids]
    return len(relevant_retrieved) / len(top_k)

def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if not relevant_ids:
        return 1.0  # If nothing is relevant, we recalled 100% of it
    if not retrieved_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_retrieved = [doc_id for doc_id in top_k if doc_id in relevant_ids]
    return len(relevant_retrieved) / len(relevant_ids)

def hit_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> bool:
    if not relevant_ids:
        return True
    if not retrieved_ids or k <= 0:
        return False
    top_k = retrieved_ids[:k]
    return any(doc_id in relevant_ids for doc_id in top_k)

def classification_metrics(actual: list[bool], expected: list[bool]) -> dict[str, float]:
    if len(actual) != len(expected):
        raise ValueError("Actual and expected lists must have the same length.")

    tp = sum(1 for a, e in zip(actual, expected, strict=True) if a and e)
    tn = sum(1 for a, e in zip(actual, expected, strict=True) if not a and not e)
    fp = sum(1 for a, e in zip(actual, expected, strict=True) if a and not e)
    fn = sum(1 for a, e in zip(actual, expected, strict=True) if not a and e)

    total = len(actual)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def citation_validity(generated_citations: list[str], provided_context_ids: list[str]) -> float:
    if not generated_citations:
        return 1.0 # No citations generated is technically valid (0% invalid)

    valid_count = sum(1 for c in generated_citations if c in provided_context_ids)
    return valid_count / len(generated_citations)

def citation_coverage(generated_citations: list[str], provided_context_ids: list[str]) -> float:
    if not provided_context_ids:
        return 1.0

    covered_count = sum(1 for c in provided_context_ids if c in generated_citations)
    return covered_count / len(provided_context_ids)

def rewrite_recovery_rate(failed_retrieval_queries: int, recovered_queries: int) -> float:
    if failed_retrieval_queries <= 0:
        return 0.0
    return recovered_queries / failed_retrieval_queries

def false_positive_rate(actual: list[bool], expected: list[bool]) -> float:
    if len(actual) != len(expected):
        raise ValueError("Actual and expected lists must have the same length.")
    fp = sum(1 for a, e in zip(actual, expected, strict=True) if a and not e)
    tn = sum(1 for a, e in zip(actual, expected, strict=True) if not a and not e)
    if fp + tn == 0:
        return 0.0
    return fp / (fp + tn)

def calculate_percentile(latencies: list[float], percentile: float) -> float:
    if not latencies:
        return 0.0
    sorted_lats = sorted(latencies)
    index = round((len(sorted_lats) - 1) * percentile)
    return sorted_lats[index]
