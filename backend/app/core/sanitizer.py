import os
import re
from typing import Optional

# Control characters to strip (excluding \t (9), \n (10), \r (13))
CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Common SQL injection signatures for anomaly logging
SQLI_SIGNATURES = [
    re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.IGNORECASE),
    re.compile(r"\b(union\s+select|select\s+.*\s+from|insert\s+into|drop\s+table)\b", re.IGNORECASE),
    re.compile(r"(\b(or|and)\b\s+[\'\"]?\w+[\'\"]?\s*=\s*[\'\"]?\w+[\'\"]?)", re.IGNORECASE)
]

def sanitize_text(text: Optional[str], max_length: int = 10000) -> str:
    """
    Sanitizes user input by stripping null bytes and dangerous control characters,
    normalizing whitespace, and truncating to maximum allowed length.
    """
    if not text:
        return ""
    # Strip null bytes and non-printable control characters
    cleaned = CONTROL_CHAR_REGEX.sub("", text)
    # Truncate to maximum length bound
    return cleaned[:max_length].strip()

def validate_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Verifies that target_path strictly resolves inside base_dir.
    Guards against path traversal (../, ..\\) attacks.
    """
    if not base_dir or not target_path:
        return False
    try:
        resolved_base = os.path.realpath(os.path.abspath(base_dir))
        resolved_target = os.path.realpath(os.path.abspath(target_path))
        # Ensure target starts with the base directory path
        return os.path.commonpath([resolved_base]) == os.path.commonpath([resolved_base, resolved_target])
    except (ValueError, OSError):
        return False

def check_sqli_anomaly(value: str) -> bool:
    """
    Checks if a string exhibits explicit SQL injection heuristic signatures.
    Note: SURAKSHA AI uses parameterized SQLAlchemy queries exclusively;
    this helper is used for proactive threat intelligence and SOC audit logging.
    """
    if not value or len(value) < 4:
        return False
    return any(pattern.search(value) is not None for pattern in SQLI_SIGNATURES)

