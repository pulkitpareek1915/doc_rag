# DocGuard Project Claims

This document tracks the verified technical claims of the DocGuard architecture, explicitly separating them from unsupported marketing claims that have not been rigorously validated.

## Verified Claims

1. **Deterministic Pipeline:** The agent successfully orchestrates retrieval, document grading, query rewriting, security scanning, and generation sequentially via LangGraph state management.
2. **Security Quarantine:** The system reliably detects prompt injections (e.g., "Ignore all previous instructions") and quarantines adversarial documents, deterministically excluding them from the generation context window.
3. **Grounded Generation:** Enforces strict adherence to a JSON schema requiring explicit citations. Citations are deterministically validated against the clean document IDs provided; invalid citations are stripped.
4. **Safe Refusal:** The generation node gracefully refuses to answer (with a specific `refusal_reason`) when sufficient verified context is unavailable.
5. **Corrective Looping:** Automatically evaluates the relevance of retrieved documents and invokes a Claude-powered rewriting loop to improve retrieval when initial results are poor.
6. **End-to-End Observability:** Langfuse tracing captures precise spans, latencies, and token usage for the retrieval, grading, rewriting, security, and generation nodes.
7. **Production Deployment Ready:** Runs as a non-root user via a multi-stage Docker build, exposing standard FastAPI endpoints secured by Redis rate limiting and Bearer token authentication.

## Pending Claims (Future Work)

1. **Statistically Meaningful Accuracy/Recall:** The current evaluation framework runs against a 10-case development fixture dataset. It validates the *mechanics* of the evaluation harness (Precision@K, False Positive Rate, etc.), but the dataset is too small to make robust statistical claims about the model's accuracy. A dataset of 100+ cases is required.
2. **HTTP MCP Transport:** The MCP server is currently implemented and tested using standard I/O (stdio) transport. SSE/HTTP transport implementation is pending.

## Claims to Avoid

Until explicitly measured and validated, we do **not** claim:

- **"100% secure against prompt injection"** (No LLM-based system is 100% secure; DocGuard uses a layered defense-in-depth approach, but novel injections may bypass current detectors).
- **"Zero hallucinations"** (DocGuard dramatically reduces hallucinations via strict grounding, but edge cases remain possible).
- **"Millisecond-latency retrieval"** (Latency is bounded by the LLM API calls for grading and generation, not just the vector database).
- **"Production Deployed"** (The system is production-*ready*, but not currently hosted publicly).
