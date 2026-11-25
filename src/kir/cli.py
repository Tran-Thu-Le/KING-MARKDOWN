"""CLI: `kir run file.kg.md -o out.json` · `kir ask file.kg.md "?x friend-of bob"`."""
import argparse
import json
import sys

from .parser import parse_file
from .query import ask


def main(argv=None):
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="kir", description="KING IR v0.4")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="parse + export node-link JSON")
    r.add_argument("file")
    r.add_argument("-o", "--out")
    a = sub.add_parser("ask", help="query triple patterns")
    a.add_argument("file")
    a.add_argument("pattern")
    o = sub.add_parser("open", help="open the KING web app on a file or folder")
    o.add_argument("path", nargs="?", default=".")
    o.add_argument("--view", choices=("book", "graph", "text", "tree", "module"))
    o.add_argument("--keep", action="store_true", help="keep the server running after the page closes")
    o.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "open":
        try:
            from king_markdown.open import open_in_browser   # lazy: kir does not depend on king_markdown
        except ImportError:
            sys.exit("error: `kir open` needs the king_markdown package (pip install -e .)")
        open_in_browser(args.path, args.view, args.keep, not args.no_browser)
        return 0

    import os
    if not os.path.isfile(args.file):
        sys.exit(f"no such file: {os.path.abspath(args.file)}")
    res = parse_file(args.file)
    for d in res.diags:
        print(d, file=sys.stderr)
    if res.errors:
        return sys.exit(1)
    if args.cmd == "run":
        text = json.dumps(res.graph.to_dict(), ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            print(f"OK: {len(res.graph.nodes)} nodes, {len(res.graph.edges)} edges -> {args.out}")
        else:
            print(text)
    else:
        try:
            cols, rows = ask(res.graph, args.pattern)
        except ValueError as e:
            print(f"pattern error: {e}", file=sys.stderr)
            sys.exit(1)
        print("\t".join("?" + c for c in cols))
        for row in rows:
            print("\t".join(json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v for v in row))
    return 0
