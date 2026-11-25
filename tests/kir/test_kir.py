import json
import subprocess
import sys
from pathlib import Path

import pytest

from kir.parser import parse_file, parse_text
from kir.query import ask

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "examples" / "kir"
HDR = "---\nkg: v0.4\n---\n"


def test_demo_clean():
    res = parse_file(EX / "demo.kg.md")
    assert res.errors == []
    assert len(res.asks) == 2
    assert res.graph.derived[0]["id"] == "demo:parents"


def test_networkx_roundtrip():
    nxb = pytest.importorskip("kir.backends.networkx")
    data = parse_file(EX / "demo.kg.md").graph.to_dict()
    back = nxb.to_json(nxb.from_json(json.loads(json.dumps(data))))
    dump = lambda d: json.dumps(d, sort_keys=True, ensure_ascii=False)
    assert dump(back) == dump(data)
    G = nxb.from_json(data)
    assert G.has_edge("demo:alice", "demo:carol", key="knows")
    assert G.edges["demo:alice", "demo:carol", "knows"]["id"] == "demo:f1"


@pytest.mark.parametrize("fname,code,line", [
    ("e1-version.kg.md", "E1", 2), ("e2-syntax.kg.md", "E2", 5),
    ("e3-name.kg.md", "E3", 6), ("e4-duplicate.kg.md", "E4", 6),
    ("e5-reference.kg.md", "E5", 6), ("e6-variable.kg.md", "E6", 6),
])
def test_errors(fname, code, line):
    errs = parse_file(EX / "errors" / fname).errors
    assert [(e.code, e.line) for e in errs] == [(code, line)]
    assert str(errs[0]).startswith(f"{fname}:{line}: {code}")


def test_ask():
    g = parse_file(EX / "demo.kg.md").graph
    assert ask(g, "?x friend-of bob") == (["x"], [("alice",), ("carol",)])
    cols, rows = ask(g, "?x is-a person, ?x knows ?y")
    assert rows == [("alice", "carol")]


def test_case_insensitive():
    g = parse_text(HDR + "@add Alice Knows BOB\n@add alice knows bob\n", "t.kg.md").graph
    assert {e[:3] for e in g.edges} == {("t:alice", "t:bob", "knows")}
    assert g.nodes["t:alice"]["label"] == "Alice"


def test_anonymous_distinct():
    g = parse_text(HDR + "@add _ r a\n@add _ r a\n", "t.kg.md").graph
    assert len({e[0] for e in g.edges}) == 2


def test_mid_line_at_is_prose():
    res = parse_text(HDR + "mail a@gmail.com @add x y z\n\\@foo bar\n", "t.kg.md")
    assert res.diags == [] and res.graph.edges == []


def test_fence_preserved():
    src = HDR + "@block code\n```python\n@decorator\nx = 1  // x\n```\n"
    res = parse_text(src, "t.kg.md")
    assert res.errors == []
    body = [res.graph.nodes[o]["value"] for s, o, k, _ in res.graph.edges if k == "body"]
    assert body == ["@decorator\nx = 1  // x"]
    assert ("t:code", "kg:python", "lang") in {e[:3] for e in res.graph.edges}


def test_warning_single_use():
    res = parse_text(HDR + "@add a r b\n@add a r c\n", "t.kg.md")
    assert {d.msg.split("`")[1] for d in res.warnings} == {"b", "c"}


def test_cli_run_compile_export(tmp_path):
    env = {**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")}
    kir = lambda *a: subprocess.run([sys.executable, "-m", "kir", *map(str, a)], env=env,
                                    capture_output=True, text=True, encoding="utf-8")
    ex = EX / "world-closed.kg.md"
    r = kir("run", ex)
    assert r.returncode == 0 and r.stdout.splitlines() ==         (EX / "world-closed.expected.txt").read_text(encoding="utf-8").splitlines()
    assert "@add k.file k.import set" in kir("compile", ex).stdout
    out = tmp_path / "o.json"
    assert kir("export", ex, "--json", out).returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["multigraph"]
    assert "<urn:kir:newton>" in kir("export", ex, "--rdf", "-").stdout
    bad = tmp_path / "bad.kg.md"
    bad.write_text("---\nkg: v0.4\n---\n@add a b\n", encoding="utf-8")
    r = kir("run", bad)
    assert r.returncode == 1 and ":4: E2:" in r.stderr


def test_no_king_markdown_import():
    for p in (ROOT / "src" / "kir").rglob("*.py"):
        import re
        assert not re.search(r"^(import|from) king_markdown", p.read_text(encoding="utf-8"), re.M), p


def test_kir_open_help():
    import subprocess, sys, os
    env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    r = subprocess.run([sys.executable, "-m", "kir", "open", "--help"], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "--view" in r.stdout


def test_kir_does_not_import_king_markdown():
    import subprocess, sys, os
    env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    code = ("import sys, kir, kir.cli, kir.parser, kir.query, kir.model, kir.backends; "
            "assert not any(m.split('.')[0] == 'king_markdown' for m in sys.modules)")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
