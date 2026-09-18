"""Persona and memory on disk. Aurora lives in these files, not in a cloud API."""

from __future__ import annotations

import re
from pathlib import Path

from aurora.paths import dossier_file, notes_file, persona_file


_FACT = re.compile(r"^-\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)\s*$")
_SECTION = re.compile(r"^##\s+(.+?)\s*$")


def _parse_facts(text: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in text.splitlines():
        m = _FACT.match(line.strip())
        if m:
            facts[m.group(1).strip()] = m.group(2).strip()
    return facts


def _parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = _SECTION.match(line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


class Persona:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.raw = path.read_text(encoding="utf-8") if path.is_file() else ""
        self.facts = _parse_facts(self.raw)
        self.sections = _parse_sections(self.raw)
        self.name = self.facts.get("name", "Аврора")

    def section(self, name: str, default: str = "") -> str:
        return self.sections.get(name.lower(), default)

    def greeting_template(self) -> str:
        return self.section(
            "greeting",
            "Привет, {name}. Я {me}. Я здесь, на твоём диске.",
        )

    def fallback_template(self) -> str:
        return self.section(
            "fallback",
            "Я рядом. Скажи это чуть иначе — или попроси запомнить что-нибудь о тебе.",
        )

    def identity_template(self) -> str:
        return self.section(
            "identity",
            "Я {me}. Я живу у тебя на компьютере и думаю на языке LC.",
        )


class Memory:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.path = dossier_file(home)
        self.notes_path = notes_file(home)
        self.reload()

    def reload(self) -> None:
        self.raw = self.path.read_text(encoding="utf-8") if self.path.is_file() else ""
        self.facts = _parse_facts(self.raw)
        if "name" not in self.facts:
            self.facts["name"] = "Артём"

    def get(self, key: str, default: str = "") -> str:
        return self.facts.get(key, default)

    def sheet(self) -> str:
        if not self.facts:
            return "Пока почти пусто — только то, что ты сам напишешь на диск."
        lines = ["Вот что лежит у меня в memory/me.md:"]
        for key, value in self.facts.items():
            lines.append(f"— {key}: {value}")
        extra = ""
        if self.notes_path.is_file():
            extra = self.notes_path.read_text(encoding="utf-8").strip()
        if extra:
            lines.append("")
            lines.append("Заметки (memory/notes.md):")
            lines.append(extra)
        return "\n".join(lines)

    def set_fact(self, key: str, value: str) -> None:
        key = key.strip()
        value = value.strip()
        self.facts[key] = value
        if not self.path.is_file():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(f"# Досье\n\n- {key}: {value}\n", encoding="utf-8")
            self.reload()
            return
        text = self.path.read_text(encoding="utf-8")
        pattern = re.compile(rf"^-\s*{re.escape(key)}\s*:.*$", re.MULTILINE)
        replacement = f"- {key}: {value}"
        if pattern.search(text):
            text = pattern.sub(replacement, text, count=1)
        else:
            if not text.endswith("\n"):
                text += "\n"
            text += f"- {key}: {value}\n"
        self.path.write_text(text, encoding="utf-8")
        self.reload()

    def add_note(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self.notes_path.parent.mkdir(parents=True, exist_ok=True)
        prev = ""
        if self.notes_path.is_file():
            prev = self.notes_path.read_text(encoding="utf-8")
            if prev and not prev.endswith("\n"):
                prev += "\n"
        self.notes_path.write_text(prev + f"- {text}\n", encoding="utf-8")


def load_persona(home: Path) -> Persona:
    return Persona(persona_file(home))


def load_memory(home: Path) -> Memory:
    return Memory(home)
