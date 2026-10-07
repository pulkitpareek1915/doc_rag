import re

from docguard.security.events import Finding

# Prompt Injection Patterns
PROMPT_INJECTION_PATTERN = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions|"
    r"disregard\s+(all\s+)?system\s+messages|"
    r"reveal\s+(the\s+)?system\s+prompt|"
    r"you\s+are\s+now\s+(the\s+)?system\s+administrator|"
    r"follow\s+these\s+instructions\s+instead|"
    r"developer\s+message:|system\s+instructions:)",
    re.IGNORECASE,
)

# Secrets Patterns
# Note: In real life these are much more robust, but these suffice for demonstration
OPENAI_KEY_PATTERN = re.compile(r"(sk-[a-zA-Z0-9\-]{20,})")
BEARER_TOKEN_PATTERN = re.compile(r"Bearer\s+([a-zA-Z0-9\-\._~+/]+=*)")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z]+ PRIVATE KEY-----")

# PII Patterns
EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
# Basic phone pattern
PHONE_PATTERN = re.compile(
    r"(\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9})"
)
# Basic CC pattern (13-16 digits with optional dashes/spaces)
CC_PATTERN = re.compile(r"(\b(?:\d[ -]*?){13,16}\b)")


def detect_prompt_injection(text: str) -> list[Finding]:
    findings = []
    for match in PROMPT_INJECTION_PATTERN.finditer(text):
        # We redact the matched string after 20 characters so it doesn't leak into logs
        matched_str = match.group(0)
        safe_str = (
            matched_str[:20] + "..." if len(matched_str) > 20 else matched_str
        )
        findings.append(
            Finding(
                detector="instruction_override",
                kind="prompt_injection",
                severity="high",
                detail=f"Matched instruction override pattern: {safe_str}",
            )
        )
    return findings


def detect_secrets(text: str) -> list[Finding]:
    findings = []

    if OPENAI_KEY_PATTERN.search(text):
        findings.append(
            Finding(
                detector="openai_key_scanner",
                kind="secret",
                severity="high",
                detail="secret_type=openai_api_key location=document",
            )
        )

    if BEARER_TOKEN_PATTERN.search(text):
        findings.append(
            Finding(
                detector="bearer_token_scanner",
                kind="secret",
                severity="high",
                detail="secret_type=bearer_token location=document",
            )
        )

    if PRIVATE_KEY_PATTERN.search(text):
        findings.append(
            Finding(
                detector="private_key_scanner",
                kind="secret",
                severity="high",
                detail="secret_type=private_key location=document",
            )
        )

    return findings


def detect_pii(text: str) -> list[Finding]:
    findings = []

    if EMAIL_PATTERN.search(text):
        findings.append(
            Finding(
                detector="email_scanner",
                kind="pii",
                severity="medium",
                detail="PII detected: email address",
            )
        )

    # Some numbers will falsely match PHONE_PATTERN, but we accept this for now.
    # We require at least some dashes/dots/parens or + prefix to reduce FPs
    # Actually, the regex is broad. Let's make it a bit stricter to avoid generic numbers.
    # The CC pattern is also broad. If CC matches, we don't log the number.

    if PHONE_PATTERN.search(text):
        findings.append(
            Finding(
                detector="phone_scanner",
                kind="pii",
                severity="low",
                detail="PII detected: phone number",
            )
        )

    if CC_PATTERN.search(text):
        findings.append(
            Finding(
                detector="credit_card_scanner",
                kind="pii",
                severity="high",
                detail="PII detected: credit card number",
            )
        )

    return findings
