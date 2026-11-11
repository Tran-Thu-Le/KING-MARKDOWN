# Ops (sửa ngược file .kg.md) viết cho cú pháp v0.2 - ĐÓNG BĂNG ở 0.3 (dev/plan-v3/plan-v3.md).
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from king_markdown.ops import OPS, Doc  # noqa: E402
from king_markdown.legacy import Parser, read  # noqa: E402

TEXT = """---
kg: 0.2
---

# Toán @toan

@dao-ham: Đạo hàm
- link: needs(gioi-han)   // ghi chú

@gioi-han: Giới hạn

# Tin @tin
"""


class OpsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "t.kg.md")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def run_op(self, name, text=TEXT, **args):
        out, extra = OPS[name](Doc(text, self.path), **args)
        g = Parser(out, self.path).build()
        self.assertEqual(g["graph"]["errors"], [], out)
        return out, extra, g

    @staticmethod
    def edges(g):
        return {(l["source"], l["type"], l["target"]) for l in g["links"] if not l.get("tree")}

    @staticmethod
    def parent(g, nid):
        return next(n["parent"] for n in g["nodes"] if n["id"] == nid)

    def test_add_node_in_section(self):
        out, extra, g = self.run_op("add_node", title="Python cơ bản", section="tin")
        self.assertEqual(extra["id"], "python-co-ban")
        self.assertEqual(self.parent(g, "python-co-ban"), "tin")

    def test_add_link_keeps_comment(self):
        out, _, g = self.run_op("add_link", source="dao-ham", target="gioi-han", type="part-of")
        self.assertIn("- link: needs(gioi-han), part-of(gioi-han)   // ghi chú", out)

    def test_add_link_new_line(self):
        _, _, g = self.run_op("add_link", source="gioi-han", target="dao-ham", type="related")
        self.assertIn(("gioi-han", "related", "dao-ham"), self.edges(g))

    def test_delete_link_removes_line(self):
        out, _, g = self.run_op("delete_link", links=[{"source": "dao-ham", "target": "gioi-han", "type": "needs"}])
        self.assertNotIn("- link:", out)
        self.assertEqual(self.edges(g), set())

    def test_move_node(self):
        _, _, g = self.run_op("move_node", ids=["gioi-han"], section="tin")
        self.assertEqual(self.parent(g, "gioi-han"), "tin")

    def test_delete_node(self):
        out, _, g = self.run_op("delete_node", text=TEXT.replace("- link: needs(gioi-han)   // ghi chú\n", ""),
                                ids=["gioi-han"])
        self.assertNotIn("@gioi-han", out)

    def test_rename_keeps_id(self):
        out, _, _ = self.run_op("rename", id="dao-ham", title="Đạo hàm cấp 1")
        self.assertIn("@dao-ham: Đạo hàm cấp 1", out)
        out, _, _ = self.run_op("rename", id="toan", title="Toán học")
        self.assertIn("# Toán học @toan", out)

    @unittest.skip("đóng băng ở 0.3: ops v0.2, schema hệ thống đã sang 0.3")
    def test_schema_add_creates_file_and_use(self):
        out, _, g = self.run_op("schema_add", kind="link", id="lien-quan", title="Liên quan")
        self.assertIn("use: schema", out)
        schema = read(os.path.join(self.dir, "schema.kg.md"))
        self.assertIn("@needs", schema)                 # chép từ templates/schema.kg.md
        self.assertIn("@lien-quan: Liên quan", schema)

    def test_set_meta_typed_and_ordered(self):
        out, _, g = self.run_op("set_meta", id="gioi-han", meta={"type": "concept", "important": "true", "level": "2"})
        self.assertIn("@gioi-han: Giới hạn\n- meta: type=concept, important=true, level=2", out)
        n = next(n for n in g["nodes"] if n["id"] == "gioi-han")
        self.assertEqual(n["meta"], {"type": "concept", "important": True, "level": 2})

    def test_set_meta_replace_and_clear(self):
        text = TEXT.replace("@dao-ham: Đạo hàm\n", "@dao-ham: Đạo hàm\n- meta: type=a\n- meta: role=b\n")
        out, _, _ = self.run_op("set_meta", text=text, id="dao-ham", meta={"type": "c"})
        self.assertEqual(out.count("- meta:"), 1)
        self.assertIn("- meta: type=c\n- link: needs(gioi-han)", out)
        out, _, _ = self.run_op("set_meta", text=out, id="dao-ham", meta={})
        self.assertNotIn("- meta:", out)

    def test_set_field_multiline_before_link(self):
        out, _, g = self.run_op("set_field", id="dao-ham", key="content", value="Dòng 1\n\nDòng 2")
        self.assertIn("- content: Dòng 1\n\n  Dòng 2\n- link: needs(gioi-han)", out)
        n = next(n for n in g["nodes"] if n["id"] == "dao-ham")
        self.assertEqual(n["content"], "Dòng 1\n\nDòng 2")      # dòng trống giữa hai đoạn được giữ
        out, _, _ = self.run_op("set_field", text=out, id="dao-ham", key="content", value="Mới")
        self.assertIn("- content: Mới\n- link:", out)
        self.assertNotIn("Dòng 2", out)

    def test_set_field_show_and_remove(self):
        out, _, g = self.run_op("set_field", id="gioi-han", key="show", value="none")
        self.assertIn("- show: none", out)
        out, _, _ = self.run_op("set_field", text=out, id="gioi-han", key="show", value="")
        self.assertNotIn("- show:", out)

    def test_set_style_on_open_style_file(self):
        """Đang mở chính style.kg.md: sửa văn bản đang mở, không ghi đĩa, không thêm use: vào chính nó."""
        style = os.path.join(self.dir, "style.kg.md")
        text = '---\nkg: 0.2\n---\n\n# Node cụ thể\n\n@s1\n- meta: select="#x", html.shape=box\n'
        with open(style, "w", encoding="utf-8") as f:
            f.write(text)
        out, extra = OPS["set_style"](Doc(text, style), selectors=["#x"], props={"color": "#ff0000"})
        self.assertIn('html.color="#ff0000"', out)
        self.assertNotIn("use:", out)
        self.assertEqual(read(style), text)

    def test_set_style_from_schema_file_adds_no_use(self):
        """Đang mở schema.kg.md rồi chỉnh format: ghi style.kg.md, không thêm use: vào schema."""
        schema = os.path.join(self.dir, "schema.kg.md")
        text = "---\nkg: 0.2\n---\n\n@hinh\n- meta: kind=type\n"
        with open(schema, "w", encoding="utf-8") as f:
            f.write(text)
        out, _ = OPS["set_style"](Doc(text, schema), selectors=["#hinh"], props={"color": "red"})
        self.assertEqual(out, text)
        self.assertIn('select="#hinh", html.color=red', read(os.path.join(self.dir, "style.kg.md")))

    def test_paste_nodes_renames_and_remaps(self):
        clip = "@dao-ham: Đạo hàm\n- link: needs(gioi-han)   // ghi chú\n\n@gioi-han: Giới hạn\n- content: xem @dao-ham\n"
        out, extra, g = self.run_op("paste_nodes", clip=clip, section="tin")
        self.assertEqual(extra["ids"], ["dao-ham-2", "gioi-han-2"])
        self.assertIn("@dao-ham-2: Đạo hàm\n- link: needs(gioi-han-2)   // ghi chú", out)
        self.assertIn("- content: xem @dao-ham-2", out)
        self.assertEqual(self.parent(g, "dao-ham-2"), "tin")

    def test_paste_nodes_rejects_plain_text(self):
        with self.assertRaises(ValueError):
            OPS["paste_nodes"](Doc(TEXT, self.path), clip="chữ thường")

    def test_comment_nodes(self):
        text = TEXT.replace("- link: needs(gioi-han)   // ghi chú\n", "")
        out, _, g = self.run_op("comment_nodes", text=text, ids=["gioi-han"])
        self.assertIn("// @gioi-han: Giới hạn", out)
        self.assertNotIn("gioi-han", {n["id"] for n in g["nodes"]})

    def test_schema_style_in_data_file(self):
        """Schema + style viết ngay trong file dữ liệu: áp cho file đó; sửa format ghi vào # Style của chính file."""
        text = ("---\nkg: 0.2\n---\n\n@a: A\n- meta: type=hinh\n\n# Schema\n\n@hinh\n- meta: kind=type\n\n"
                "# Style\n\n@s-hinh\n- meta: select=\"type=hinh\", html.color=red\n")
        g = Parser(text, self.path).build()
        self.assertEqual(g["graph"]["errors"], [])
        n = {x["id"]: x for x in g["nodes"]}
        self.assertEqual(n["a"]["style"]["html"]["color"], "red")
        self.assertEqual((n["hinh"]["def"], n["s-hinh"]["def"]), ("schema", "style"))
        bad = Parser(text.replace("type=hinh\n\n# Schema", "type=khac\n\n# Schema"), self.path).build()
        self.assertIn("kiểu node không khai báo trong schema: khac", " ".join(e["msg"] for e in bad["graph"]["errors"]))
        out, _ = OPS["set_style"](Doc(text, self.path), selectors=["#a"], props={"shape": "box"})
        self.assertNotIn("use:", out)
        self.assertNotIn("# Node cụ thể", out)
        self.assertIn('# Style\n\n@s-hinh\n- meta: select="type=hinh", html.color=red\n\n@s-a\n- meta: select="#a", html.shape=box', out)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "style.kg.md")))

    @unittest.skip("đóng băng ở 0.3: ops v0.2, schema hệ thống đã sang 0.3")
    def test_system_schema_style(self):
        """use: king/schema, king/style đọc bộ mẫu hệ thống; sửa format không ghi vào bộ mẫu mà vào style.kg.md của thư mục."""
        from king_markdown.parser import system_file
        text = "---\nkg: 0.2\nuse: king/schema, king/style\n---\n\n@a: A\n- meta: type=concept, role=Nạp\n"
        g = Parser(text, self.path).build()
        self.assertEqual(g["graph"]["errors"], [])
        self.assertEqual(g["graph"]["use"], ["king/schema.kg.md", "king/style.kg.md"])
        self.assertIn("concept", g["graph"]["schema"]["types"])
        system_style = system_file("style")
        before = read(system_style)
        out, _ = OPS["set_style"](Doc(text, self.path), selectors=["#a"], props={"color": "red"})
        self.assertEqual(read(system_style), before)
        self.assertIn("use: king/schema, king/style, style", out)
        self.assertIn('select="#a", html.color=red', read(os.path.join(self.dir, "style.kg.md")))

    def test_set_style(self):
        out, _, _ = self.run_op("set_style", selectors=["#dao-ham"], props={"shape": "box"})
        style = read(os.path.join(self.dir, "style.kg.md"))
        self.assertIn('select="#dao-ham", html.shape=box', style)
        g = Parser(out, self.path).build()
        n = next(n for n in g["nodes"] if n["id"] == "dao-ham")
        self.assertEqual(n["style"]["html"]["shape"], "box")


if __name__ == "__main__":
    unittest.main()
