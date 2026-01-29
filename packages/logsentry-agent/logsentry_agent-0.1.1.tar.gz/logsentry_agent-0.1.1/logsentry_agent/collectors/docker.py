from __future__ import annotations

import json
from datetime import datetime, timezone

from logsentry_agent.normalize import apply_graceful_degradation


def parse_line(line: str, *, container: str, image: str | None = None) -> dict | None:
    line = line.strip()
    if not line:
        return None
    payload: dict
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        payload = {"message": line}
    event = {
        "source": f"docker:{container}",
        "category": "application",
        "action": "container.log",
        "severity": "low",
        "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "container_name": container,
        "image": image,
        "message": payload.get("message") or payload.get("log"),
    }
    return apply_graceful_degradation(event, raw_line=line)
