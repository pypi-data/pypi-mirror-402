from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/logsentry/agent.yml")


@dataclass
class AgentConfig:
    agent_id: str
    shared_secret: str
    endpoint: str
    spool_path: Path
    spool_max_mb: int
    retry_max_seconds: int
    max_in_flight: int
    sources: list[str] = field(default_factory=list)
    allow_raw: bool = False


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

    return AgentConfig(
        agent_id=_get("agent_id"),
        shared_secret=_get("shared_secret"),
        endpoint=_get("endpoint", "http://localhost:8002/v1/ingest"),
        spool_path=Path(_get("spool_path", "/var/lib/logsentry/spool.db")),
        spool_max_mb=int(_get("spool_max_mb", 64)),
        retry_max_seconds=int(_get("retry_max_seconds", 60)),
        max_in_flight=int(_get("max_in_flight", 200)),
        sources=sources,
        allow_raw=str(_get("allow_raw", "false")).lower() in {"1", "true", "yes"},
    )
