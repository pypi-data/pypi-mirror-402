from __future__ import annotations

import socket
import sys

from logsentry_agent.fingerprint import compute_fingerprint


def build_envelope(*, version: str, events: list[dict]) -> dict:
    return {
        "agent": {
            "version": version,
            "platform": sys.platform,
            "hostname": socket.gethostname(),
        },
        "host": {
            "fingerprint": compute_fingerprint(),
        },
        "events": events,
    }
