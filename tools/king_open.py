"""Open the KING web app on a file or folder; the server stops when the editor page closes.

  python tools/king_open.py <file.kg.md | folder> [--view graph|text|tree|book|module] [--keep] [--no-browser]

Same as `kir open`. Works without installing the package (adds src/ to sys.path).
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from king_markdown.open import VIEWS, open_in_browser  # noqa: E402


def main():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Open the KING web app on a .kg.md file or folder.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--view", choices=VIEWS)
    ap.add_argument("--keep", action="store_true", help="keep the server running after the page closes")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    open_in_browser(a.path, a.view, a.keep, not a.no_browser)


if __name__ == "__main__":
    main()
