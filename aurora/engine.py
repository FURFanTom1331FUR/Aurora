"""Aurora engine: one object that answers from LC + persona + memory."""

from __future__ import annotations

from pathlib import Path

from aurora.paths import find_home
from aurora.runtime import Runtime, load_runtime


class Aurora:
    def __init__(self, home: Path | None = None) -> None:
        self.home = find_home(home) if home is None else Path(home)
        self.runtime: Runtime = load_runtime(self.home)

    def reply(self, message: str) -> str:
        return self.runtime.reply(message)

    def reload(self) -> None:
        self.runtime.reload()
