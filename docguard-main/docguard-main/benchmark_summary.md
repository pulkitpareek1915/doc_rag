# DocGuard Evaluation Benchmark Summary

> [!WARNING]
> **DEVELOPMENT FIXTURE DATASET ONLY**
> This benchmark was executed against a heavily constrained 10-case development dataset designed strictly to validate the mathematical harness (Precision@K, FPR, P50/P95 latencies) and CI regression gates. The outputs below do **NOT** represent statistically meaningful public accuracy claims. A dataset of 100+ cases must be established before performance claims can be cited.

## Overview
This document summarizes the offline evaluation metrics for the DocGuard agent.

| Metric | Value | Sample Size | Evaluation Mode | Model | Notes |
|--------|-------|-------------|-----------------|-------|-------|
| Retrieval Precision@K | 0.0% | 2 | Offline/Mock | N/A | Mock retrieval returned hardcoded IDs against different ground truth. |
| Retrieval Hit@K | 0.0% | 2 | Offline/Mock | N/A | Needs live vectorstore integration for real stats. |
| Grader F1 | 66.7% | 2 | Offline/Mock | N/A | |
| Security Recall | 100.0% | 4 | Offline/Mock | N/A | |
| Security FPR | 100.0% | 4 | Offline/Mock | N/A | Extremely sensitive to small sample size. |
| Citation Validity | 100.0% | 2 | Offline/Mock | N/A | |
| Correct Refusal | 50.0% | 2 | Offline/Mock | N/A | |
| Unsafe Answer Rate | 0.0% | 2 | Offline/Mock | N/A | Critical metric correctly sitting at zero. |
| P50 Latency | 0.002 ms | 10 | Offline/Mock | N/A | Simulated without API overhead. |
| P95 Latency | 0.005 ms | 10 | Offline/Mock | N/A | Statistically insignificant on n=10. |
