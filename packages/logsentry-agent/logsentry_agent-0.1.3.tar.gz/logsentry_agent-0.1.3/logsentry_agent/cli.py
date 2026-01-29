from __future__ import annotations

import argparse
from datetime import datetime, timezone

from logsentry_agent.config import load_config
from logsentry_agent.envelope import build_envelope
from logsentry_agent.health import build_health_event
from logsentry_agent.http import send_payload
from logsentry_agent.run import run_collectors
from logsentry_agent.spool import SpoolQueue
from logsentry_agent.state import AgentState


def _validate_credentials(config) -> str | None:
    missing = []
    if not config.agent_id:
        missing.append("agent_id")
    if not config.shared_secret:
        missing.append("shared_secret")
    if missing:
        return "Missing required agent configuration: " + ", ".join(missing)
    return None


def cmd_test_send(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(config.spool_path, config.spool_max_mb, config.spool_drop_policy)
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    event = {
        "source": "agent",
        "category": "system",
        "action": "test_send",
        "severity": "low",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "LogSentry agent test event",
    }
    payload = build_envelope(version="0.1.2", events=[event])
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
    spool = SpoolQueue(config.spool_path, config.spool_max_mb, config.spool_drop_policy)
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    metrics = {
        "spool_size": spool.pending_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    state = AgentState.load(config.state_path)
    if state.stats.get("windows_eventlog"):
        metrics["windows_eventlog"] = state.stats["windows_eventlog"]
    payload = build_envelope(version="0.1.2", events=[build_health_event(metrics)])
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
    spool = SpoolQueue(config.spool_path, config.spool_max_mb, config.spool_drop_policy)
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    batch = spool.dequeue_batch(config.max_in_flight)
    if not batch:
        print("Spool empty.")
        return 0
    payloads = [payload for _, payload in batch]
    events = [event for item in payloads for event in item.get("events", [])]
    payload = build_envelope(version="0.1.2", events=events)
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
    run_parser = sub.add_parser("run", help="Run configured collectors")
    run_parser.add_argument("--once", action="store_true", help="Collect once and exit")
    run_parser.add_argument("--debug", action="store_true", help="Print collector stats")

    args = parser.parse_args()

    if args.command == "test-send":
        raise SystemExit(cmd_test_send(args))
    if args.command == "send-health":
        raise SystemExit(cmd_send_health(args))
    if args.command == "drain-spool":
        raise SystemExit(cmd_drain_spool(args))
    if args.command == "run":
        raise SystemExit(run_collectors(config=load_config(), once=args.once, debug=args.debug))

    parser.print_help()


if __name__ == "__main__":
    main()
