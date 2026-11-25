"""Open the KING web app on a file or folder; the server stops when the editor page closes."""
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote

VIEWS = ("graph", "text", "tree", "book", "lecture", "module")


def free_port(start=8765, count=20):
    """First free localhost port in start..start+count-1 (8765-8784), or None."""
    for p in range(start, start + count):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return None


def open_in_browser(path=".", view=None, keep=False, browser=True):
    """Serve the folder of `path` (or `path` itself) and open `?file=` in the browser. Blocks until stopped."""
    from .server import serve
    p = Path(path).resolve()
    if not p.exists():
        sys.exit(f"not found: {p}")
    if p.is_file():
        if not p.name.endswith(".kg.md"):
            sys.exit(f"not a .kg.md file: {p.name}")
        folder, fname = p.parent, p.name
    else:
        folder, fname = p, None
    if view and view not in VIEWS:
        sys.exit(f"unknown view: {view} (use {', '.join(VIEWS)})")
    port = free_port()
    if port is None:
        sys.exit("no free port in 8765-8784")
    url = f"http://127.0.0.1:{port}/"
    q = []
    if fname:
        q.append("file=" + quote(fname))
    if view:
        q.append("view=" + view)
    if q:
        url += "?" + "&".join(q)
    print(f"KING {url}  (folder {folder}; {'Ctrl+C to stop' if keep else 'close the page to stop'})", flush=True)
    if browser:
        threading.Timer(0.8, webbrowser.open, [url]).start()
    serve(str(folder), port, browser=False, keep=keep)
