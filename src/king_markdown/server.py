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
from .ops03 import OPS03, Doc03
from .parser import Parser, kg_version, read, slug

ROOT = [os.getcwd()]
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
JS = ("editor", "graph", "explorer", "book", "lecture", "module", "inspect", "run", "app")
ASSETS = {"/app.css": "text/css; charset=utf-8",
          **{f"/js/{n}.js": "text/javascript; charset=utf-8" for n in JS}}


# ====================== file / thư mục ======================
def kg_path(name):
    base = os.path.basename(name or "")
    if base != name or not base.endswith(".kg.md"):
        raise ValueError(f"invalid file name: {name}")
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
        raise ValueError(f"not a directory: {path}")
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
        raise ValueError("file name may only contain ASCII letters, digits, - _ .")
    path = os.path.join(ROOT[0], base + ".kg.md")
    if os.path.exists(path):
        raise ValueError(f"{base}.kg.md already exists")
    # file mới theo cú pháp hiện hành 0.3 (không còn sinh schema/style kiểu 0.2)
    write(path, f"---\nkg: 0.3\n---\n\n# {base} @{slug(base)}\n")
    return {"name": base + ".kg.md"}


def kg_version(text):
    lines = text.replace("\r\n", "\n").splitlines()
    if lines and lines[0].strip() == "---":
        for raw in lines[1:]:
            if raw.strip() == "---":
                break
            m = re.match(r"\s*kg\s*:\s*(\S+)", raw)
            if m:
                return m.group(1)
    return None


def is_kir(text):
    return kg_version(text) in ("v0.4", "0.4")


def _kir_run(text, name):
    """kir.world.run_text with the file's real path (relative @import works); paths shown as file names."""
    from kir.world import run_text
    try:
        path = kg_path(name) if name else "<string>"
    except ValueError:
        path = os.path.basename(name or "") or "<string>"
    outputs, diags = run_text(text, str(path))
    short = os.path.basename(str(path))
    return outputs, [d.replace(str(path), short) for d in diags]


def kir_parse(text, name):
    """Outline/headings from the 0.3 parser, problems from kir (0.3 errors do not apply to kg: v0.4)."""
    g = Parser(text, name).build()
    errs = []
    try:
        for d in _kir_run(text, name)[1]:
            m = re.match(r".*?:(\d+): (.*)$", d)
            errs.append({"line": int(m.group(1)), "msg": m.group(2)} if m else {"line": 1, "msg": d})
    except Exception as e:                                      # noqa: BLE001
        errs.append({"line": 1, "msg": f"kir: {e}"})
    g["graph"]["errors"], g["graph"]["warnings"] = errs, []
    return g


def run_kir(text, name=None):
    """Run a `kg: v0.4` file with kir.world (lazy import); returns the /api/run JSON."""
    text = text.replace("\r\n", "\n")
    if not is_kir(text):
        return {"ok": False, "outputs": [], "diags": ["Run is available for kg: v0.4 files"], "ms": 0}
    try:
        import kir.world                                        # noqa: F401
    except Exception:                                            # noqa: BLE001
        return {"ok": False, "outputs": [], "diags": ["kir run is not available"], "ms": 0,
                "error": "kir run is not available"}
    t0 = time.perf_counter()
    outputs, diags = _kir_run(text, name)
    return {"ok": not diags, "outputs": [str(o) for o in outputs],
            "diags": [str(d) for d in diags], "ms": int((time.perf_counter() - t0) * 1000)}


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
            return self.reply({"error": "local access only"}, 403)
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
            self.reply({"error": "not found"}, 404)
        except Exception as e:                                   # noqa: BLE001
            self.reply({"error": str(e)}, 400)

    def do_POST(self):
        if not self.local() or not self.headers.get("Content-Type", "").startswith("application/json"):
            return self.reply({"error": "invalid request"}, 403)
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
                    raise ValueError(f"not a directory: {p}")
                ROOT[0] = p
                return self.reply({"root": p, "files": kg_files(p)})
            if path == "/api/new":
                return self.reply(new_file(b["name"]))
            if path == "/api/save":
                p = kg_path(b["name"])
                write(p, b["text"])
                return self.reply({"mtime": os.path.getmtime(p)})
            if path == "/api/parse":
                text = b["text"].replace("\r\n", "\n")
                if is_kir(text):
                    return self.reply(kir_parse(text, b["name"]))
                return self.reply(Parser(text, kg_path(b["name"])).build())
            if path == "/api/run":
                return self.reply(run_kir(b["text"], b.get("name")))
            if path == "/api/op":
                src = b["text"].replace("\r\n", "\n")
                ver = kg_version(src) or "0.3"
                if ver.startswith(("0.1", "0.2")):                   # file cũ: thao tác theo cú pháp 0.2
                    d, ops = Doc(src, kg_path(b["name"])), OPS
                else:                                                # 0.3: ghi đúng cú pháp 0.3
                    d, ops = Doc03(src, kg_path(b["name"])), OPS03
                text, extra = ops[b["op"]](d, **(b.get("args") or {}))
                return self.reply({"text": text, **extra})
            self.reply({"error": "not found"}, 404)
        except KeyError as e:
            self.reply({"error": f"missing or invalid: {e}"}, 400)
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
    STARTUP = 60.0                    # no page connected within this time (page never loaded) -> stop too

    def __init__(self):
        self.seen, self.lock, self.used, self.empty_at = {}, threading.Lock(), False, None
        self.started = time.monotonic()

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
            if not self.used:
                return now - self.started >= self.STARTUP
            if self.seen:
                self.empty_at = None
                return False
            self.empty_at = self.empty_at or now
            return now - self.empty_at >= self.GRACE


CLIENTS = Clients()


def watch(srv):
    while True:
        time.sleep(0.5)
        if CLIENTS.all_closed():
            print("No editor page open: stopping server.", flush=True)
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
        raise SystemExit("could not open any port")
    url = f"http://127.0.0.1:{p}/"
    tail = "Ctrl+C to stop" if keep else "close the page or Ctrl+C to stop"
    print(f"Editor: {url}  (folder {ROOT[0]})  {tail}", flush=True)
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
