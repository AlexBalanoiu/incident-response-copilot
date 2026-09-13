import re

FORBIDDEN_PATTERNS = [
    (r"kubectl\s+delete\s+namespace", "Deleting a namespace is never an acceptable proposed fix"),
    (r"kubectl\s+delete\s+.*--force", "Forced deletion bypasses graceful shutdown and is disallowed"),
    (r"kubectl\s+delete\s+pv\b", "Deleting a PersistentVolume risks unrecoverable data loss"),
    (r"kubectl\s+delete\s+pvc\b", "Deleting a PersistentVolumeClaim risks unrecoverable data loss"),
    (r"kubectl\s+drain\b", "Draining nodes is an infrastructure-wide action outside fix-proposer scope"),
    (r"DROP\s+(TABLE|DATABASE)", "Dropping tables/databases is never an acceptable proposed fix"),
    (r"rm\s+-rf\s+/", "Destructive filesystem commands are disallowed"),
    (r"kubectl\s+delete\s+.*--all\b", "Bulk deletion across all resources is disallowed"),
]


def validate_fix_safety(fix_text: str) -> dict:
    """
    Check a proposed fix (YAML manifest and/or shell commands) against the
    safety policy. This is a hard rule check, not a judgment call for the LLM.

    Returns:
        {"status": "safe", "violations": []}
        or
        {"status": "unsafe", "violations": [{"pattern": <str>, "reason": <str>}, ...]}
    """
    violations = []
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, fix_text, re.IGNORECASE):
            violations.append({"pattern": pattern, "reason": reason})

    return {
        "status": "unsafe" if violations else "safe",
        "violations": violations,
    }