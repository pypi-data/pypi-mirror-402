from __future__ import annotations

import random
import time
from collections import deque
from datetime import datetime, timezone

from logsentry_agent.collectors.windows_eventlog import (
    WindowsEventLogReader,
    should_filter_since,
)
from logsentry_agent.config import AgentConfig
from logsentry_agent.envelope import build_envelope
from logsentry_agent.http import send_payload
from logsentry_agent.normalizers.windows_eventlog import normalize_event
from logsentry_agent.spool import SpoolQueue
from logsentry_agent.state import AgentState


def run_collectors(*, config: AgentConfig, once: bool = False, debug: bool = False) -> int:
    state = AgentState.load(config.state_path)
    spool = SpoolQueue(config.spool_path, config.spool_max_mb, config.spool_drop_policy)
    if not config.agent_id or not config.shared_secret:
        print("Missing required agent configuration: agent_id, shared_secret")
        return 1

    windows_collector = None
    if "windows_eventlog" in config.sources or "windows" in config.sources:
        windows_collector = WindowsEventLogReader(config.windows_eventlog, state)
    if windows_collector is None:
        print("No supported collectors configured. Add `windows_eventlog` to sources.")
        return 1

    queue: deque[dict] = deque()
    backoff_seconds = 0.0
    last_flush = time.monotonic()
    while True:
        poll_start = time.monotonic()
        if windows_collector:
            try:
                records, stats = windows_collector.poll()
            except RuntimeError as exc:
                print(str(exc))
                return 1
            for record in records:
                if (
                    config.windows_eventlog.start_mode == "since_minutes"
                    and not state.get_checkpoint(record["channel"])
                ):
                    if should_filter_since(record, config.windows_eventlog.since_minutes):
                        continue
                normalized = normalize_event(
                    record,
                    allow_raw=config.allow_raw,
                    redacted_fields=set(config.windows_eventlog.redacted_fields),
                    event_max_bytes=config.windows_eventlog.event_max_bytes,
                )
                if normalized is None:
                    stats.dropped_too_large += 1
                    continue
                if len(queue) < config.queue_max_size:
                    queue.append(normalized)
                else:
                    time.sleep(config.windows_eventlog.poll_interval_seconds)
                    break
            state.update_stats(
                "windows_eventlog",
                {
                    "events_collected_last_poll": stats.events_collected,
                    "access_denied": stats.access_denied,
                    "dropped_too_large": stats.dropped_too_large,
                    "last_bookmarks": stats.last_bookmarks,
                    "last_poll": datetime.now(timezone.utc).isoformat(),
                    "spool_size": spool.pending_count(),
                },
            )
            state.save()
            if debug:
                print(
                    "Windows collector stats:",
                    {
                        "events_collected": stats.events_collected,
                        "last_bookmarks": stats.last_bookmarks,
                        "access_denied": stats.access_denied,
                        "queue_size": len(queue),
                        "spool_size": spool.pending_count(),
                    },
                )

        batch_limit = min(config.batch_size, config.max_in_flight)
        should_flush = (
            len(queue) >= batch_limit
            or (time.monotonic() - last_flush) * 1000 >= config.flush_interval_ms
        )
        if queue and should_flush:
            batch = [queue.popleft() for _ in range(min(batch_limit, len(queue)))]
            payload = build_envelope(version="0.1.2", events=batch)
            try:
                response = send_payload(
                    endpoint=config.endpoint,
                    agent_id=config.agent_id,
                    secret=config.shared_secret,
                    payload=payload,
                    retry_max_seconds=config.retry_max_seconds,
                )
            except Exception:  # noqa: BLE001
                response = None
            if response is None or response.status_code >= 300:
                spool.enqueue(payload)
                backoff_seconds = max(
                    1.0,
                    min(backoff_seconds * 2 or 1.0, config.retry_max_seconds),
                )
                time.sleep(backoff_seconds + random.random())
            else:
                backoff_seconds = 0.0
            last_flush = time.monotonic()

        if once:
            break
        elapsed = time.monotonic() - poll_start
        sleep_for = max(config.windows_eventlog.poll_interval_seconds - elapsed, 0.0)
        time.sleep(sleep_for)

    if queue:
        batch = list(queue)
        payload = build_envelope(version="0.1.2", events=batch)
        try:
            response = send_payload(
                endpoint=config.endpoint,
                agent_id=config.agent_id,
                secret=config.shared_secret,
                payload=payload,
                retry_max_seconds=config.retry_max_seconds,
            )
        except Exception:  # noqa: BLE001
            spool.enqueue(payload)
            return 1
        if response.status_code >= 300:
            spool.enqueue(payload)
            return 1
    return 0
