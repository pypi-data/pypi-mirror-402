from __future__ import annotations

from datetime import datetime, timezone


def build_health_event(metrics: dict) -> dict:
    return {
        "source": "agent",
        "category": "system",
        "action": "agent.health",
        "severity": "low",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
