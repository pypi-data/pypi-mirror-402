from __future__ import annotations

from datetime import datetime, timezone

from logsentry_agent.normalize import apply_graceful_degradation

LOGIN_FAILURE_IDS = {4625}
LOGIN_SUCCESS_IDS = {4624}


def normalize_event(record: dict) -> dict:
    event_id = int(record.get("event_id", 0))
    action = "event"
    severity = "low"
    if event_id in LOGIN_FAILURE_IDS:
        action = "login_failed"
        severity = "medium"
    elif event_id in LOGIN_SUCCESS_IDS:
        action = "login_success"
        severity = "low"
    event = {
        "source": "windows",
        "category": "authentication",
        "action": action,
        "severity": severity,
        "timestamp": record.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "actor_user": record.get("user"),
        "actor_ip": record.get("ip"),
        "event_id": event_id,
        "channel": record.get("channel"),
    }
    return apply_graceful_degradation(event)
