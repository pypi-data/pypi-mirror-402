from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentState:
    path: Path
    offsets: dict[str, int]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump({"offsets": self.offsets}, handle)

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        if not path.exists():
            return cls(path=path, offsets={})
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(path=path, offsets=data.get("offsets", {}))
