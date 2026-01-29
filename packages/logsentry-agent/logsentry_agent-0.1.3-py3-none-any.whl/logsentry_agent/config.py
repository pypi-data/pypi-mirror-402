from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _default_config_path() -> Path:
    if os.name == "nt":
        program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "LogSentry" / "agent.yml"
    return Path("/etc/logsentry/agent.yml")


def _default_spool_path() -> Path:
    if os.name == "nt":
        program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "LogSentry" / "spool.db"
    return Path("/var/lib/logsentry/spool.db")


def _default_state_path() -> Path:
    if os.name == "nt":
        program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "LogSentry" / "state.json"
    return Path("/var/lib/logsentry/state.json")


DEFAULT_CONFIG_PATH = _default_config_path()


@dataclass
class AgentConfig:
    agent_id: str
    shared_secret: str
    endpoint: str
    spool_path: Path
    spool_max_mb: int
    retry_max_seconds: int
    max_in_flight: int
    batch_size: int
    flush_interval_ms: int
    queue_max_size: int
    spool_drop_policy: str
    state_path: Path
    sources: list[str] = field(default_factory=list)
    allow_raw: bool = False
    windows_eventlog: "WindowsEventLogConfig" | None = None


@dataclass
class WindowsEventLogConfig:
    channels: list[str] = field(default_factory=lambda: ["Security", "System", "Application"])
    poll_interval_seconds: int = 2
    start_mode: str = "tail"
    since_minutes: int = 10
    from_record: int | None = None
    level_min: str = "Information"
    event_id_allow: list[int] = field(default_factory=list)
    event_id_deny: list[int] = field(default_factory=list)
    provider_allow: list[str] = field(default_factory=list)
    provider_deny: list[str] = field(default_factory=list)
    checkpoint_path: Path = field(default_factory=_default_state_path)
    max_events_per_poll: int = 200
    event_max_bytes: int = 32768
    redacted_fields: list[str] = field(
        default_factory=lambda: ["command_line", "sid", "token", "logon_guid"]
    )


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def load_config(path: Path | None = None) -> AgentConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    file_config = _load_yaml(config_path)
    env_config = {
        "agent_id": os.getenv("LOGSENTRY_AGENT_ID"),
        "shared_secret": os.getenv("LOGSENTRY_AGENT_SECRET"),
        "endpoint": os.getenv("LOGSENTRY_ENDPOINT"),
        "spool_path": os.getenv("LOGSENTRY_SPOOL_PATH"),
        "spool_max_mb": os.getenv("LOGSENTRY_SPOOL_MAX_MB"),
        "retry_max_seconds": os.getenv("LOGSENTRY_RETRY_MAX_SECONDS"),
        "max_in_flight": os.getenv("LOGSENTRY_MAX_IN_FLIGHT"),
        "batch_size": os.getenv("LOGSENTRY_BATCH_SIZE"),
        "flush_interval_ms": os.getenv("LOGSENTRY_FLUSH_INTERVAL_MS"),
        "queue_max_size": os.getenv("LOGSENTRY_QUEUE_MAX_SIZE"),
        "spool_drop_policy": os.getenv("LOGSENTRY_SPOOL_DROP_POLICY"),
        "state_path": os.getenv("LOGSENTRY_STATE_PATH"),
        "sources": os.getenv("LOGSENTRY_SOURCES"),
        "allow_raw": os.getenv("LOGSENTRY_ALLOW_RAW"),
    }

    def _get(key, default=None):
        value = env_config.get(key)
        if value is not None:
            return value
        return file_config.get(key, default)

    sources = _get("sources", [])
    if isinstance(sources, str):
        sources = [item.strip() for item in sources.split(",") if item.strip()]

    state_path_raw = _get("state_path")
    state_path_value = Path(state_path_raw) if state_path_raw else _default_state_path()
    windows_config = file_config.get("windows_eventlog", {}) or {}
    if not state_path_raw and windows_config.get("checkpoint_path"):
        state_path_value = Path(windows_config["checkpoint_path"])
    checkpoint_path_value = windows_config.get("checkpoint_path", state_path_value)
    windows_eventlog = WindowsEventLogConfig(
        channels=windows_config.get("channels", ["Security", "System", "Application"]),
        poll_interval_seconds=int(windows_config.get("poll_interval_seconds", 2)),
        start_mode=windows_config.get("start_mode", "tail"),
        since_minutes=int(windows_config.get("since_minutes", 10)),
        from_record=(
            int(windows_config["from_record"]) if windows_config.get("from_record") else None
        ),
        level_min=windows_config.get("level_min", "Information"),
        event_id_allow=[int(item) for item in windows_config.get("event_id_allow", [])],
        event_id_deny=[int(item) for item in windows_config.get("event_id_deny", [])],
        provider_allow=windows_config.get("provider_allow", []),
        provider_deny=windows_config.get("provider_deny", []),
        checkpoint_path=Path(checkpoint_path_value),
        max_events_per_poll=int(windows_config.get("max_events_per_poll", 200)),
        event_max_bytes=int(windows_config.get("event_max_bytes", 32768)),
        redacted_fields=windows_config.get(
            "redacted_fields",
            ["command_line", "sid", "token", "logon_guid"],
        ),
    )

    return AgentConfig(
        agent_id=_get("agent_id"),
        shared_secret=_get("shared_secret"),
        endpoint=_get("endpoint", "http://localhost:8002/v1/ingest"),
        spool_path=Path(_get("spool_path", _default_spool_path())),
        spool_max_mb=int(_get("spool_max_mb", 64)),
        retry_max_seconds=int(_get("retry_max_seconds", 60)),
        max_in_flight=int(_get("max_in_flight", 200)),
        batch_size=int(_get("batch_size", 200)),
        flush_interval_ms=int(_get("flush_interval_ms", 2000)),
        queue_max_size=int(_get("queue_max_size", 1000)),
        spool_drop_policy=_get("spool_drop_policy", "drop_oldest"),
        state_path=state_path_value,
        sources=sources,
        allow_raw=str(_get("allow_raw", "false")).lower() in {"1", "true", "yes"},
        windows_eventlog=windows_eventlog,
    )
