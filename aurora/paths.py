"""Locate Aurora's home on disk: persona, memory, brain."""

from __future__ import annotations

from pathlib import Path


def find_home(start: Path | None = None) -> Path:
    """Walk up from start (or this file / cwd) until brain/ and persona/ exist."""
    candidates: list[Path] = []
    if start is not None:
        candidates.append(start.resolve())
    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve().parent.parent)

    seen: set[Path] = set()
    for base in candidates:
        for path in [base, *base.parents]:
            if path in seen:
                continue
            seen.add(path)
            if (path / "brain").is_dir() and (path / "persona").is_dir():
                return path
    raise FileNotFoundError(
        "Не нашла дом Авроры: нужны папки brain/ и persona/. "
        "Запусти из корня репозитория."
    )


def persona_file(home: Path) -> Path:
    return home / "persona" / "persona.md"


def memory_dir(home: Path) -> Path:
    return home / "memory"


def dossier_file(home: Path) -> Path:
    return memory_dir(home) / "me.md"


def notes_file(home: Path) -> Path:
    return memory_dir(home) / "notes.md"


def brain_dir(home: Path) -> Path:
    return home / "brain"
