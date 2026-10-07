from dataclasses import dataclass


@dataclass
class Finding:
    detector: str
    kind: str
    severity: str
    detail: str
