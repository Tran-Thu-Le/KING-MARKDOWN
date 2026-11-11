import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from king_markdown.values import (ValueError_, format_value, parse_value,  # noqa: E402
                                  split_top, strip_comment, type_of)


class ValuesTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_value("3"), 3)
        self.assertEqual(parse_value("-0.5"), -0.5)
        self.assertIs(parse_value("true"), True)
        self.assertIsNone(parse_value("none"))
        self.assertEqual(parse_value("chữ tự do"), "chữ tự do")
        self.assertEqual(parse_value('"a, b"'), "a, b")
        self.assertEqual(parse_value('"3"'), "3")

    def test_list_dict(self):
        self.assertEqual(parse_value("(a, b)"), ["a", "b"])
        self.assertEqual(parse_value("(x)"), ["x"])
        self.assertEqual(parse_value("()"), [])
        self.assertEqual(parse_value("(a=1, b=(x, y))"), {"a": 1, "b": ["x", "y"]})
        self.assertEqual(parse_value('(t="1, 2", n=none)'), {"t": "1, 2", "n": None})
        self.assertEqual(type_of(parse_value("(w=3)")), "Dict")

    def test_content_code(self):
        self.assertEqual(parse_value("[có $x^2$, (a)]"), {"content": "có $x^2$, (a)"})
        self.assertEqual(parse_value("[\n  dòng 1\n    dòng 2\n]"), {"content": "dòng 1\n  dòng 2"})
        self.assertEqual(parse_value("`f'(x) // a`"), {"code": "f'(x) // a"})
        self.assertEqual(type_of(parse_value("[a]")), "Content")

    def test_errors(self):
        for bad in ("(a, b", "[abc", '"abc', "(a=1, b)", "(a=1, a=2)", "(a,,b)"):
            with self.assertRaises(ValueError_, msg=bad):
                parse_value(bad)

    def test_round_trip(self):
        for v in (3, 0.5, True, None, "chữ", "a, b", "3", ["a", "b"], ["x"], {"a": 1, "b": ["x", "y"]},
                  {"content": "nội dung"}, {"code": "x // y"}, "true"):
            self.assertEqual(parse_value(format_value(v)), v, v)

    def test_comment(self):
        self.assertEqual(strip_comment("- web: https://x.org // ghi chú"), "- web: https://x.org")
        self.assertEqual(strip_comment('- a: "x // y"'), '- a: "x // y"')
        self.assertEqual(strip_comment("- a: `x // y` // c"), "- a: `x // y`")
        self.assertEqual(strip_comment("// cả dòng"), "")

    def test_split_top(self):
        self.assertEqual(split_top('a, (b, c), "d, e", [f, g]'), ["a", "(b, c)", '"d, e"', "[f, g]"])


if __name__ == "__main__":
    unittest.main()
