"""Aurora LC parser.

Statement shape (dream syntax):

    (LC. 31. print(null));

A statement is a parenthesized `LC` header, a statement id, then a call chain
ending with `);`. Calls may be chained with `.`:

    (LC. 20. if_contains("привет", "hello").reply("Привет, {name}."));
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class LCParseError(Exception):
    """User-facing parse failure for a .avr / LC fragment."""

    def __init__(self, message: str, line: int = 0, column: int = 0, source: str = "<lc>") -> None:
        self.message = message
        self.line = line
        self.column = column
        self.source = source
        loc = f"{source}:{line}:{column}" if line else source
        super().__init__(f"{loc}: {message}")


@dataclass(frozen=True)
class Arg:
    kind: str  # "null" | "string" | "number" | "ident"
    value: Any

    @property
    def is_null(self) -> bool:
        return self.kind == "null"

    def as_text(self) -> str:
        if self.is_null:
            return ""
        return str(self.value)


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple[Arg, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Statement:
    sid: str
    calls: tuple[Call, ...]
    source: str = "<lc>"
    line: int = 1

    @property
    def sort_key(self) -> tuple:
        parts: list[tuple[int, str]] = []
        for chunk in self.sid.split("."):
            if chunk.isdigit():
                parts.append((0, f"{int(chunk):012d}"))
            else:
                parts.append((1, chunk))
        return (self.source, self.line, tuple(parts), self.sid)


class _Tok:
    __slots__ = ("kind", "value", "line", "column")

    def __init__(self, kind: str, value: str, line: int, column: int) -> None:
        self.kind = kind
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:  # pragma: no cover
        return f"Tok({self.kind!r}, {self.value!r}, {self.line}:{self.column})"


def _tokenize(text: str, source: str) -> list[_Tok]:
    tokens: list[_Tok] = []
    i = 0
    n = len(text)
    line = 1
    col = 1

    def peek(k: int = 0) -> str:
        j = i + k
        return text[j] if j < n else ""

    def bump() -> str:
        nonlocal i, line, col
        ch = text[i]
        i += 1
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1
        return ch

    while i < n:
        ch = peek()
        start_line, start_col = line, col

        if ch in " \t\r\n":
            bump()
            continue

        # comments: // ... or # ...
        if ch == "#" or (ch == "/" and peek(1) == "/"):
            while i < n and peek() != "\n":
                bump()
            continue

        if ch == "(":
            bump()
            tokens.append(_Tok("LPAREN", "(", start_line, start_col))
            continue
        if ch == ")":
            bump()
            tokens.append(_Tok("RPAREN", ")", start_line, start_col))
            continue
        if ch == ".":
            bump()
            tokens.append(_Tok("DOT", ".", start_line, start_col))
            continue
        if ch == ",":
            bump()
            tokens.append(_Tok("COMMA", ",", start_line, start_col))
            continue
        if ch == ";":
            bump()
            tokens.append(_Tok("SEMI", ";", start_line, start_col))
            continue

        if ch in "\"'":
            quote = bump()
            buf: list[str] = []
            closed = False
            while i < n:
                c = bump()
                if c == quote:
                    closed = True
                    break
                if c == "\\":
                    nxt = bump() if i < n else ""
                    escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
                    buf.append(escapes.get(nxt, nxt))
                else:
                    buf.append(c)
            if not closed:
                raise LCParseError("незакрытая строка", start_line, start_col, source)
            tokens.append(_Tok("STRING", "".join(buf), start_line, start_col))
            continue

        if ch.isdigit() or (ch == "-" and peek(1).isdigit()):
            buf = [bump()]
            while peek().isdigit() or peek() == ".":
                # keep dotted numbers only if next after dot is a digit AND we are
                # not at a call-chain boundary. LC ids are tokenized separately as IDENT.
                if peek() == "." and not peek(1).isdigit():
                    break
                buf.append(bump())
            raw = "".join(buf)
            tokens.append(_Tok("NUMBER", raw, start_line, start_col))
            continue

        if ch.isalpha() or ch == "_" or ("а" <= ch.lower() <= "я") or ch.lower() == "ё":
            buf = [bump()]
            while True:
                c = peek()
                if c.isalnum() or c in "_:" or ("а" <= c.lower() <= "я") or c.lower() == "ё":
                    buf.append(bump())
                else:
                    break
            raw = "".join(buf)
            kind = "NULL" if raw == "null" else "IDENT"
            tokens.append(_Tok(kind, raw, start_line, start_col))
            continue

        raise LCParseError(f"неожиданный символ {ch!r}", start_line, start_col, source)

    tokens.append(_Tok("EOF", "", line, col))
    return tokens


class _Reader:
    def __init__(self, tokens: list[_Tok], source: str) -> None:
        self.tokens = tokens
        self.source = source
        self.i = 0

    def peek(self) -> _Tok:
        return self.tokens[self.i]

    def eat(self, kind: str | None = None) -> _Tok:
        tok = self.peek()
        if kind is not None and tok.kind != kind:
            raise LCParseError(
                f"ожидалось {kind}, получила {tok.kind} ({tok.value!r})",
                tok.line,
                tok.column,
                self.source,
            )
        self.i += 1
        return tok

    def match(self, kind: str) -> bool:
        if self.peek().kind == kind:
            self.i += 1
            return True
        return False


def _parse_arg(r: _Reader) -> Arg:
    tok = r.peek()
    if tok.kind == "NULL":
        r.eat()
        return Arg("null", None)
    if tok.kind == "STRING":
        r.eat()
        return Arg("string", tok.value)
    if tok.kind == "NUMBER":
        r.eat()
        raw = tok.value
        value: Any = float(raw) if "." in raw else int(raw)
        return Arg("number", value)
    if tok.kind == "IDENT":
        r.eat()
        return Arg("ident", tok.value)
    raise LCParseError(
        f"ожидался аргумент, получила {tok.kind} ({tok.value!r})",
        tok.line,
        tok.column,
        r.source,
    )


def _parse_call(r: _Reader) -> Call:
    name_tok = r.eat("IDENT")
    r.eat("LPAREN")
    args: list[Arg] = []
    if r.peek().kind != "RPAREN":
        args.append(_parse_arg(r))
        while r.match("COMMA"):
            args.append(_parse_arg(r))
    r.eat("RPAREN")
    return Call(name_tok.value, tuple(args))


def _parse_id(r: _Reader) -> str:
    """Statement id: 31 | 20.1 | boot | 10.greet"""
    parts: list[str] = []
    tok = r.peek()
    if tok.kind == "NUMBER":
        parts.append(r.eat().value)
    elif tok.kind == "IDENT":
        parts.append(r.eat().value)
    else:
        raise LCParseError("ожидался id выражения LC", tok.line, tok.column, r.source)
    while r.peek().kind == "DOT":
        nxt = r.tokens[r.i + 1] if r.i + 1 < len(r.tokens) else None
        # Lookahead: DOT IDENT LPAREN starts the call chain, not the id.
        if nxt is not None and nxt.kind == "IDENT":
            after = r.tokens[r.i + 2] if r.i + 2 < len(r.tokens) else None
            if after is not None and after.kind == "LPAREN":
                break
        r.eat("DOT")
        part = r.peek()
        if part.kind in {"NUMBER", "IDENT"}:
            parts.append(r.eat().value)
        else:
            raise LCParseError("обрезанный id выражения LC", part.line, part.column, r.source)
    return ".".join(parts)


def _parse_statement(r: _Reader) -> Statement:
    lparen = r.eat("LPAREN")
    kw = r.eat("IDENT")
    if kw.value != "LC":
        raise LCParseError(
            f"выражение должно начинаться с LC, а не {kw.value!r}",
            kw.line,
            kw.column,
            r.source,
        )
    r.eat("DOT")
    sid = _parse_id(r)
    r.eat("DOT")
    calls = [_parse_call(r)]
    while r.match("DOT"):
        calls.append(_parse_call(r))
    r.eat("RPAREN")
    r.eat("SEMI")
    return Statement(sid=sid, calls=tuple(calls), source=r.source, line=lparen.line)


def parse(text: str, source: str = "<lc>") -> list[Statement]:
    """Parse a full .avr file or a fragment into LC statements."""
    if text.startswith("\ufeff"):
        text = text[1:]
    tokens = _tokenize(text, source)
    r = _Reader(tokens, source)
    statements: list[Statement] = []
    while r.peek().kind != "EOF":
        statements.append(_parse_statement(r))
    return statements


def parse_file(path) -> list[Statement]:
    from pathlib import Path

    p = Path(path)
    return parse(p.read_text(encoding="utf-8"), source=str(p))
