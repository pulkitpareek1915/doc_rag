from docguard.security.detectors import (
    detect_pii,
    detect_prompt_injection,
    detect_secrets,
)
from docguard.security.events import Finding


def scan_document(content: str) -> list[Finding]:
    findings = []
    findings.extend(detect_prompt_injection(content))
    findings.extend(detect_secrets(content))
    findings.extend(detect_pii(content))
    return findings
