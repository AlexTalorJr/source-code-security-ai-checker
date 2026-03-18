"""Deterministic fingerprint for finding deduplication."""

import hashlib
import re


def compute_fingerprint(file_path: str, rule_id: str, snippet: str) -> str:
    """Compute a deterministic SHA-256 fingerprint for finding deduplication.

    Normalizes inputs before hashing:
    - file_path: forward slashes, no leading ./, stripped
    - rule_id: lowercase, stripped
    - snippet: whitespace-collapsed, stripped
    """
    norm_path = file_path.replace("\\", "/").lstrip("./").strip()
    norm_rule = rule_id.lower().strip()
    norm_snippet = re.sub(r"\s+", " ", snippet).strip()

    content = f"{norm_path}:{norm_rule}:{norm_snippet}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
