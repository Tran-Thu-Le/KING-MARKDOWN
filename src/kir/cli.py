"""CLI for KIR (charter edition).

    kir run file.kg.md                 compile + run rules + print (`@print`) results
    kir compile file.kg.md             KING sugar -> pure KIR (`@add s r o` lines)
    kir export file.kg.md --json OUT   networkx node-link JSON   (--rdf OUT: RDF Turtle)
    kir view [path] [--view text]      open the KING web app (server stops when the page closes)
"""
import argparse
import os
import sys


def _need_file(path):
    if not os.path.isfile(path):
        sys.exit(f"no such file: {os.path.abspath(path)}")


def main(argv=None):
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="kir", description="KIR: KING IR (@add s r o)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="compile + run rules + print results").add_argument("file")
    sub.add_parser("compile", help="KING sugar -> pure KIR").add_argument("file")
    e = sub.add_parser("export", help="export to networkx node-link JSON or RDF Turtle")
    e.add_argument("file")
    e.add_argument("--json", metavar="OUT", help="write JSON ('-' = stdout; default)")
    e.add_argument("--rdf", metavar="OUT", help="write RDF Turtle ('-' = stdout)")
    e.add_argument("--base", help="IRI prefix for names")
    for name in ("view", "open"):
        o = sub.add_parser(name, help="open the KING web app on a file or folder"
                           + (" (alias of view)" if name == "open" else ""))
        o.add_argument("path", nargs="?", default=".")
        o.add_argument("--view", choices=("text", "book", "lecture", "graph", "tree", "module"))
        o.add_argument("--keep", action="store_true", help="keep the server running after the page closes")
        o.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd in ("view", "open"):
        try:
            from king_markdown.open import open_in_browser   # lazy: kir does not depend on king_markdown
        except ImportError:
            sys.exit("error: `kir view` needs the king_markdown package (pip install -e .)")
        open_in_browser(args.path, args.view, args.keep, not args.no_browser)
        return 0

    _need_file(args.file)
    if args.cmd == "run":
        from .world import main as run_main
        return run_main([args.file])
    if args.cmd == "compile":
        from .compile import main as compile_main
        return compile_main([args.file])
    from .export import main as export_main
    rest = [args.file] + (["--json", args.json] if args.json else []) + (["--rdf", args.rdf] if args.rdf else []) \
        + (["--base", args.base] if args.base else [])
    return export_main(rest)
