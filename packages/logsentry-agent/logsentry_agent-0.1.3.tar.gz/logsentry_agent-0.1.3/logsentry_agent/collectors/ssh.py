from __future__ import annotations

import re
from datetime import datetime, timezone

from logsentry_agent.normalize import apply_graceful_degradation

FAILED_RE = re.compile(r"Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>\S+)")
SUCCESS_RE = re.compile(r"Accepted (password|publickey) for (?P<user>\S+) from (?P<ip>\S+)")


def parse_line(line: str) -> dict | None:
    if match := FAILED_RE.search(line):
        return _build_event(match.group("user"), match.group("ip"), "login_failed")
    if match := SUCCESS_RE.search(line):
        return _build_event(match.group("user"), match.group("ip"), "login_success")
    return None


def _build_event(user: str, ip: str, action: str) -> dict:
    event = {
        "source": "ssh",
        "category": "authentication",
        "action": action,
        "severity": "medium" if action == "login_failed" else "low",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_user": user,
        "actor_ip": ip,
    }
    return apply_graceful_degradation(event)
