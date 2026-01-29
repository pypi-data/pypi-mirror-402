from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentState:
    path: Path
    checkpoints: dict[str, dict] = field(default_factory=dict)
    stats: dict[str, dict] = field(default_factory=dict)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "checkpoints": self.checkpoints,
                    "stats": self.stats,
                },
                handle,
            )

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        if not path.exists():
            return cls(path=path)
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(
            path=path,
            checkpoints=data.get("checkpoints", {}),
            stats=data.get("stats", {}),
        )

    def update_checkpoint(self, channel: str, record_number: int, timestamp: str) -> None:
        self.checkpoints[channel] = {
            "record_number": record_number,
            "timestamp": timestamp,
        }

    def get_checkpoint(self, channel: str) -> dict | None:
        return self.checkpoints.get(channel)

    def update_stats(self, key: str, value: dict) -> None:
        self.stats[key] = value
