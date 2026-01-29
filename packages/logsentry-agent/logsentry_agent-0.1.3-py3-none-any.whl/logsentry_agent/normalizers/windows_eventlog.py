from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from logsentry_agent.normalize import apply_graceful_degradation

_ACTION_MAP = {
    4624: ("auth.login_success", "authentication", "low"),
    4625: ("auth.login_failed", "authentication", "medium"),
    7045: ("system.service_installed", "system", "medium"),
    4720: ("iam.account_created", "iam", "medium"),
    4728: ("iam.privilege_change", "iam", "medium"),
    4732: ("iam.privilege_change", "iam", "medium"),
    4756: ("iam.privilege_change", "iam", "medium"),
}

_CHANNEL_CATEGORY = {
    "security": "authentication",
    "system": "system",
    "application": "application",
}

_REGEXES = {
    "actor_user": re.compile(r"Account Name:\s+(?P<value>[^\r\n]+)", re.IGNORECASE),
    "target_user": re.compile(r"Target Account Name:\s+(?P<value>[^\r\n]+)", re.IGNORECASE),
    "actor_ip": re.compile(
        r"(Source Network Address|IpAddress):\s+(?P<value>[^\r\n]+)", re.IGNORECASE
    ),
    "process": re.compile(r"Process Name:\s+(?P<value>[^\r\n]+)", re.IGNORECASE),
    "service": re.compile(r"Service Name:\s+(?P<value>[^\r\n]+)", re.IGNORECASE),
}


def _extract_fields(message: str) -> dict[str, str]:
    extracted: dict[str, str] = {}
    if not message:
        return extracted
    for key, regex in _REGEXES.items():
        if match := regex.search(message):
            value = match.group("value").strip()
            if value and value != "-":
                extracted[key] = value
    return extracted


def _redact_raw(raw: dict, redacted_fields: set[str]) -> dict:
    sanitized = {}
    for key, value in raw.items():
        if key.lower() in redacted_fields:
            continue
        sanitized[key] = value
    return sanitized


def normalize_event(
    record: dict,
    *,
    allow_raw: bool = False,
    redacted_fields: set[str] | None = None,
    event_max_bytes: int | None = None,
) -> dict | None:
    event_id = int(record.get("event_id", 0))
    action, category, severity = _ACTION_MAP.get(
        event_id,
        (
            "event.generic",
            _CHANNEL_CATEGORY.get(str(record.get("channel", "")).lower(), "system"),
            "low",
        ),
    )
    message = record.get("message") or ""
    extracted = _extract_fields(message)
    event = {
        "source": "windows",
        "category": category,
        "action": action,
        "severity": severity,
        "timestamp": record.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "actor_user": extracted.get("actor_user") or record.get("user"),
        "actor_ip": extracted.get("actor_ip") or record.get("ip"),
        "target_user": extracted.get("target_user"),
        "hostname": record.get("computer"),
        "process": extracted.get("process"),
        "service": extracted.get("service"),
        "event_id": event_id,
        "channel": record.get("channel"),
        "provider": record.get("provider"),
        "message": message,
    }
    if allow_raw:
        redacted_fields = redacted_fields or set()
        event["raw_event"] = _redact_raw(record, {field.lower() for field in redacted_fields})
    normalized = apply_graceful_degradation(event)
    if event_max_bytes is not None:
        payload_size = len(json.dumps(normalized, separators=(",", ":")).encode("utf-8"))
        if payload_size > event_max_bytes:
            return None
    return normalized
