from __future__ import annotations

import unittest

from aurora.parser import LCParseError, parse


class ParsePrintNullTests(unittest.TestCase):
    def test_canonical_print_null(self) -> None:
        stmts = parse("(LC. 31. print(null));")
        self.assertEqual(len(stmts), 1)
        s = stmts[0]
        self.assertEqual(s.sid, "31")
        self.assertEqual(s.calls[0].name, "print")
        self.assertTrue(s.calls[0].args[0].is_null)
        self.assertIsNone(s.calls[0].args[0].value)

    def test_print_null_whitespace(self) -> None:
        stmts = parse("  ( LC.  31.  print( null ) )  ;  ")
        self.assertEqual(stmts[0].sid, "31")
        self.assertTrue(stmts[0].calls[0].args[0].is_null)


class ParseShapeTests(unittest.TestCase):
    def test_chain_if_contains_reply(self) -> None:
        src = '(LC. 20. if_contains("привет", "hello").reply("Привет, {name}."));'
        s = parse(src)[0]
        self.assertEqual(s.sid, "20")
        self.assertEqual(s.calls[0].name, "if_contains")
        self.assertEqual(
            [a.value for a in s.calls[0].args],
            ["привет", "hello"],
        )
        self.assertEqual(s.calls[1].name, "reply")
        self.assertEqual(s.calls[1].args[0].value, "Привет, {name}.")

    def test_match_alias_and_empty_call(self) -> None:
        s = parse("(LC. 7. match('hi').greet());")[0]
        self.assertEqual(s.calls[0].name, "match")
        self.assertEqual(s.calls[0].args[0].value, "hi")
        self.assertEqual(s.calls[1].name, "greet")
        self.assertEqual(s.calls[1].args, ())

    def test_dotted_id(self) -> None:
        s = parse('(LC. 20.1. reply("x"));')[0]
        self.assertEqual(s.sid, "20.1")

    def test_ident_id(self) -> None:
        s = parse("(LC. boot. load_persona());")[0]
        self.assertEqual(s.sid, "boot")
        self.assertEqual(s.calls[0].name, "load_persona")

    def test_number_and_ident_args(self) -> None:
        s = parse("(LC. 1. remember(city, 42));")[0]
        self.assertEqual(s.calls[0].args[0].kind, "ident")
        self.assertEqual(s.calls[0].args[0].value, "city")
        self.assertEqual(s.calls[0].args[1].kind, "number")
        self.assertEqual(s.calls[0].args[1].value, 42)

    def test_string_escapes_and_nested_parens(self) -> None:
        s = parse(r'(LC. 1. reply("a\n\"(ok)\""));')[0]
        self.assertEqual(s.calls[0].args[0].value, 'a\n"(ok)"')

    def test_multiple_statements_and_comments(self) -> None:
        src = """
        // night thought
        (LC. 10. load_persona());
        # still a comment
        (LC. 11. load_memory());
        (LC. 12. print(null));
        """
        stmts = parse(src)
        self.assertEqual([s.sid for s in stmts], ["10", "11", "12"])
        self.assertEqual(stmts[0].line, 3)

    def test_semicolon_inside_string(self) -> None:
        s = parse('(LC. 1. reply("ok); still"));')[0]
        self.assertEqual(s.calls[0].args[0].value, "ok); still")

    def test_bom(self) -> None:
        stmts = parse("\ufeff(LC. 1. greet());")
        self.assertEqual(stmts[0].calls[0].name, "greet")


class ParseErrorTests(unittest.TestCase):
    def test_missing_semicolon(self) -> None:
        with self.assertRaises(LCParseError) as ctx:
            parse("(LC. 1. greet())")
        self.assertIn("SEMI", str(ctx.exception))

    def test_not_lc(self) -> None:
        with self.assertRaises(LCParseError):
            parse("(XX. 1. greet());")

    def test_unclosed_string(self) -> None:
        with self.assertRaises(LCParseError) as ctx:
            parse('(LC. 1. reply("oops));')
        self.assertIn("незакрытая", str(ctx.exception))

    def test_unexpected_char(self) -> None:
        with self.assertRaises(LCParseError):
            parse("(LC. 1. reply($));")

    def test_empty_file(self) -> None:
        self.assertEqual(parse(""), [])
        self.assertEqual(parse("  \n// only comments\n"), [])


if __name__ == "__main__":
    unittest.main()
