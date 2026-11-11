import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from king_markdown.legacy import Parser, parse_meta, read, slug  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")


def build(name):
    path = os.path.join(FIX, name)
    return Parser(read(path), path).build()


def msgs(g, kind="errors"):
    return " | ".join(e["msg"] for e in g["graph"][kind])


class TestValid(unittest.TestCase):
    def setUp(self):
        self.g = build("ok.kg.md")

    def test_no_errors(self):
        self.assertEqual(self.g["graph"]["errors"], [])
        self.assertEqual(self.g["graph"]["warnings"], [])

    def test_nodes(self):
        ids = {n["id"]: n for n in self.g["nodes"]}
        self.assertEqual(set(ids), {"toan", "giai-tich", "dao-ham", "tich-phan"})
        self.assertEqual(ids["toan"]["kind"], "section")
        self.assertEqual(ids["dao-ham"]["parent"], "toan")
        self.assertEqual(ids["dao-ham"]["title"], "Đạo hàm")

    def test_links(self):
        got = {(l["source"], l["type"], l["target"]) for l in self.g["links"]}
        self.assertIn(("dao-ham", "part-of", "giai-tich"), got)
        self.assertIn(("tich-phan", "needs", "dao-ham"), got)
        self.assertIn(("tich-phan", "export", "toan"), got)       # loại() → section chứa
        self.assertIn(("dao-ham", "mention", "tich-phan"), got)   # @id trong content
        self.assertIn(("toan", "contains", "dao-ham"), got)       # cây chứa

    def test_line_numbers(self):
        n = next(n for n in self.g["nodes"] if n["id"] == "dao-ham")
        self.assertEqual(n["line"], 9)


class TestErrors(unittest.TestCase):
    def test_duplicate_id(self):
        self.assertIn("ID trùng: a", msgs(build("dup-id.kg.md")))

    def test_unknown_field(self):
        self.assertIn("trường lạ: contain", msgs(build("bad-field.kg.md")))

    def test_missing_target_and_module(self):
        m = msgs(build("missing-target.kg.md"))
        self.assertIn("không tìm thấy node: khong-co", m)
        self.assertIn("module chưa import: math", m)

    def test_cycle(self):
        self.assertIn("vòng lặp needs", msgs(build("cycle.kg.md")))

    def test_schema(self):
        m = msgs(build("schema-error.kg.md"))
        self.assertIn("role=Sai không thuộc", m)
        self.assertIn("thiếu khóa bắt buộc role", m)
        self.assertIn("loại link không khai báo trong schema: lien-quan", m)

    def test_v01_frontmatter_warns(self):
        g = build("v01-frontmatter.kg.md")
        self.assertIn("không còn dùng (v0.2)", msgs(g, "warnings"))


class TestContain(unittest.TestCase):
    def test_edges_across_sections(self):
        g = build("contain.kg.md")
        self.assertEqual(g["graph"]["errors"], [])          # contain không cần khai báo trong schema
        got = {(l["source"], l["type"], l["target"]) for l in g["links"]}
        self.assertIn(("giai-tich", "contain", "dao-ham"), got)
        self.assertIn(("giai-tich", "contain", "tich-phan"), got)
        self.assertIn("contain", g["graph"]["dag"])

    def test_errors(self):
        m = msgs(build("contain-error.kg.md"))
        self.assertIn("không tìm thấy node: khong-co", m)
        self.assertIn("loại link contain do parser tự sinh", m)
        self.assertIn("vòng lặp contain", m)
        self.assertIn("contain cần danh sách ID", m)

    def test_field_hint(self):
        self.assertIn("là khóa meta: - meta: contain=b", msgs(build("bad-field.kg.md")))


class TestStyle(unittest.TestCase):
    def test_example_style(self):
        from king_markdown.parser import Parser as Parser03       # ví dụ đã sang 0.3; style vẫn v0.2
        path = os.path.join(ROOT, "examples", "python-course", "vidu.kg.md")
        g = Parser03(read(path), path).build()
        n = {n["id"]: n for n in g["nodes"]}
        self.assertEqual(n["tich-phan"]["style"]["html"]["shape"], "circle")       # #id thắng
        self.assertEqual(n["dao-ham"]["style"]["typst"]["frame"], "khung-nap")     # role=Nạp


class TestMentionInCode(unittest.TestCase):
    def test_at_in_code_is_not_a_mention(self):
        text = ("---\nkg: 0.2\n---\n\n@a: A\n- content: Ví dụ `@khong-co` và\n"
                "```markdown\n@cung-khong-co: X\n- link: needs(b)\n```\n  còn @b là tham chiếu thật.\n\n@b: B\n")
        g = Parser(text, "x.kg.md").build()
        self.assertEqual(g["graph"]["errors"], [])
        got = {(l["source"], l["type"], l["target"]) for l in g["links"] if not l.get("tree")}
        self.assertEqual(got, {("a", "mention", "b")})


class TestBracketContent(unittest.TestCase):
    TEXT = ("---\nkg: 0.2\n---\n\n@a: A\n- content: [Dòng đầu\n- đây: không phải trường\n@b: tham chiếu, không phải node mới\n\n"
            "# không phải heading\ncuối]\n- link: needs(b)\n\n@b: B\n- content: [một dòng]\n- ask: [xem [KING](url)\n")

    def test_long_content_is_literal(self):
        g = Parser(self.TEXT, "x.kg.md").build()
        self.assertEqual(g["graph"]["errors"], [])
        n = {x["id"]: x for x in g["nodes"]}
        self.assertEqual(set(n), {"a", "b"})
        self.assertEqual(n["a"]["content"], "Dòng đầu\n- đây: không phải trường\n@b: tham chiếu, không phải node mới\n\n# không phải heading\ncuối")
        self.assertEqual(n["b"]["content"], "một dòng")
        got = {(l["source"], l["type"], l["target"]) for l in g["links"] if not l.get("tree")}
        self.assertIn(("a", "needs", "b"), got)

    def test_markdown_link_is_not_bracket(self):
        g = Parser("@b: B\n- content: [KING](https://x.org) là ngôn ngữ\n- link: needs(c)\n\n@c: C\n", "x.kg.md").build()
        self.assertEqual(g["graph"]["errors"], [])
        n = {x["id"]: x for x in g["nodes"]}
        self.assertEqual(n["b"]["content"], "[KING](https://x.org) là ngôn ngữ")

    def test_ops_respect_brackets(self):
        from king_markdown.ops import OPS, Doc
        out, _ = OPS["set_meta"](Doc(self.TEXT, "x.kg.md"), id="a", meta={"type": "t"})
        self.assertIn("@a: A\n- meta: type=t\n- content: [Dòng đầu", out)
        out, _ = OPS["add_link"](Doc(out, "x.kg.md"), source="a", target="b", type="see")
        self.assertIn("cuối]\n- link: needs(b), see(b)", out)


class TestHelpers(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slug("Đạo hàm cấp 2"), "dao-ham-cap-2")

    def test_parse_meta(self):
        self.assertEqual(parse_meta('type=concept, important=true, n=3, allow="a, b"'),
                         {"type": "concept", "important": True, "n": 3, "allow": "a, b"})


if __name__ == "__main__":
    unittest.main()
