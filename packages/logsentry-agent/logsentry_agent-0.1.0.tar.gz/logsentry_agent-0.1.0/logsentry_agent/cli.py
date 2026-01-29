from __future__ import annotations

import argparse
import socket
import sys
from datetime import datetime, timezone

from logsentry_agent.config import load_config
from logsentry_agent.fingerprint import compute_fingerprint
from logsentry_agent.health import build_health_event
from logsentry_agent.http import send_payload
from logsentry_agent.spool import SpoolQueue


def _build_envelope(config, events: list[dict]) -> dict:
    return {
        "agent": {
            "version": "0.1.0",
            "platform": sys.platform,
            "hostname": socket.gethostname(),
        },
        "host": {
            "fingerprint": compute_fingerprint(),
        },
        "events": events,
    }


def cmd_test_send(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(config.spool_path, config.spool_max_mb)
    event = {
        "source": "agent",
        "category": "system",
        "action": "test_send",
        "severity": "low",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "LogSentry agent test event",
    }
    payload = _build_envelope(config, [event])
    try:
        response = send_payload(
            endpoint=config.endpoint,
            agent_id=config.agent_id,
            secret=config.shared_secret,
            payload=payload,
            retry_max_seconds=config.retry_max_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        spool.enqueue(payload)
        print(f"Failed to send: {exc}; event spooled.")
        return 1
    if response.status_code >= 300:
        spool.enqueue(payload)
        print(f"Backend rejected ({response.status_code}); event spooled.")
        return 1
    print("Test event accepted.")
    return 0


def cmd_send_health(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(config.spool_path, config.spool_max_mb)
    metrics = {
        "spool_size": spool.pending_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload = _build_envelope(config, [build_health_event(metrics)])
    response = send_payload(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
    )
    if response.status_code >= 300:
        spool.enqueue(payload)
        return 1
    return 0


def cmd_drain_spool(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(config.spool_path, config.spool_max_mb)
    batch = spool.dequeue_batch(config.max_in_flight)
    if not batch:
        print("Spool empty.")
        return 0
    payloads = [payload for _, payload in batch]
    events = [event for item in payloads for event in item.get("events", [])]
    payload = _build_envelope(config, events)
    response = send_payload(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
    )
    if response.status_code >= 300:
        print(f"Backend rejected ({response.status_code}); keeping spool.")
        return 1
    spool.delete([row_id for row_id, _ in batch])
    print("Spool drained.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="LogSentry agent CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("test-send", help="Send a test event")
    sub.add_parser("send-health", help="Send a heartbeat event")
    sub.add_parser("drain-spool", help="Send queued events")

    args = parser.parse_args()

    if args.command == "test-send":
        raise SystemExit(cmd_test_send(args))
    if args.command == "send-health":
        raise SystemExit(cmd_send_health(args))
    if args.command == "drain-spool":
        raise SystemExit(cmd_drain_spool(args))

    parser.print_help()


if __name__ == "__main__":
    main()
