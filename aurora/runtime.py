"""Execute Aurora LC statements against persona + memory. No network, no LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from aurora.parser import Arg, Call, Statement, parse_file
from aurora.paths import brain_dir
from aurora.store import Memory, Persona, load_memory, load_persona


NAME_RE = re.compile(
    r"(?:меня\s+зовут|зови\s+меня|мо[её]\s+имя)\s+([A-Za-zА-Яа-яЁё-]+)",
    re.IGNORECASE,
)
NOTE_RE = re.compile(r"запомни(?:\s+что)?\s*[:\-]?\s*(.+)$", re.IGNORECASE | re.DOTALL)


class LCRuntimeError(Exception):
    pass


@dataclass
class Turn:
    user: str
    vars: dict[str, str] = field(default_factory=dict)
    reply_text: str = ""
    stopped: bool = False
    answered: bool = False
    remembered: bool = False
    trace: list[str] = field(default_factory=list)

    def set_reply(self, text: str, *, overwrite: bool = False) -> None:
        text = text.strip()
        if not text:
            return
        if self.answered and not overwrite:
            return
        self.reply_text = text
        self.answered = True


class Runtime:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.persona: Persona = load_persona(home)
        self.memory: Memory = load_memory(home)
        self.statements: list[Statement] = self._load_brain()

    def _load_brain(self) -> list[Statement]:
        folder = brain_dir(self.home)
        files = sorted(folder.glob("*.avr"))
        statements: list[Statement] = []
        for path in files:
            statements.extend(parse_file(path))
        statements.sort(key=lambda s: s.sort_key)
        return statements

    def reload(self) -> None:
        self.persona = load_persona(self.home)
        self.memory = load_memory(self.home)
        self.statements = self._load_brain()

    def reply(self, user_text: str) -> str:
        turn = Turn(user=user_text.strip())
        self._hydrate_vars(turn)
        for stmt in self.statements:
            if turn.stopped:
                break
            self._run_statement(stmt, turn)
        if not turn.answered:
            turn.set_reply(self._render(self.persona.fallback_template(), turn))
        return turn.reply_text.strip()

    def _hydrate_vars(self, turn: Turn) -> None:
        turn.vars["me"] = self.persona.name
        turn.vars["persona"] = self.persona.name
        turn.vars["user_message"] = turn.user
        for key, value in self.persona.facts.items():
            turn.vars.setdefault(key, value)
        for key, value in self.memory.facts.items():
            turn.vars[key] = value
        if "name" not in turn.vars:
            turn.vars["name"] = "Артём"
        turn.vars["memory_sheet"] = self.memory.sheet()
        turn.vars["remember_ack"] = "Записала."

    def _render(self, template: str, turn: Turn) -> str:
        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return turn.vars.get(key, match.group(0))

        return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, template)

    def _arg_text(self, arg: Arg, turn: Turn) -> str:
        return self._render(arg.as_text(), turn)

    def _run_statement(self, stmt: Statement, turn: Turn) -> None:
        skip_rest = False
        for call in stmt.calls:
            if skip_rest or turn.stopped:
                return
            skip_rest = not self._run_call(call, turn, stmt)

    def _run_call(self, call: Call, turn: Turn, stmt: Statement) -> bool:
        """Return False to skip the rest of the chain."""
        name = call.name.lower()
        handler = self.COMMANDS.get(name)
        if handler is None:
            raise LCRuntimeError(
                f"{stmt.source}:{stmt.line}: неизвестная команда LC `{call.name}`"
            )
        return handler(self, call, turn)

    def _cmd_print(self, call: Call, turn: Turn) -> bool:
        # print(null) is the empty utterance — a pause, not speech.
        if not call.args or call.args[0].is_null:
            turn.trace.append("print(null)")
            return True
        turn.trace.append(f"print({call.args[0].as_text()!r})")
        return True

    def _cmd_reply(self, call: Call, turn: Turn) -> bool:
        parts = [self._arg_text(a, turn) for a in call.args if not a.is_null]
        text = " ".join(parts).strip()
        turn.set_reply(text)
        return True

    def _cmd_greet(self, call: Call, turn: Turn) -> bool:
        if call.args:
            template = self._arg_text(call.args[0], turn)
        else:
            template = self.persona.greeting_template()
        turn.set_reply(self._render(template, turn))
        return True

    def _cmd_recall(self, call: Call, turn: Turn) -> bool:
        self.memory.reload()
        self._hydrate_vars(turn)
        if not call.args:
            turn.vars["memory_sheet"] = self.memory.sheet()
            return True
        key = self._arg_text(call.args[0], turn).strip()
        value = self.memory.get(key, "")
        turn.vars[key] = value
        if value:
            turn.vars["recalled"] = value
        return True

    def _cmd_remember(self, call: Call, turn: Turn) -> bool:
        if len(call.args) < 2:
            return True
        key = self._arg_text(call.args[0], turn).strip()
        value = self._arg_text(call.args[1], turn).strip()
        if key and value:
            self.memory.set_fact(key, value)
            turn.vars[key] = value
            turn.remembered = True
            turn.vars["remember_ack"] = f"Записала {key}: {value}."
        return True

    def _cmd_if_contains(self, call: Call, turn: Turn) -> bool:
        hay = turn.user.casefold()
        needles = [self._arg_text(a, turn).casefold() for a in call.args if not a.is_null]
        needles = [n for n in needles if n]
        if not needles:
            return False
        return any(n in hay for n in needles)

    def _cmd_load_persona(self, call: Call, turn: Turn) -> bool:
        self.persona = load_persona(self.home)
        self._hydrate_vars(turn)
        turn.trace.append("load_persona")
        return True

    def _cmd_load_memory(self, call: Call, turn: Turn) -> bool:
        self.memory.reload()
        self._hydrate_vars(turn)
        turn.trace.append("load_memory")
        return True

    def _cmd_fallback(self, call: Call, turn: Turn) -> bool:
        return not turn.answered

    def _cmd_stop(self, call: Call, turn: Turn) -> bool:
        turn.stopped = True
        return True

    def _cmd_note(self, call: Call, turn: Turn) -> bool:
        text = " ".join(self._arg_text(a, turn) for a in call.args if not a.is_null).strip()
        if text:
            self.memory.add_note(text)
            turn.remembered = True
        return True

    def _cmd_remember_from_message(self, call: Call, turn: Turn) -> bool:
        user = turn.user.strip()
        name_match = NAME_RE.search(user)
        if name_match:
            name = name_match.group(1).strip(" .,!?")
            if name:
                self.memory.set_fact("name", name)
                turn.vars["name"] = name
                turn.remembered = True
                turn.vars["remember_ack"] = f"Хорошо. Буду звать тебя {name}."
                return True
        note_match = NOTE_RE.search(user)
        payload = ""
        if note_match:
            payload = note_match.group(1).strip(" .,!?")
        if payload:
            kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[=:]\s*(.+)$", payload)
            if kv:
                key, value = kv.group(1), kv.group(2).strip()
                self.memory.set_fact(key, value)
                turn.vars[key] = value
                turn.remembered = True
                turn.vars["remember_ack"] = f"Записала {key}: {value}."
            else:
                self.memory.add_note(payload)
                turn.remembered = True
                turn.vars["remember_ack"] = "Записала это к себе на диск. Не в облако — сюда."
        else:
            turn.vars["remember_ack"] = "Скажи, что запомнить: «запомни …» или «меня зовут …»."
        return True

    def _cmd_identity(self, call: Call, turn: Turn) -> bool:
        turn.set_reply(self._render(self.persona.identity_template(), turn))
        return True

    COMMANDS = {
        "print": _cmd_print,
        "reply": _cmd_reply,
        "greet": _cmd_greet,
        "recall": _cmd_recall,
        "remember": _cmd_remember,
        "if_contains": _cmd_if_contains,
        "match": _cmd_if_contains,
        "load_persona": _cmd_load_persona,
        "load_memory": _cmd_load_memory,
        "fallback": _cmd_fallback,
        "stop": _cmd_stop,
        "note": _cmd_note,
        "remember_from_message": _cmd_remember_from_message,
        "identity": _cmd_identity,
    }


def load_runtime(home: Path) -> Runtime:
    return Runtime(home)
