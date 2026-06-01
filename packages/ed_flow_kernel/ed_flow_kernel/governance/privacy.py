"""Public-safe privacy checks."""

from __future__ import annotations

import re
from typing import Any


FORBIDDEN_PUBLIC_TERMS = ["PATIENT_PHN", "PATIENT_ULI", "PATIENT_CHART", "PATIENT_ID", "PATIENT_BIRTHDATE"]
PHI_LIKE_PATTERNS = [
    re.compile(r"\b\d{9,10}\b"),
    re.compile(r"\bPHN\b", re.IGNORECASE),
    re.compile(r"\bULI\b", re.IGNORECASE),
]


def public_payload_has_phi_like_values(payload: Any) -> bool:
    """Return True when a public artifact appears to contain identifiers."""

    text = str(payload)
    if any(term in text for term in FORBIDDEN_PUBLIC_TERMS):
        return True
    return any(pattern.search(text) for pattern in PHI_LIKE_PATTERNS)
