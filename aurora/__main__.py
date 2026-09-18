"""python -m aurora — offline desktop companion."""

from __future__ import annotations

import argparse
import sys

from aurora.engine import Aurora
from aurora.paths import find_home


def _utf8_stdio() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _cli(aurora: Aurora) -> None:
    print("Аврора · офлайн · LC. Пустая строка — выход.")
    while True:
        try:
            line = input("ты: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            return
        print("Аврора:", aurora.reply(line))
        print()


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="aurora",
        description="Аврора — личный офлайн-спутник. Без облачных LLM.",
    )
    parser.add_argument("--once", metavar="TEXT", help="один ответ в stdout, без окна")
    parser.add_argument("--cli", action="store_true", help="чат в терминале, без окна")
    parser.add_argument("--home", help="корень с папками brain/, persona/, memory/")
    args = parser.parse_args(argv)

    try:
        home = find_home() if not args.home else args.home
        aurora = Aurora(home)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.once is not None:
        print(aurora.reply(args.once))
        return 0
    if args.cli:
        _cli(aurora)
        return 0

    from aurora.ui import run_app

    run_app(aurora)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
