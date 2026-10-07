# Security Policy

DocGuard is an open-source demonstration project focusing on Secure Document Intelligence and defensive RAG architectures.

## Supported Security Posture

DocGuard implements a defense-in-depth architecture, utilizing programmatic and LLM-assisted tools to quarantine adversarial prompt injections, PII, and credentials before they enter generative contexts. 

However, **DocGuard makes no claims of absolute security**. LLMs are inherently non-deterministic, and novel adversarial injections may bypass the current detection boundaries. This project is intended to demonstrate a hardened architectural baseline for enterprise RAG, not to serve as an impenetrable commercial security appliance out-of-the-box.

## Reporting a Vulnerability

If you discover a security vulnerability or novel prompt-injection bypass in DocGuard, please **do not submit the vulnerability or exploit payloads through public GitHub issues**. 

Instead, please responsibly disclose it by emailing the maintainer directly or opening a private GitHub Security Advisory if available. We will work to patch the detection boundary appropriately.
