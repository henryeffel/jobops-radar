import json
from pathlib import Path
from typing import Any, Protocol


class JobPostingProvider(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class FixtureProvider:
    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(self) -> list[dict[str, Any]]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else [payload]


class SaraminProvider:
    """Reserved boundary for the approved official API integration."""

    def fetch(self) -> list[dict[str, Any]]:
        raise NotImplementedError("Saramin API approval and integration are pending")
