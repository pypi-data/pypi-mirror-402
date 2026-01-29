from __future__ import annotations

from datetime import datetime, timezone


def apply_graceful_degradation(event: dict, *, raw_line: str | None = None) -> dict:
    normalized = event.copy()
    if not normalized.get("timestamp"):
        normalized["timestamp"] = datetime.now(timezone.utc).isoformat()
        normalized["timestamp_quality"] = "derived"
    if "actor_user" not in normalized:
        normalized["actor_user"] = None
    if "actor_ip" not in normalized:
        normalized["actor_ip"] = None
    if raw_line and "raw_line" not in normalized:
        normalized["raw_line"] = raw_line
    return normalized
