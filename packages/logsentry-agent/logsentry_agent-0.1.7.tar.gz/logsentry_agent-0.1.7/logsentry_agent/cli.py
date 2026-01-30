from __future__ import annotations

import argparse
from datetime import datetime, timezone

from logsentry_agent import __version__
from logsentry_agent.config import load_config
from logsentry_agent.envelope import build_envelope
from logsentry_agent.health import build_health_event
from logsentry_agent.http import send_payload
from logsentry_agent.run import _calculate_spool_drain_limit, run_collectors
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


def _load_spool_key(config) -> str | None:
    if not config.reliability or not config.reliability.spool_encrypt:
        return None
    if config.reliability.spool_key_path:
        return config.reliability.spool_key_path.read_text(encoding="utf-8").strip()
    return SpoolQueue.derive_key(config.shared_secret)


def cmd_test_send(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=_load_spool_key(config),
    )
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
    state = AgentState.load(config.state_path)
    payload = build_envelope(version=__version__, events=[event], seq=state.next_envelope_seq())
    state.save()
    result = send_payload(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
        security=config.security,
    )
    if result.status != "ok":
        spool.enqueue(payload, priority="low")
        status = result.response.status_code if result.response else "error"
        print(f"Backend rejected ({status}); event spooled.")
        return 1
    print("Test event accepted.")
    return 0


def cmd_send_health(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=_load_spool_key(config),
    )
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
    payload = build_envelope(
        version=__version__, events=[build_health_event(metrics)], seq=state.next_envelope_seq()
    )
    state.save()
    result = send_payload(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
        security=config.security,
    )
    if result.status != "ok":
        spool.enqueue(payload, priority="low")
        return 1
    return 0


def cmd_drain_spool(args: argparse.Namespace) -> int:
    config = load_config()
    spool = SpoolQueue(
        config.spool_path,
        config.spool_max_mb,
        config.spool_drop_policy,
        drop_priority=(config.reliability.drop_priority if config.reliability else None),
        encrypt=bool(config.reliability and config.reliability.spool_encrypt),
        encryption_key=_load_spool_key(config),
    )
    missing = _validate_credentials(config)
    if missing:
        print(missing)
        return 1
    pending_count = spool.pending_count()
    if pending_count == 0:
        print("Spool empty.")
        return 0
    percent = args.percent
    if percent is None and config.reliability:
        percent = config.reliability.spool_drain_percent
    if percent is not None and (percent < 1 or percent > 100):
        print("Percent must be between 1 and 100.")
        return 2
    limit = _calculate_spool_drain_limit(
        pending_count=pending_count,
        config=config,
        batch_size_override=config.max_in_flight,
        percent_override=percent,
    )
    batch = spool.dequeue_batch(limit)
    payloads = [payload for _, payload in batch]
    events = [event for item in payloads for event in item.get("events", [])]
    state = AgentState.load(config.state_path)
    payload = build_envelope(version=__version__, events=events, seq=state.next_envelope_seq())
    state.save()
    result = send_payload(
        endpoint=config.endpoint,
        agent_id=config.agent_id,
        secret=config.shared_secret,
        payload=payload,
        retry_max_seconds=config.retry_max_seconds,
        security=config.security,
    )
    if result.status != "ok":
        status = result.response.status_code if result.response else "error"
        print(f"Backend rejected ({status}); keeping spool.")
        return 1
    spool.delete([row_id for row_id, _ in batch])
    print("Spool drained.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="LogSentry agent CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("test-send", help="Send a test event")
    sub.add_parser("send-health", help="Send a heartbeat event")
    drain_parser = sub.add_parser("drain-spool", help="Send queued events")
    drain_parser.add_argument(
        "--percent",
        type=int,
        help="Drain only this percentage of the current spool (1-100).",
    )
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
