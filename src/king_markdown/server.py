"""king_markdown.server - server HTTP cục bộ cho editor (chỉ thư viện chuẩn).

Chỉ nghe 127.0.0.1. Trang web/index.html gọi các API dưới đây; phép sửa nằm trong ops.py.
Chạy: king serve [thư mục] [--port 8765] [--no-browser]
"""
import json
import os
import re
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .ops import OPS, Doc, seed, write
from .parser import Parser, read, slug

ROOT = [os.getcwd()]
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
JS = ("editor", "graph", "explorer", "book", "module", "inspect", "app")
ASSETS = {"/app.css": "text/css; charset=utf-8",
          **{f"/js/{n}.js": "text/javascript; charset=utf-8" for n in JS}}


# ====================== file / thư mục ======================
def kg_path(name):
    base = os.path.basename(name or "")
    if base != name or not base.endswith(".kg.md"):
        raise ValueError(f"tên file không hợp lệ: {name}")
    return os.path.join(ROOT[0], base)


def kg_files(folder):
    try:
        return sorted(f for f in os.listdir(folder) if f.endswith(".kg.md"))
    except OSError:
        return []


def side_mtime(name):
    return max([os.path.getmtime(os.path.join(ROOT[0], f)) for f in kg_files(ROOT[0]) if f != name] or [0])


def list_dirs(path):
    path = os.path.abspath(path or ROOT[0])
    if not os.path.isdir(path):
        raise ValueError(f"không phải thư mục: {path}")
    dirs = []
    for e in sorted(os.scandir(path), key=lambda e: e.name.lower()):
        if e.is_dir() and not e.name.startswith((".", "__")):
            dirs.append({"name": e.name, "path": e.path, "kg": len(kg_files(e.path))})
    parent = os.path.dirname(path)
    return {"path": path, "parent": parent if parent != path else None, "dirs": dirs, "files": kg_files(path)}


def new_file(name):
    base = name.strip()
    base = base[:-6] if base.endswith(".kg.md") else base
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", base):
        raise ValueError("tên file chỉ gồm chữ không dấu, số, - _ .")
    path = os.path.join(ROOT[0], base + ".kg.md")
    if os.path.exists(path):
        raise ValueError(f"đã có {base}.kg.md")
    for role in ("schema", "style"):
        f = os.path.join(ROOT[0], role + ".kg.md")
        if not os.path.exists(f):
            seed(f, role)
    write(path, f"---\nkg: 0.2\nuse: schema, style\n---\n\n# {base} @{slug(base)}\n")
    return {"name": base + ".kg.md"}


# ====================== HTTP ======================
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, obj, code=200, ctype="application/json; charset=utf-8"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def local(self):
        return self.headers.get("Host", "").rsplit(":", 1)[0] in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self.local():
            return self.reply({"error": "chỉ nhận truy cập từ máy này"}, 403)
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                return self.reply(read(os.path.join(WEB, "index.html")).encode("utf-8"),
                                  ctype="text/html; charset=utf-8")
            if u.path in ASSETS:
                return self.reply(read(os.path.join(WEB, *u.path[1:].split("/"))).encode("utf-8"),
                                  ctype=ASSETS[u.path])
            if u.path == "/api/state":
                return self.reply({"root": ROOT[0], "files": kg_files(ROOT[0]), "ops": sorted(OPS)})
            if u.path == "/api/dirs":
                return self.reply(list_dirs(q.get("path")))
            if u.path == "/api/file":
                p = kg_path(q.get("name"))
                return self.reply({"text": read(p), "mtime": os.path.getmtime(p), "side": side_mtime(q["name"])})
            if u.path == "/api/mtime":
                p = kg_path(q.get("name"))
                return self.reply({"mtime": os.path.getmtime(p), "side": side_mtime(q["name"])})
            self.reply({"error": "không có"}, 404)
        except Exception as e:                                   # noqa: BLE001
            self.reply({"error": str(e)}, 400)

    def do_POST(self):
        if not self.local() or not self.headers.get("Content-Type", "").startswith("application/json"):
            return self.reply({"error": "yêu cầu không hợp lệ"}, 403)
        try:
            b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            path = urlparse(self.path).path
            if path == "/api/ping":
                return self.reply({"ok": CLIENTS.ping(b["id"])})
            if path == "/api/bye":
                return self.reply({"ok": CLIENTS.bye(b["id"])})
            if path == "/api/open-folder":
                p = os.path.abspath(b["path"])
                if not os.path.isdir(p):
                    raise ValueError(f"không phải thư mục: {p}")
                ROOT[0] = p
                return self.reply({"root": p, "files": kg_files(p)})
            if path == "/api/new":
                return self.reply(new_file(b["name"]))
            if path == "/api/save":
                p = kg_path(b["name"])
                write(p, b["text"])
                return self.reply({"mtime": os.path.getmtime(p)})
            if path == "/api/parse":
                return self.reply(Parser(b["text"].replace("\r\n", "\n"), kg_path(b["name"])).build())
            if path == "/api/op":
                d = Doc(b["text"], kg_path(b["name"]))
                text, extra = OPS[b["op"]](d, **(b.get("args") or {}))
                return self.reply({"text": text, **extra})
            self.reply({"error": "không có"}, 404)
        except KeyError as e:
            self.reply({"error": f"thiếu hoặc sai: {e}"}, 400)
        except Exception as e:                                   # noqa: BLE001
            self.reply({"error": str(e)}, 400)


class Server(ThreadingHTTPServer):
    # Trên Windows, SO_REUSEADDR cho hai tiến trình cùng nghe một cổng (request rơi vào server cũ),
    # nên tắt đi để cổng đang bận thì nhảy sang cổng kế tiếp.
    allow_reuse_address = os.name != "nt"


class Clients:
    """Các trang editor đang mở. Trang gửi /api/ping mỗi 10 s và /api/bye khi đóng.
    Đã từng có trang mà nay không còn trang nào (sau GRACE giây, để F5 tải lại kịp) → dừng server."""
    GRACE, STALE = 3.0, 90.0          # STALE: tab bị trình duyệt hãm timer (~1 lần/phút) vẫn chưa bị coi là đóng

    def __init__(self):
        self.seen, self.lock, self.used, self.empty_at = {}, threading.Lock(), False, None

    def ping(self, cid):
        with self.lock:
            self.seen[str(cid)] = time.monotonic()
            self.used, self.empty_at = True, None
        return True

    def bye(self, cid):
        with self.lock:
            self.seen.pop(str(cid), None)
        return True

    def all_closed(self):
        now = time.monotonic()
        with self.lock:
            self.seen = {k: t for k, t in self.seen.items() if now - t < self.STALE}
            if not self.used or self.seen:
                self.empty_at = None
                return False
            self.empty_at = self.empty_at or now
            return now - self.empty_at >= self.GRACE


CLIENTS = Clients()


def watch(srv):
    while True:
        time.sleep(0.5)
        if CLIENTS.all_closed():
            print("Đã đóng trang editor: dừng server.", flush=True)
            srv.shutdown()
            return


def serve(folder=".", port=8765, browser=True, keep=False):
    ROOT[0] = os.path.abspath(folder)
    for p in range(port, port + 20):
        try:
            srv = Server(("127.0.0.1", p), Handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit("không mở được cổng nào")
    url = f"http://127.0.0.1:{p}/"
    tail = "Ctrl+C để dừng" if keep else "đóng trang hoặc Ctrl+C để dừng"
    print(f"Editor: {url}  (thư mục {ROOT[0]})  {tail}", flush=True)
    if not keep:
        threading.Thread(target=watch, args=(srv,), daemon=True).start()
    if browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
