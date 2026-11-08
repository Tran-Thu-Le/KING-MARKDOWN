"""king_markdown.cli - lệnh `king`.

    king serve [thư mục] [--port 8765] [--no-browser] [--keep]   # mở editor; đóng trang thì server dừng
    king parse bai.kg.md                                # in JSON
    king parse bai.kg.md -o graph.json --strict         # ghi JSON; thoát mã 1 nếu có lỗi
    king html bai.kg.md bai.html                        # HTML tĩnh, chỉ xem
"""
import argparse
import json
import os
import re
import sys

from .parser import Parser, read
from .server import WEB


def static_html(name, text, graph):
    """web/index.html ở chế độ chỉ xem: nhúng CSS, JS và dữ liệu vào một file, không cần server."""
    page = read(os.path.join(WEB, "index.html"))
    page = page.replace('<link rel="stylesheet" href="app.css">',
                        f"<style>\n{read(os.path.join(WEB, 'app.css'))}</style>", 1)
    page = re.sub(r'<script src="(js/[a-z]+\.js)"></script>',
                  lambda m: "<script>\n" + read(os.path.join(WEB, *m.group(1).split("/"))) + "</script>",
                  page)
    data = json.dumps({"name": name, "text": text, "graph": graph}, ensure_ascii=False)
    return page.replace("/*KG_STATIC*/null", data.replace("</", "<\\/"), 1)


def report(data, path):
    for e in data["graph"]["errors"]:
        print(f"LỖI   {e.get('file', path)}:{e['line']}: {e['msg']}", file=sys.stderr)
    for w in data["graph"]["warnings"]:
        print(f"CHÚ Ý {w.get('file', path)}:{w['line']}: {w['msg']}", file=sys.stderr)


def cmd_parse(a):
    data = Parser(read(a.file), a.file).build()
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    report(data, a.file)
    return 1 if a.strict and data["graph"]["errors"] else 0


def cmd_html(a):
    text = read(a.file)
    data = Parser(text, a.file).build()
    out = a.out or re.sub(r"(\.kg)?\.md$", "", a.file) + ".html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(static_html(os.path.basename(a.file), text, data))
    report(data, a.file)
    print(f"Đã ghi {out}")
    return 1 if a.strict and data["graph"]["errors"] else 0


def cmd_serve(a):
    from .server import serve
    serve(a.folder, a.port, browser=not a.no_browser, keep=a.keep)
    return 0


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="king", description="KING Markdown (.kg.md): Knowledge is KING.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("serve", help="mở editor trên trình duyệt")
    p.add_argument("folder", nargs="?", default=".")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--keep", action="store_true", help="không tự dừng khi đóng trang editor")
    p.set_defaults(fn=cmd_serve)

    p = sub.add_parser("parse", help=".kg.md → JSON (node-link, dùng được với networkx)")
    p.add_argument("file")
    p.add_argument("-o", "--out", help="file JSON đầu ra (bỏ trống: in ra màn hình)")
    p.add_argument("--strict", action="store_true", help="thoát mã 1 nếu có lỗi")
    p.set_defaults(fn=cmd_parse)

    p = sub.add_parser("html", help=".kg.md → HTML tĩnh, chỉ xem")
    p.add_argument("file")
    p.add_argument("out", nargs="?", help="file HTML (mặc định: cùng tên, đuôi .html)")
    p.add_argument("--strict", action="store_true", help="thoát mã 1 nếu có lỗi")
    p.set_defaults(fn=cmd_html)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
