from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from logsentry_agent.normalize import apply_graceful_degradation

COMBINED_RE = re.compile(
    r"(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] "
    r"\"(?P<method>\S+) (?P<path>\S+) [^\"]+\" "
    r"(?P<status>\d{3}) (?P<size>\d+|-)"
)

TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None
        return normalize_json(payload)
    match = COMBINED_RE.match(line)
    if not match:
        return None
    data = match.groupdict()
    timestamp = _parse_time(data.get("time"))
    category = "access" if data.get("path") in {"/admin", "/wp-admin", "/.env"} else "network"
    event = {
        "source": "nginx",
        "category": category,
        "action": "http_request",
        "severity": _severity_from_status(data.get("status")),
        "timestamp": timestamp,
        "actor_ip": data.get("ip"),
        "actor_user": None if data.get("user") == "-" else data.get("user"),
        "target_path": data.get("path"),
        "target_service": "nginx",
        "status": int(data.get("status")),
    }
    return apply_graceful_degradation(event, raw_line=line)


def normalize_json(payload: dict) -> dict:
    status = payload.get("status") or payload.get("status_code")
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    path = payload.get("request_uri") or payload.get("path")
    category = (
        "access" if path in {"/admin", "/wp-admin", "/.env"} else payload.get("category", "network")
    )
    event = {
        "source": "nginx",
        "category": category,
        "action": "http_request",
        "severity": _severity_from_status(status),
        "timestamp": timestamp,
        "actor_ip": payload.get("remote_addr") or payload.get("client_ip"),
        "actor_user": payload.get("remote_user"),
        "target_path": path,
        "target_service": payload.get("host") or "nginx",
        "status": status,
    }
    return apply_graceful_degradation(event)


def _parse_time(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.strptime(value, TIME_FORMAT)
        return parsed.astimezone(timezone.utc).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()


def _severity_from_status(status: str | int | None) -> str:
    try:
        status_int = int(status)
    except (TypeError, ValueError):
        return "low"
    if status_int >= 500:
        return "high"
    if status_int >= 400:
        return "medium"
    return "low"
