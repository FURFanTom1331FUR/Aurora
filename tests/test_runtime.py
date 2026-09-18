from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from aurora.engine import Aurora
from aurora.parser import parse_file
from aurora.runtime import Runtime


REPO = Path(__file__).resolve().parent.parent


def _copy_home() -> Path:
    dest = Path(tempfile.mkdtemp(prefix="aurora-"))
    for name in ("brain", "persona", "memory"):
        shutil.copytree(REPO / name, dest / name)
    return dest


class BrainFilesParseTests(unittest.TestCase):
    def test_all_avr_parse(self) -> None:
        files = sorted((REPO / "brain").glob("*.avr"))
        self.assertGreaterEqual(len(files), 4)
        total = 0
        for path in files:
            stmts = parse_file(path)
            self.assertTrue(stmts, msg=f"empty brain: {path}")
            total += len(stmts)
        self.assertGreaterEqual(total, 8)


class ChatFromDiskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = _copy_home()
        self.aurora = Aurora(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_greet_uses_dossier_name(self) -> None:
        text = self.aurora.reply("привет")
        self.assertIn("Артём", text)
        self.assertIn("Аврора", text)

    def test_identity_not_cloud(self) -> None:
        text = self.aurora.reply("кто ты")
        self.assertIn("Аврора", text)
        lower = text.lower()
        self.assertTrue("диске" in text or "LC" in text or "диске" in lower)

    def test_rejects_llama_and_openai(self) -> None:
        text = self.aurora.reply("ты же chatgpt на llama?")
        self.assertIn("Аврора", text)
        self.assertNotIn("конечно, я ChatGPT", text)

    def test_recall_name(self) -> None:
        text = self.aurora.reply("как меня зовут")
        self.assertIn("Артём", text)

    def test_remember_name(self) -> None:
        ack = self.aurora.reply("меня зовут Мира")
        self.assertIn("Мира", ack)
        again = self.aurora.reply("как меня зовут")
        self.assertIn("Мира", again)
        dossier = (self.home / "memory" / "me.md").read_text(encoding="utf-8")
        self.assertIn("Мира", dossier)

    def test_note_from_message(self) -> None:
        ack = self.aurora.reply("запомни: люблю тишину")
        self.assertIn("диск", ack.lower() + ack)
        notes = (self.home / "memory" / "notes.md").read_text(encoding="utf-8")
        self.assertIn("люблю тишину", notes)

    def test_fallback(self) -> None:
        text = self.aurora.reply("кхм-кхм зелёные квадраты 999")
        self.assertTrue(text)
        self.assertIn("диске", text)

    def test_lc_question(self) -> None:
        text = self.aurora.reply("что такое LC")
        self.assertIn("print(null)", text)

    def test_unknown_command_raises(self) -> None:
        rt = Runtime(self.home)
        from aurora.parser import parse

        rt.statements = parse("(LC. 1. explode());")
        with self.assertRaises(Exception):
            rt.reply("hi")


if __name__ == "__main__":
    unittest.main()
