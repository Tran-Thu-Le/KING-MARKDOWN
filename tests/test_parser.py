"""Parser KING Markdown 0.3."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from king_markdown.parser import Parser, read  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures03")


def parse(text, name="t.kg.md"):
    return Parser(text, os.path.join(FIX, name)).build()


def fx(name):
    path = os.path.join(FIX, name)
    return Parser(read(path), path).build()


def nodes(g):
    return {n["id"]: n for n in g["nodes"]}


def edges(g, typ=None):
    return {(l["source"], l["type"], l["target"]) for l in g["links"]
            if not l.get("tree") and (typ is None or l["type"] == typ)}


def msgs(g, kind="errors"):
    return " | ".join(e["msg"] for e in g["graph"][kind])


HEAD = "---\nkg: 0.3\nuse:\n- king/schema.node: Concept, Group\n- king/schema.link: needs, part-of\n---\n"


class ExamplesTest(unittest.TestCase):
    def test_hinh_tron(self):
        g = fx("hinh-tron.kg.md")
        self.assertEqual(g["graph"]["errors"], [])
        N = nodes(g)
        self.assertEqual(N["duong-tron"]["type"], "Concept")
        self.assertEqual(N["duong-tron"]["title"], "Đường tròn")
        self.assertEqual(N["duong-tron"]["attrs"], {"role": "Nạp"})
        self.assertTrue(N["duong-tron"]["content"].startswith("Tập hợp"))
        self.assertEqual(N["hinh-tron"]["kind"], "node")             # tên section tự sinh nhường tên node
        self.assertEqual(N["hinh-tron-2"]["kind"], "section")
        self.assertIn(("hinh-tron", "needs", "duong-tron"), edges(g))
        self.assertIn(("hinh-tron", "mention", "duong-tron"), edges(g))
        self.assertEqual(N["hinh-hoc-phang"]["style"]["html"]["radius"], 10)   # king/style: type=Group

    def test_truyen_kieu_inverse_merge(self):
        g = fx("truyen-kieu.kg.md")
        self.assertEqual(g["graph"]["errors"], [])
        author = [l for l in g["links"] if l["type"] == "author"]
        self.assertEqual(len(author), 1)                               # author + works → một cạnh
        self.assertEqual((author[0]["source"], author[0]["target"]), ("truyen-kieu", "nguyen-du"))
        self.assertEqual(author[0]["lines"], [16, 22])
        self.assertEqual(edges(g, "wrote"), {("nguyen-du", "wrote", "thi-sinh"),
                                             ("ho-xuan-huong", "wrote", "thi-sinh")})
        self.assertEqual(nodes(g)["van-hoc"]["content"], "Các tác phẩm và tác giả.")   # văn bản dưới heading
        self.assertEqual(g["graph"]["schema"]["links"]["author"]["inverse"], "works")


class BlockTest(unittest.TestCase):
    def test_attrs_and_body(self):
        g = parse(HEAD + "@node a\n- label: A\n- n: 3\n\n- ý một\n- ý hai: không phải thuộc tính\n\nĐoạn 2.\n")
        a = nodes(g)["a"]
        self.assertEqual(a["attrs"], {"n": 3})
        self.assertEqual(a["content"], "- ý một\n- ý hai: không phải thuộc tính\n\nĐoạn 2.")

    def test_block_ends(self):
        g = parse(HEAD + "@node a\n- label: A\n@node b\n# S\n@node c\n")
        N = nodes(g)
        self.assertEqual(N["a"]["content"] if "content" in N["a"] else "", "")
        self.assertEqual(N["c"]["parent"], "s")
        self.assertIsNone(N["a"]["parent"])

    def test_fence_and_indent(self):
        g = parse(HEAD + "@node a\n\n```\n@node khong-phai\n# không phải heading\n```\n  @node cung-khong\n")
        self.assertEqual(set(nodes(g)), {"a"})
        self.assertIn("@node khong-phai", nodes(g)["a"]["content"])

    def test_multiline_value(self):
        g = parse(HEAD + "@node a\n- de: [\n  Cho $f(x)$.\n  Tính $f'(1)$.\n  ]\n- tags: (x,\n  y)\n")
        a = nodes(g)["a"]
        self.assertEqual(a["attrs"]["de"], {"content": "Cho $f(x)$.\nTính $f'(1)$."})
        self.assertEqual(a["attrs"]["tags"], ["x", "y"])

    def test_section_attrs(self):
        g = parse(HEAD + "# Chương 1 @c1\n- level: 1\n\nMở đầu.\n\n## Mục\n- Ý danh sách ngay dưới heading\n")
        N = nodes(g)
        self.assertEqual(N["c1"]["attrs"], {"level": 1})
        self.assertEqual(N["c1"]["content"], "Mở đầu.")
        self.assertEqual(N["muc"]["content"], "- Ý danh sách ngay dưới heading")

    def test_comment(self):
        g = parse(HEAD + "@node a  // chú thích\n- web: https://x.org // c\n// dòng comment\n- n: 1\n")
        self.assertEqual(nodes(g)["a"]["attrs"], {"web": "https://x.org", "n": 1})


class ErrorTest(unittest.TestCase):
    def test_v02_syntax(self):
        self.assertIn("cú pháp v0.2", msgs(parse(HEAD + "@a: Tiêu đề\n")))

    def test_label_on_open_line(self):
        g = parse(HEAD + "@node a: Nhãn\n")
        self.assertIn("không có ':'", msgs(g))
        self.assertEqual(nodes(g)["a"]["title"], "Nhãn")

    def test_type_rules(self):
        self.assertIn("node type chưa import", msgs(parse(HEAD + "@node a\n- type: Module\n")))
        self.assertIn("viết hoa chữ đầu", msgs(parse(HEAD + "@node a\n- type: concept\n")))
        self.assertIn("tên node viết thường", msgs(parse(HEAD + "@node Hinh_x\n- n: 1\n")) or
                      msgs(parse(HEAD + "@node hinh_x\n")))

    def test_local_type(self):
        g = parse(HEAD + "@node Hinh\n- label: Hình\n\nMô tả kiểu.\n\n@node a\n- type: Hinh\n")
        self.assertEqual(g["graph"]["errors"], [])
        self.assertEqual(g["graph"]["schema"]["types"]["Hinh"]["title"], "Hình")
        self.assertNotIn("Hinh", nodes(g))

    def test_link_errors(self):
        self.assertIn("link type chưa import", msgs(parse(HEAD + "@node a\n@node b\n- link friend: (a)\n")))
        self.assertIn("không tìm thấy node: zz", msgs(parse(HEAD + "@node a\n- link needs: (zz)\n")))
        self.assertIn("vòng lặp needs", msgs(parse(HEAD + "@node a\n- link needs: (b)\n@node b\n- link needs: (a)\n")))
        self.assertIn("tự sinh", msgs(parse(HEAD + "@node a\n@node b\n- link mention: (a)\n")))

    def test_import_selective(self):
        g = parse("---\nkg: 0.3\nuse:\n- king/schema.node: Concept\n---\n@node a\n- type: Group\n")
        self.assertIn("node type chưa import", msgs(g))
        g = parse("---\nkg: 0.3\nuse:\n- king/schema.node: Khong-co\n---\n")
        self.assertIn("không có node type Khong-co", msgs(g))

    def test_dup_and_bad_attr(self):
        self.assertIn("tên trùng", msgs(parse(HEAD + "@node a\n@node a\n")))
        self.assertIn("viết hai lần", msgs(parse(HEAD + "@node a\n- n: 1\n- n: 2\n")))
        self.assertIn("thuộc tính phải có dạng", msgs(parse(HEAD + "@node a\n- ý không có khóa\n")))
        self.assertIn("thiếu ngoặc đóng", msgs(parse(HEAD + "@node a\n- t: (a, b\n")))

    def test_typo_warning(self):
        g = parse(HEAD + "@node a\n- role: X\n@node b\n- role: Y\n@node c\n- rol: Z\n")
        self.assertIn("có phải role", msgs(g, "warnings"))

    def test_has_not_yet(self):
        self.assertIn("chưa hỗ trợ", msgs(parse(HEAD + "@node a\n- has: (b)\n"), "warnings"))

    def test_hide(self):
        g = parse(HEAD + "# A @a\n- hide: graph, module\n\n@node x\n\n# B @b\n\n@link ban\n- hide: all\n\n"
                  "@node g\n- type: Group\n- hide: (book)\n\n@node y\n- hide: true\n- link ban: (x)\n\n@node z\n- hide: grap\n")
        n = nodes(g)
        self.assertEqual(n["a"]["hide"], ["graph", "module"])
        self.assertEqual(n["g"]["hide"], ["book"])
        self.assertEqual(n["y"]["hide"], ["all"])
        self.assertNotIn("hide", n["x"])                  # con của section bị ẩn: view tự ẩn theo, JSON không ghi
        self.assertNotIn("hide", n["z"])
        self.assertIn("không có view grap", msgs(g, "warnings"))
        self.assertEqual([l["hide"] for l in g["links"] if l["type"] == "ban"], [["all"]])
        self.assertEqual(g["graph"]["schema"]["links"]["ban"]["hide"], ["all"])

    def test_legacy_file(self):
        g = parse("---\nkg: 0.2\n---\n@a: A\n- content: x\n")
        self.assertEqual(g["nodes"][0]["title"], "A")
        self.assertIn("cú pháp cũ", msgs(g, "warnings"))


if __name__ == "__main__":
    unittest.main()
