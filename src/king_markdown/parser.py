"""king_markdown.parser - parser KING Markdown 0.3 (.kg.md).

    from king_markdown.parser import Parser
    graph = Parser(text, "bai.kg.md").build()     # JSON node-link (networkx)

Ba bước: cắt block (cut_blocks) → ngữ nghĩa (Parser.build) → JSON.
File có `kg: 0.2` (và file style) được đọc bằng parser cũ trong legacy.py.

Cú pháp 0.3 (dev/plan-v2/plan-v2c.md):
    # Tiêu đề [@tên]          section; các dòng "- " ngay dưới là thuộc tính của section
    @node tên                 node (tên viết thường, gạch nối; như tên biến trong file)
    @node Kieu                khai báo node type (viết hoa chữ đầu)
    @link tên                 khai báo link type; trong block: - inverse:, - from A to (B, C)
    - key: value              thuộc tính (các dòng "- " liền ngay dưới dòng mở)
    - link tên: (B, C)        link từ node này
    (dòng trống) văn bản      nội dung (Markdown)
"""
import difflib
import os
import re

from . import legacy
from .legacy import SYSTEM_PREFIX, read, slug, system_file, use_name, apply_style, prose
from .values import DATA_TYPES, ValueError_, as_text, parse_value, split_top, strip_comment

__all__ = ["Parser", "read", "slug", "cut_blocks"]

NAME = r"[a-z0-9][a-z0-9-]*"
TYPE = r"[A-Z][A-Za-z0-9-]*"
REF = rf"{NAME}(?:\.{NAME})?"
RE_HEADING = re.compile(rf"^(#{{1,6}})\s+(.*?)(?:\s+@({NAME}))?\s*$")
RE_OPEN = re.compile(r"^@(node|link)\s+(\S+)\s*$")
RE_OPEN_LOOSE = re.compile(r"^@(node|link)\b(.*)$")
RE_OLD_NODE = re.compile(rf"^@({NAME})\s*:")                 # @id: Tiêu đề (v0.2)
RE_ATTR = re.compile(r"^-\s+(?:link\s+(\S+)|([A-Za-z_][\w-]*))\s*:(?:\s(.*)|)$")
RE_FROM = re.compile(r"^-\s+from\s+(.+?)\s+to\s+(.+)$")
RE_FENCE = re.compile(r"^\s*(```|~~~)")
RE_MENTION = re.compile(rf"(?<![\w@.])@({REF})")

SPECIAL = {"label", "type", "ask", "show", "hide", "inverse", "dag"}    # thuộc tính có nghĩa riêng
HIDE_VIEWS = ("graph", "tree", "book", "module")


def parse_hide(v):
    """- hide: all | graph, module | (graph, module) | true → (danh sách view, tên sai)."""
    if v is True:
        return ["all"], []
    if v in (False, None, ""):
        return [], []
    items = v if isinstance(v, list) else [x.strip() for x in as_text(v).split(",")]
    out, bad = [], []
    for x in (as_text(i).strip().lower() for i in items):
        if x == "all" or x in HIDE_VIEWS:
            if x not in out:
                out.append(x)
        elif x:
            bad.append(x)
    return (["all"] if "all" in out else out), bad
NOT_YET = {"has": "node con (has) chưa hỗ trợ ở 0.3"}
BUILTIN_LINKS = ("contains", "mention")


# ====================== bước 1: cắt block ======================
def frontmatter_end(lines):
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return len(lines)


def kg_version(text):
    lines = text.splitlines()
    for raw in lines[1:frontmatter_end(lines)]:
        m = re.match(r"\s*kg\s*:\s*([\d.]+)", raw)
        if m:
            return m.group(1)
    return None


def _balanced(s):
    """True nếu mọi ( [ " ` trong s đã đóng."""
    depth, q = 0, None
    for c in s:
        if q:
            q = None if c == q else q
        elif c in "\"`":
            q = c
        elif c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
    return depth <= 0 and q is None


def cut_blocks(lines, start, errors):
    """Danh sách block: section / node / link. Mỗi block:
    {kind, name, level, title, attrs: [(key, sub, raw, line)], froms: [(a, b, line)], body, line, end, parent}."""
    blocks, stack = [], []            # stack: [(level, block)]
    cur, phase = None, "attrs"
    fence, pend = False, None         # pend: thuộc tính nhiều dòng đang mở [key, sub, text, line]

    def err(n, msg):
        errors.append({"line": n, "msg": msg})

    def open_block(b):
        nonlocal cur, phase
        if cur is not None:
            cur["end"] = b["line"] - 1
        cur, phase = b, "attrs"
        blocks.append(b)

    def finish_pend():
        nonlocal pend
        if pend:
            cur["attrs"].append(tuple(pend))
            pend = None

    for i in range(start, len(lines)):
        n, raw = i + 1, lines[i]
        if pend:                                         # giá trị [ … ] / ( … ) nhiều dòng
            pend[2] += "\n" + raw
            if _balanced(pend[2]):
                finish_pend()
            continue
        if fence:
            if RE_FENCE.match(raw):
                fence = False
            if cur is not None:
                cur["body"].append(raw)
            continue
        if RE_FENCE.match(raw):
            fence = True
            if cur is not None:
                phase = "body"
                cur["body"].append(raw)
            continue

        m = RE_HEADING.match(raw)
        if m:
            level = len(m.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            if stack and level > stack[-1][0] + 1:
                errors.append({"line": n, "msg": f"heading nhảy cấp (từ {stack[-1][0]} xuống {level})", "warn": True})
            b = {"kind": "section", "name": m.group(3), "title": m.group(2).strip(), "level": level,
                 "attrs": [], "froms": [], "body": [], "line": n,
                 "parent": stack[-1][1] if stack else None}
            open_block(b)
            stack.append((level, b))
            continue

        if raw.startswith("@"):
            text = strip_comment(raw)
            m = RE_OPEN.match(text)
            loose = RE_OPEN_LOOSE.match(text)
            if m or loose:
                kw = (m or loose).group(1)
                if m:
                    name = m.group(2)
                else:
                    rest = loose.group(2).strip()
                    name = re.split(r"[\s:]", rest, maxsplit=1)[0] if rest else ""
                    if not name:
                        err(n, f"@{kw} cần một tên: @{kw} ten-{kw}")
                    elif ":" in rest:
                        err(n, f"dòng mở không có ':' và nhãn; viết @{kw} {name} rồi - label: …")
                    else:
                        err(n, f"dòng mở chỉ gồm @{kw} và tên: {text}")
                b = {"kind": kw, "name": name, "attrs": [], "froms": [], "body": [], "line": n,
                     "parent": stack[-1][1] if stack else None}
                if m is None and ":" in loose.group(2):          # cứu: @node x: Nhãn → label
                    b["attrs"].append(("label", None, loose.group(2).split(":", 1)[1].strip(), n))
                open_block(b)
                continue
            mo = RE_OLD_NODE.match(text)
            if mo:
                err(n, f"cú pháp v0.2 (@{mo.group(1)}: …); 0.3 viết @node {mo.group(1)} và - label: …")
                continue

        if cur is None:
            continue                                      # phần mở đầu trước heading / @ đầu tiên

        if phase == "attrs":
            if not raw.strip():
                phase = "body"
                continue
            line = strip_comment(raw)
            if not line.strip():
                continue                                  # dòng chỉ có comment
            if raw.startswith("- "):
                mf = RE_FROM.match(line) if cur["kind"] == "link" else None
                ma = RE_ATTR.match(line)
                if mf:
                    cur["froms"].append((mf.group(1).strip(), mf.group(2).strip(), n))
                    continue
                if ma:
                    rec = ["link" if ma.group(1) else ma.group(2), ma.group(1), (ma.group(3) or "").strip(), n]
                    if _balanced(rec[2]):
                        cur["attrs"].append(tuple(rec))
                    else:
                        pend = rec
                    continue
                if cur["kind"] != "section":
                    err(n, "thuộc tính phải có dạng - key: value (nội dung thì cách dãy thuộc tính một dòng trống)")
                    continue
            phase = "body"                                # section: văn bản ngay dưới heading là nội dung
        line = strip_comment(raw)
        if raw.strip() and not line.strip():
            continue                                      # dòng chỉ có comment
        cur["body"].append(line)

    if pend:
        err(pend[3], f"thuộc tính {pend[0]}: thiếu ngoặc đóng")
        finish_pend()
    if fence:
        err(len(lines), "khối code ``` chưa đóng")
    if cur is not None:
        cur["end"] = len(lines)
    for b in blocks:                                      # bỏ dòng trống ở đầu và cuối nội dung
        body = b["body"]
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        b["body"] = "\n".join(body)
    return blocks


# ====================== bước 2: ngữ nghĩa ======================
def _names(v):
    """Giá trị đầu mút link → danh sách tên."""
    if isinstance(v, list):
        return [as_text(x) for x in v]
    if isinstance(v, str) and v:
        return [v]
    return []


class Parser:
    def __init__(self, text, filename="<input>", bare=False):
        self.text = text.replace("\r\n", "\n")
        self.lines = self.text.split("\n")
        self.filename = filename
        self.dir = os.path.dirname(os.path.abspath(filename)) if filename != "<input>" else os.getcwd()
        self.bare = bare                          # bare: đọc file schema (không nạp use:)
        self.fm = {"kg": "0.3", "modules": [], "names": {}, "use": []}
        self.use_shown = []
        self.types = {}                           # node type: Ten → {title, line, file?, attrs, content}
        self.ltypes = {}                          # link type: ten → {title, inverse, dag, line, file?}
        self.rules = []
        self.nodes, self.links = {}, []
        self.errors, self.warnings = [], []

    def err(self, line, msg):
        self.errors.append({"line": line, "msg": msg})

    def warn(self, line, msg):
        self.warnings.append({"line": line, "msg": msg})

    # ---------- frontmatter ----------
    def parse_frontmatter(self):
        end = frontmatter_end(self.lines)
        if end == 0:
            return 0
        if end == len(self.lines) and self.lines[-1].strip() != "---":
            self.err(1, "frontmatter không có dòng --- đóng")
        uses, in_use = [], False
        for i in range(1, end - 1):
            raw, n = self.lines[i], i + 1
            line = strip_comment(raw)
            if not line.strip():
                continue
            if in_use and line.lstrip().startswith("- "):
                item = line.strip()[2:].strip()
                key, _, names = item.partition(":")
                uses.append((key.strip(), [x for x in split_top(names) if x] if names.strip() else None, n))
                continue
            in_use = False
            if ":" not in line:
                self.err(n, f"frontmatter không hiểu: {line.strip()}")
                continue
            key, value = (s.strip() for s in line.split(":", 1))
            if key == "kg":
                self.fm["kg"] = value
            elif key == "use":
                if value:
                    uses += [(x, None, n) for x in split_top(value) if x]
                else:
                    in_use = True
            elif key == "import":                      # import: mod, mod2.ten (một node lẻ)
                for item in split_top(value):
                    if "." in item:
                        mod, short = item.split(".", 1)
                        self.fm["names"][short] = mod
                    elif item:
                        self.fm["modules"].append(item)
            else:
                self.warn(n, f"khóa frontmatter lạ: {key}")
        if not self.bare:
            for key, names, n in uses:
                self.load_use(key, names, n)
        return end

    def load_use(self, key, names, n):
        m = re.fullmatch(r"(.+?)(?:\.(node|link))?", key)
        fname, part = m.group(1), m.group(2)
        if fname.startswith(SYSTEM_PREFIX):
            path = system_file(fname[len(SYSTEM_PREFIX):])
        else:
            path = os.path.join(self.dir, use_name(fname))
        if not path or not os.path.exists(path):
            self.err(n, f"use: không tìm thấy {use_name(fname)}"
                     + (" trong schema / style của hệ thống" if fname.startswith(SYSTEM_PREFIX) else ""))
            return
        self.fm["use"].append(key)
        shown = (SYSTEM_PREFIX if fname.startswith(SYSTEM_PREFIX) else "") + os.path.basename(path)
        if shown not in self.use_shown:
            self.use_shown.append(shown)
        tag = os.path.basename(path)
        text = read(path)
        ver = kg_version(text) or "0.3"
        if ver.startswith("0.2") or ver.startswith("0.1"):
            # file v0.2 (style; schema cũ): luật style giữ định dạng cũ
            schema, rules, e, w = legacy.load_uses([path])
            self.rules += rules
            self.errors += e
            self.warnings += w
            for t, s in schema["types"].items():
                self.types.setdefault(t[:1].upper() + t[1:], {"title": s["title"], "file": tag, "line": s["line"]})
            for t, s in schema["links"].items():
                self.ltypes.setdefault(t, {"title": s["title"], "dag": s["dag"], "inverse": None,
                                           "file": tag, "line": s["line"]})
            return
        sub = Parser(text, path, bare=True)
        sub.build()
        self.errors += [{**e, "file": tag} for e in sub.errors]
        self.warnings += [{**w, "file": tag} for w in sub.warnings]
        for kind, table, mine in (("node", sub.types, self.types), ("link", sub.ltypes, self.ltypes)):
            if part and part != kind:
                continue
            want = names if (names is not None and part == kind) else list(table)
            for t in want:
                if t not in table:
                    self.err(n, f"{tag} không có {'node type' if kind == 'node' else 'link type'} {t}")
                    continue
                mine[t] = {**table[t], "file": tag}

    # ---------- khai báo ----------
    def declare(self, b):
        """@node Kieu (node type) hoặc @link ten (link type)."""
        attrs = self.read_attrs(b, allow_link=False)
        if b["kind"] == "node":
            self.types[b["name"]] = {"title": as_text(attrs.pop("label", b["name"])), "line": b["line"],
                                     "attrs": attrs, "content": b["body"]}
            if b["froms"]:
                self.err(b["froms"][0][2], "- from … to … chỉ dùng trong @link")
            return
        inv = attrs.pop("inverse", None)
        if inv is not None and not (isinstance(inv, str) and re.fullmatch(NAME, inv)):
            self.err(b["line"], f"inverse cần một tên link viết thường: {as_text(inv)}")
            inv = None
        dag = attrs.pop("dag", False)
        self.ltypes[b["name"]] = {"title": as_text(attrs.pop("label", b["name"])), "line": b["line"],
                                  "inverse": inv, "dag": dag is True, "hide": self.read_hide(attrs, b["line"]),
                                  "attrs": attrs, "content": b["body"]}

    def read_attrs(self, b, allow_link=True, links=None):
        out = {}
        for key, sub, raw, line in b["attrs"]:
            if key == "link":
                if not allow_link:
                    self.err(line, "- link …: chỉ dùng trong node")
                elif links is not None:
                    links.append((sub, raw, line))
                continue
            if key in out:
                self.err(line, f"thuộc tính {key} viết hai lần")
                continue
            if key in NOT_YET:
                self.warn(line, NOT_YET[key])
            if not re.fullmatch(NAME, key):
                self.err(line, f"tên thuộc tính viết thường, gạch nối: {key}")
            try:
                v = raw if key == "label" and not raw.startswith('"') else parse_value(raw)
            except ValueError_ as e:
                self.err(line, f"{key}: {e}")
                v = raw
            out[key] = v
            self._seen_keys.setdefault(key, []).append(line)
        return out

    # ---------- build ----------
    def build(self):
        ver = kg_version(self.text)
        if ver and (ver.startswith("0.2") or ver.startswith("0.1")):
            g = legacy.Parser(self.text, self.filename, bare=self.bare).build()
            if not self.bare and "select=" not in self.text:      # file style: định dạng v0.2 là đúng (đóng băng)
                g["graph"]["warnings"].insert(0, {"line": 1, "msg": f"file kg: {ver} (cú pháp cũ); hãy chuyển sang 0.3"})
            self._legacy = g
            return g
        self._seen_keys = {}
        start = self.parse_frontmatter()
        cut_err = []
        blocks = cut_blocks(self.lines, start, cut_err)
        for e in cut_err:
            (self.warnings if e.pop("warn", False) else self.errors).append(e)

        # khai báo trước (type / link type dùng được ở mọi chỗ trong file)
        for b in blocks:
            if b["kind"] == "link" or (b["kind"] == "node" and re.fullmatch(TYPE, b["name"] or "")):
                if b["kind"] == "link" and not re.fullmatch(NAME, b["name"]):
                    self.err(b["line"], f"tên link viết thường, gạch nối: {b['name']}")
                    continue
                if b["kind"] == "node" and b["name"] in DATA_TYPES:
                    self.err(b["line"], f"{b['name']} là kiểu dữ liệu dựng sẵn, không khai báo lại")
                    continue
                table = self.ltypes if b["kind"] == "link" else self.types
                if b["name"] in table and "file" not in table[b["name"]]:
                    self.err(b["line"], f"khai báo trùng: {b['name']} (dòng {table[b['name']]['line']})")
                    continue
                self.declare(b)
                b["decl"] = True

        raw_links, raw_froms = [], []
        # tên section tự sinh (không có @tên) không được chiếm tên node / section viết rõ
        self._taken = {b["name"] for b in blocks if b["name"] and not b.get("decl")}
        for b in blocks:
            if b.get("decl"):
                if b["kind"] == "link":
                    raw_froms += [(b["name"], a, c, line) for a, c, line in b["froms"]]
                continue
            if b["kind"] == "section":
                auto = b["name"] is None
                name = b["name"] or self._unique(slug(b["title"]))
                b["name"] = name
                attrs = self.read_attrs(b, allow_link=False)
                self.add_node(name, b, kind="section", title=b["title"], level=b["level"],
                              auto_id=auto, attrs=attrs)
                continue
            if b["kind"] == "node":
                name = b["name"]
                if not name:
                    continue
                if not re.fullmatch(NAME, name):
                    self.err(b["line"], f"tên node viết thường, gạch nối (kiểu viết hoa chữ đầu): {name}")
                    continue
                links = []
                attrs = self.read_attrs(b, links=links)
                label = attrs.pop("label", None)
                typ = attrs.pop("type", None)
                if typ is not None:
                    typ = as_text(typ)
                    if not re.fullmatch(TYPE, typ):
                        hint = typ[:1].upper() + typ[1:]
                        self.err(b["line"], f"tên kiểu viết hoa chữ đầu: {typ} → {hint}")
                        typ = hint if hint in self.types else None
                    elif typ not in self.types:
                        self.err(b["line"], f"node type chưa import / khai báo: {typ}")
                if b["froms"]:
                    self.err(b["froms"][0][2], "- from … to … chỉ dùng trong @link")
                self.add_node(name, b, kind="node", label=as_text(label) if label is not None else "",
                              type=typ, attrs=attrs)
                raw_links += [(name, sub, raw, line) for sub, raw, line in links]

        self.make_links(raw_links, raw_froms)
        self.check_typos()
        self.check_cycles()
        return self.to_json()

    def _unique(self, base):
        name, k = base, 2
        while name in self.nodes or name in self._taken:
            name, k = f"{base}-{k}", k + 1
        return name

    def add_node(self, name, b, kind, attrs, label="", type=None, title=None, level=None, auto_id=False):
        if name in self.nodes:
            self.err(b["line"], f"tên trùng: {name} (đã khai báo ở dòng {self.nodes[name]['line']})")
            return
        parent = b["parent"]["name"] if b.get("parent") else None
        node = {"id": name, "kind": kind, "type": type, "label": label,
                "title": title if title is not None else (label or name),
                "attrs": attrs, "content": b["body"], "parent": parent, "level": level,
                "line": b["line"], "end": b.get("end"), "auto_id": auto_id, "external": False,
                "ask": as_text(attrs["ask"]) if "ask" in attrs else "",
                "show": as_text(attrs["show"]) if "show" in attrs else None,
                "hide": self.read_hide(attrs, b["line"])}
        self.nodes[name] = node

    def read_hide(self, attrs, line):
        """- hide: … → danh sách view bị ẩn (None nếu không ẩn). Con cháu được view tự ẩn theo."""
        hide, bad = parse_hide(attrs.get("hide"))
        if bad:
            self.warn(line, f"hide: không có view {', '.join(bad)} (dùng all, {', '.join(HIDE_VIEWS)})")
        return hide or None

    # ---------- link ----------
    def resolve(self, ref, line):
        if ref in self.nodes:
            return ref
        if "." not in ref and ref in self.fm["names"]:
            ref = f"{self.fm['names'][ref]}.{ref}"
        if "." in ref:
            mod, short = ref.split(".", 1)
            if mod in self.fm["modules"] or self.fm["names"].get(short) == mod:
                if ref not in self.nodes:
                    self.nodes[ref] = {"id": ref, "kind": "external", "title": short, "label": short,
                                       "module": mod, "external": True, "line": line, "parent": None,
                                       "attrs": {}, "content": "", "ask": "", "show": None,
                                       "level": None, "auto_id": False, "type": None}
                return ref
            self.err(line, f"module chưa import: {mod} (trong {ref})")
            return None
        self.err(line, f"không tìm thấy node: {ref}")
        return None

    def add_link(self, src, typ, dst, line, declared_at, rev=False):
        key = (src, typ, dst)
        if key in self.seen:
            l = self.seen[key]
            if line not in l.setdefault("lines", [l["line"]]):
                l["lines"].append(line)                   # link trùng: gộp
            return
        l = {"source": src, "target": dst, "type": typ, "line": line,
             "declared_at": declared_at, "reversed": rev}
        hide = (self.ltypes.get(typ) or {}).get("hide")
        if hide:
            l["hide"] = hide                              # - hide: … của @link: ẩn mọi link loại này
        self.seen[key] = l
        self.links.append(l)

    def make_links(self, raw_links, raw_froms):
        self.seen = {}
        inverse = {s["inverse"]: t for t, s in self.ltypes.items() if s.get("inverse")}
        for name, sub, raw, line in raw_links:
            if not sub or not re.fullmatch(NAME, sub):
                self.err(line, f"tên link viết thường, gạch nối: - link {sub or '?'}: …")
                continue
            try:
                targets = _names(parse_value(raw))
            except ValueError_ as e:
                self.err(line, f"link {sub}: {e}")
                continue
            if not targets:
                self.err(line, f"link {sub}: cần đích, ví dụ - link {sub}: (a, b)")
            if sub in BUILTIN_LINKS:
                self.err(line, f"loại link {sub} do parser tự sinh, không viết tay")
                continue
            if sub in self.ltypes:
                typ, rev = sub, False
            elif sub in inverse:
                typ, rev = inverse[sub], True
            else:
                self.err(line, f"link type chưa import / khai báo: {sub}")
                continue
            for t in targets:
                tgt = self.resolve(t, line)
                if tgt:
                    self.add_link(tgt, typ, name, line, name, True) if rev else self.add_link(name, typ, tgt, line, name)
        for typ, a, c, line in raw_froms:
            try:
                srcs, dsts = _names(parse_value(a)), _names(parse_value(c))
            except ValueError_ as e:
                self.err(line, f"{typ}: {e}")
                continue
            for s in srcs:
                for d in dsts:
                    rs, rd = self.resolve(s, line), self.resolve(d, line)
                    if rs and rd:
                        self.add_link(rs, typ, rd, line, None)
        for node in list(self.nodes.values()):            # @tên trong nội dung
            for fld in ("content", "ask"):
                for m in RE_MENTION.finditer(prose(node.get(fld) or "")):
                    ref = m.group(1)
                    if ref in ("node", "link"):
                        continue
                    tgt = self.resolve(ref, node["line"])
                    if tgt and tgt != node["id"]:
                        self.add_link(node["id"], "mention", tgt, node["line"], node["id"])
        for node in self.nodes.values():                  # cạnh cây chứa
            if node.get("parent"):
                self.links.append({"source": node["parent"], "target": node["id"],
                                   "type": "contains", "tree": True})

    # ---------- kiểm lỗi ----------
    def check_typos(self):
        """Thuộc tính chỉ dùng đúng một lần và rất giống một thuộc tính khác: có thể gõ nhầm."""
        keys = self._seen_keys
        for k, lines in keys.items():
            if len(lines) != 1 or k in SPECIAL:
                continue
            others = [o for o in keys if o != k and (len(keys[o]) > 1 or o in SPECIAL)]
            near = difflib.get_close_matches(k, others, n=1, cutoff=0.75)
            if near:
                self.warn(lines[0], f"thuộc tính {k} chỉ dùng một lần; có phải {near[0]}?")

    def dag_types(self):
        return [t for t, s in self.ltypes.items() if s.get("dag")]

    def check_cycles(self):
        for typ in self.dag_types():
            adj = {}
            for l in self.links:
                if l["type"] == typ:
                    adj.setdefault(l["source"], []).append(l["target"])
            color, path = {}, []

            def dfs(u):
                color[u] = 1
                path.append(u)
                for v in adj.get(u, []):
                    if color.get(v) == 1:
                        cyc = path[path.index(v):] + [v]
                        self.err(self.nodes[u]["line"], f"vòng lặp {typ}: {' → '.join(cyc)}")
                    elif not color.get(v):
                        dfs(v)
                path.pop()
                color[u] = 2

            for u in list(adj):
                if not color.get(u):
                    dfs(u)

    # ---------- JSON ----------
    def to_json(self):
        links = [{**l, "key": f"{l['type']}:{i}"} for i, l in enumerate(self.links)]
        full = []
        for nd in self.nodes.values():
            d = dict(nd)
            d["meta"] = ({"type": d["type"]} if d.get("type") else {}) | {
                k: as_text(v) if isinstance(v, (list, dict)) or v is None else v for k, v in d["attrs"].items()}
            full.append(d)
        apply_style(self.rules, full, links)
        nodes = [{k: v for k, v in nd.items() if v not in (None, "", {}) or k in ("id", "parent")} for nd in full]
        schema = {"types": {t: {k: v for k, v in s.items() if k in ("title", "line", "file")}
                            for t, s in self.types.items()},
                  "keys": {},
                  "links": {t: {k: v for k, v in s.items() if k in ("title", "line", "file", "inverse", "dag", "hide") and v is not None}
                            for t, s in self.ltypes.items()}}
        return {
            "directed": True,
            "multigraph": True,
            "graph": {
                "file": os.path.basename(self.filename),
                "kg": self.fm["kg"],
                "use": self.use_shown,
                "fields": [],
                "schema": schema,
                "dag": self.dag_types(),
                "import_modules": self.fm["modules"],
                "import_names": self.fm["names"],
                "errors": self.errors,
                "warnings": self.warnings,
            },
            "nodes": nodes,
            "links": links,
        }
