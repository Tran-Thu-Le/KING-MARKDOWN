"""Parser KING IR (kg: v0.4). Python thuần, không import king_markdown."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import BUILTIN_NODES, DEFAULT_LANGUAGES, RESERVED, Diag, Graph

NAME_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
NUM_RE = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?\Z")
FENCE = "`" * 3


@dataclass
class Tok:
    kind: str   # name | str | num | bool | none | var | anon | eq | comma | bad
    text: str
    value: object = None


class LexError(Exception):
    pass


def tokenize(s):
    """Tách token của 1 dòng lệnh; bỏ comment `//` ngoài chuỗi."""
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif s.startswith("//", i):
            break
        elif c == '"':
            j, buf = i + 1, []
            while j < n and s[j] != '"':
                if s[j] == "\\" and j + 1 < n and s[j + 1] in '"\\':
                    j += 1
                buf.append(s[j])
                j += 1
            if j >= n:
                raise LexError("unterminated string")
            toks.append(Tok("str", s[i:j + 1], "".join(buf)))
            i = j + 1
        elif c == ",":
            toks.append(Tok("comma", ","))
            i += 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in ',"' and not s.startswith("//", j):
                j += 1
            toks.append(classify(s[i:j]))
            i = j
    return toks


def classify(w):
    lw = w.lower()
    if w == "=":
        return Tok("eq", w)
    if w == "_":
        return Tok("anon", w)
    if w.startswith("?"):
        return Tok("var" if NAME_RE.match(w[1:]) else "bad", w, lw[1:])
    if NUM_RE.match(w):
        return Tok("num", w, int(w) if re.fullmatch(r"-?\d+", w) else float(w))
    if lw in ("true", "false"):
        return Tok("bool", w, lw == "true")
    if lw == "none":
        return Tok("none", w, None)
    if NAME_RE.match(w):
        return Tok("name", w, lw)
    return Tok("bad", w)


@dataclass
class Result:
    graph: Graph
    diags: list = field(default_factory=list)
    asks: list = field(default_factory=list)   # (line, patterns)

    @property
    def errors(self):
        return [d for d in self.diags if d.code.startswith("E")]

    @property
    def warnings(self):
        return [d for d in self.diags if d.code == "W"]


def parse_file(path):
    p = Path(path)
    return parse_text(p.read_text(encoding="utf-8"), p.name)


def _stem(fname):
    return fname[:-6] if fname.endswith(".kg.md") else Path(fname).stem


def _builtin(lw):
    return lw in BUILTIN_NODES or lw in RESERVED or lw in DEFAULT_LANGUAGES


def value_id(v):
    return "value:" + json.dumps(v, ensure_ascii=False)


def parse_text(text, fname="<string>"):
    stem = _stem(fname)
    g = Graph(stem)
    res = Result(g)
    lines = text.splitlines()

    def err(code, ln, msg):
        res.diags.append(Diag(code, fname, ln, msg))

    # --- frontmatter ---
    start, version = 0, None
    if lines and lines[0].strip() == "---":
        for k in range(1, len(lines)):
            if lines[k].strip() == "---":
                start = k + 1
                break
            m = re.match(r"\s*kg\s*:\s*(.*?)\s*\Z", lines[k])
            if m:
                version = (m.group(1).strip("'\""), k + 1)
    if version is None:
        err("E1", 1, "missing `kg: v0.4` in frontmatter")
    elif version[0] != "v0.4":
        err("E1", version[1], f"unsupported version `{version[0]}`, need `kg: v0.4`")

    defined = {}            # tên p / block -> dòng
    refs = []               # (a, b, line) của a.b
    uses = {}               # tên -> [số lần, dòng đầu]
    blocks = []             # (node id, lang, line)
    counter = [0]

    def node_of(t, ln):
        """Token -> id node (None nếu lỗi)."""
        if t.kind == "name":
            lw = t.value
            if _builtin(lw):
                return g.add_node(f"kg:{lw}", label=lw)
            nid = g.add_node(f"{stem}:{lw}")
            g.nodes[nid].setdefault("label", t.text)
            uses.setdefault(lw, [0, ln])[0] += 1
            core = lw.strip(".")
            if "." in core:
                a, b = core.rsplit(".", 1)
                refs.append((a, b, ln))
                g.nodes[nid]["ref"] = [f"{stem}:{a}", b]
            return nid
        if t.kind == "anon":
            counter[0] += 1
            return g.add_node(f"{stem}:_{counter[0]}", label="_", anon=True)
        if t.kind in ("str", "num", "bool", "none"):
            kind = {"str": "string", "num": "number", "bool": "boolean", "none": "none"}[t.kind]
            return g.add_node(value_id(t.value), kind=kind, value=t.value)
        if t.kind == "bad":
            err("E3", ln, f"invalid name `{t.text}` (use only [A-Za-z0-9._-])")
        elif t.kind == "var":
            err("E6", ln, f"variable `{t.text}` is only allowed in `@ask` or `@add p = …`")
        else:
            err("E2", ln, f"misplaced token `{t.text}`")
        return None

    def link_of(t, ln):
        if t.kind == "eq":
            return "="
        if t.kind == "name":
            return t.value
        if t.kind in ("bad", "var"):
            node_of(t, ln)
        else:
            err("E2", ln, f"link must be a name, got `{t.text}`")
        return None

    def define(t, ln):
        if t.kind != "name":
            if t.kind == "bad":
                err("E3", ln, f"invalid name `{t.text}`")
            elif t.kind in ("bool", "none"):
                err("E3", ln, f"`{t.text}` is a reserved name")
            else:
                err("E2", ln, f"defined name must be a name, got `{t.text}`")
            return None
        lw = t.value
        if _builtin(lw):
            err("E3", ln, f"`{t.text}` is a reserved name")
            return None
        if lw in defined:
            err("E4", ln, f"`{t.text}` already defined at line {defined[lw]}")
            return None
        defined[lw] = ln
        return lw

    i, fence = start, False
    while i < len(lines):
        raw, ln = lines[i], i + 1
        i += 1
        if fence:                       # code fence trong văn xuôi: bỏ qua
            if raw.lstrip().startswith(FENCE):
                fence = False
            continue
        if raw.lstrip().startswith(FENCE):
            fence = True
            continue
        if not raw.startswith("@"):
            continue                    # văn xuôi (kể cả `\@`, `@` giữa dòng)
        m = re.match(r"@(\S*)(.*)\Z", raw)
        cmd, rest = m.group(1).lower(), m.group(2)
        if cmd not in ("add", "ask", "block"):
            err("E2", ln, f"unknown directive `@{m.group(1)}`")
            continue
        try:
            toks = tokenize(rest)
        except LexError as e:
            err("E2", ln, str(e))
            continue
        kinds = [t.kind for t in toks]
        if cmd == "add":
            if len(toks) == 3 and kinds[0] != "eq" and kinds[2] != "eq" and "comma" not in kinds:
                s, r, o = node_of(toks[0], ln), link_of(toks[1], ln), node_of(toks[2], ln)
                if None not in (s, r, o):
                    g.add_edge(s, o, r)
            elif len(toks) == 5 and kinds[1] == "eq" and "comma" not in kinds:
                p = define(toks[0], ln)
                body = toks[2:]
                if "var" in kinds:
                    if p:  # node suy ra: chỉ lưu, chưa tính
                        g.derived.append({"id": f"{stem}:{p}", "pattern": [t.text for t in body], "line": ln})
                    continue
                s, r, o = node_of(body[0], ln), link_of(body[1], ln), node_of(body[2], ln)
                if None not in (s, r, o) and p:
                    g.add_edge(s, o, r, sid=f"{stem}:{p}")
            else:
                err("E2", ln, f"`@add` needs 3 tokens (s r o) or 5 tokens (p = s r o), got {len(toks)}")
        elif cmd == "ask":
            pats, cur = [], []
            for t in toks + [Tok("comma", ",")]:
                if t.kind == "comma":
                    pats.append(cur)
                    cur = []
                else:
                    cur.append(t)
            if any(len(p) != 3 for p in pats):
                err("E2", ln, "`@ask` needs 3-token patterns joined by `,`")
            elif "bad" in kinds:
                err("E3", ln, "invalid name in `@ask`")
            else:
                res.asks.append((ln, [[t.text for t in p] for p in pats]))
        else:  # block
            if len(toks) != 1:
                err("E2", ln, f"`@block` needs 1 name token, got {len(toks)}")
                continue
            name = define(toks[0], ln)
            fm = re.match(FENCE + r"\s*([A-Za-z0-9._+-]+)\s*\Z", lines[i]) if i < len(lines) else None
            if not fm:
                err("E2", ln, "`@block` must be followed by a ```language code fence on the next line")
                continue
            j = i + 1
            while j < len(lines) and lines[j].strip() != FENCE:
                j += 1
            if j >= len(lines):
                err("E2", ln, "`@block` code fence is not closed")
                break
            content = "\n".join(lines[i + 1:j])
            i = j + 1
            if name:
                nid = g.add_node(f"{stem}:{name}", label=toks[0].text)
                vid = g.add_node(value_id(content), kind="string", value=content)
                g.add_edge(nid, vid, "body")
                blocks.append((nid, fm.group(1).lower(), ln))

    # --- sau một lượt: ngôn ngữ, block, a.b, cảnh báo ---
    declared = {g.nodes[s]["label"].lower() for s, o, k, _ in g.edges
                if k == "is-a" and o == "kg:language" and s.startswith(stem + ":")}
    langs = set(DEFAULT_LANGUAGES) | declared
    for nm in sorted(declared & set(defined)):
        err("E3", defined[nm], f"`{nm}` is a declared language name (reserved)")
    for nid, lang, ln in blocks:
        if lang not in langs:
            err("E2", ln + 1, f"language `{lang}` not declared (add `@add {lang} is-a language`)")
            continue
        lid = f"kg:{lang}" if lang in DEFAULT_LANGUAGES else f"{stem}:{lang}"
        g.add_node(lid, label=lang)
        g.add_edge(nid, lid, "lang")
        if lang in declared:
            uses.setdefault(lang, [0, ln])[0] += 1
    have = {(s, k) for s, o, k, _ in g.edges}
    for a, b, ln in refs:
        if (f"{stem}:{a}", b) not in have:
            err("E5", ln, f"`{a}.{b}`: no edge `{a} {b} …`")
    for nm, (cnt, ln) in uses.items():
        if cnt == 1 and nm not in defined:
            res.diags.append(Diag("W", fname, ln, f"node `{nm}` appears only once (typo?)"))
    res.diags.sort(key=lambda d: (d.line, d.code))
    return res
