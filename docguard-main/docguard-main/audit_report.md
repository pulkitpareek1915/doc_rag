# DocGuard Stage 17 Final Security & Architecture Audit Report

## Executive Summary
A comprehensive security and architectural audit was performed against the DocGuard system across its FastAPI, LangGraph, Authentication, MCP, Cache, and Docker components. The overarching architecture is extremely robust, honoring all major security invariants: untrusted data remains isolated, quarantined data never hits the LLM, and caching correctly avoids storing raw context.

However, two findings require immediate attention to stabilize the CI pipeline and ensure proper observability in the rewrite layer. 

---

## 🔴 Must-Fix Items (High/Critical)

### 1. CI Pipeline Breaks on Authentication Integration (HIGH)
- **Location:** `tests/api/test_query.py`, `tests/api/test_ingest.py`
- **Evidence:** Running the test suite yields 8 failed API tests.
- **Impact:** The `HTTPBearer` requirement from Stage 15 was injected into the FastAPI router, but the unit tests were not updated to either mock `settings.auth_enabled = False` or provide a valid auth token. The pipeline is currently failing on CI.
- **Recommendation:** Override the `settings.auth_enabled` environment config or mock the dependency in tests for `/query` and `/documents/ingest` to ensure test stability.

---

## 🟠 Should-Fix Items (Medium)

### 2. NameError in Query Rewriter Swallows Langfuse Tracing (MEDIUM)
- **Location:** `src/docguard/agent/nodes/rewrite.py`
- **Evidence:** `get_client()` is called around line 69 but was never imported at the top of the file. Because it is wrapped in an `except Exception: pass` block, the error silently fails instead of crashing the app.
- **Impact:** Langfuse token usage for Claude's rewriting logic is silently being dropped.
- **Recommendation:** Add `from langfuse import get_client` to `rewrite.py`.

---

## 🟢 Passed Controls & Observations (INFO)

### 3. Architecture & Graph Security (PASSED)
- **Status:** EXCELLENT. 
- **Notes:** The LangGraph logic in `graph.py` rigidly enforces that `security_node` executes before `generate_node`. The `security_node` successfully overwrites `relevant_docs` with ONLY `clean_docs`, permanently separating quarantined content from the generation prompt. Empty contexts gracefully trigger the `refuse` node.

### 4. Authentication & Rate-Limiting (PASSED)
- **Status:** EXCELLENT.
- **Notes:** Fails closed if token is missing but auth is enabled. The token is hashed with SHA-256 before being used as a Redis rate-limit key, safely preventing plaintext tokens from resting in Redis memory. The rate limiter correctly pipelined the atomic `INCR/EXPIRE` logic to prevent race conditions. 

### 5. Cache Data Safety (PASSED)
- **Status:** EXCELLENT.
- **Notes:** The caching layer in `services/query.py` strictly pulls the final `dict(answer, citations, refusal_reason)`. It NEVER serializes or caches the raw document context, effectively isolating prompt injections from caching mechanisms.

### 6. MCP Integration (PASSED)
- **Status:** EXCELLENT.
- **Notes:** The MCP server (`mcp/server.py`) acts exclusively as an adapter, directly invoking the single-source-of-truth `execute_query(..., source="mcp")`. It does not invent its own generation logic or bypass security.

### 7. Docker Hardening (PASSED)
- **Status:** EXCELLENT.
- **Notes:** Implements a true multi-stage build. Final runtime drops root privileges explicitly via `USER docguard` and limits installed OS dependencies.

### 8. Evaluation Framework (PASSED)
- **Status:** EXCELLENT.
- **Notes:** Live evaluation is strictly gated behind an explicit `--live` flag, heavily mitigating accidental LLM billing drains. The current evaluation sample size is noted as a "Development Fixture" and is safely segregated from resume/public documentation claims.

---

## Final Risk Assessment
**Risk Level:** **LOW**. 
The system enforces its safety bounds properly. No prompt injection paths or bypasses exist that can force poisoned content into the generation layer. The few identified issues are purely related to testing hygiene (CI fixes) and observability tracking (Langfuse import).
