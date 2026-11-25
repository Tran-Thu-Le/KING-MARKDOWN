"""/api/run in the web server, tested with a fake kir.world module."""
import json
import sys
import threading
import types
import urllib.request

import pytest

from king_markdown import server


class FakeResult:
    def __init__(self, outputs, diags, ok):
        self.outputs, self.diags, self.ok = outputs, diags, ok


@pytest.fixture
def srv(tmp_path):
    server.ROOT[0] = str(tmp_path)
    s = server.Server(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()
    s.server_close()


def post(base, path, body):
    req = urllib.request.Request(base + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


V4 = "---\nkg: v0.4\n---\n@print x\n"


V0 = V4.replace("@print x\n", "")


def test_run_with_fake_kir(srv, monkeypatch):
    mod = types.ModuleType("kir.world")
    seen = {}

    def run_text(text, fname="<string>"):
        seen["args"] = (text, fname)
        return ["a", "b"], []

    mod.run_text = run_text
    monkeypatch.setitem(sys.modules, "kir.world", mod)
    j = post(srv, "/api/run", {"name": "demo.kg.md", "text": V4.replace("\n", "\r\n")})
    assert j["ok"] is True and j["outputs"] == ["a", "b"]
    assert j["diags"] == []
    assert isinstance(j["ms"], int)
    assert seen["args"][0] == V4 and seen["args"][1].endswith("demo.kg.md")


def test_run_on_03_file(srv):
    j = post(srv, "/api/run", {"name": "a.kg.md", "text": "---\nkg: 0.3\n---\n# A @a\n"})
    assert j["ok"] is False and j["diags"] == ["Run is available for kg: v0.4 files"]


def test_run_without_kir_run(srv, monkeypatch):
    monkeypatch.setitem(sys.modules, "kir.world", None)        # import fails
    j = post(srv, "/api/run", {"name": "a.kg.md", "text": V4})
    assert j["ok"] is False and j["error"] == "kir run is not available"


def test_run_real_world_engine(srv):
    j = post(srv, "/api/run", {"name": "w.kg.md", "text": V0 + "@add a b c\n@print(a b c)\n@print(a b d)\n"})
    assert j["ok"] is True and j["outputs"] == ["a b c: true", "a b d: unknown"]


def test_run_real_world_engine_error(srv):
    j = post(srv, "/api/run", {"name": "w.kg.md", "text": V0 + "@add var.x b c\n"})
    assert j["ok"] is False and ":4: E16:" in j["diags"][0]


def test_parse_v04_uses_kir_problems(srv):
    ok = post(srv, "/api/parse", {"name": "w.kg.md", "text": V0 + "@import set\n@add a b c\n@print(a b c and x y z)\n"})
    assert ok["graph"]["errors"] == []                     # no 0.3 "node not found: add"
    bad = post(srv, "/api/parse", {"name": "w.kg.md", "text": V0 + "@add var.x b c\n"})
    assert bad["graph"]["errors"][0]["line"] == 4 and bad["graph"]["errors"][0]["msg"].startswith("E16")
