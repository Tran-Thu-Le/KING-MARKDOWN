"""king_markdown.parser - parser cho ngôn ngữ KING Markdown (.kg.md, v0.2).

    from king_markdown.parser import Parser
    graph = Parser(text, "bai.kg.md").build()     # JSON node-link (networkx)

Frontmatter `use: schema, style` nạp schema.kg.md (kiểm lỗi) và style.kg.md (định dạng).
Dòng lệnh: king parse | king html | king serve (xem cli.py).
"""
import os
import re
import unicodedata

ID = r"[a-z0-9][a-z0-9-]*"
REF = rf"{ID}(?:\.{ID})?"                      # id hoặc module.id
RE_HEADING = re.compile(rf"^(#{{1,6}})\s+(.*?)(?:\s+@({ID}))?\s*$")
RE_NODE = re.compile(rf"^@({ID})\s*(?::\s*(.*))?$")
RE_FIELD = re.compile(r"^\s*[-*]\s+([a-z][a-z0-9-]*)\s*:\s*(.*)$")
RE_LINK = re.compile(rf"([a-z][a-z0-9-]*)(!?)\(\s*([^)]*?)\s*\)")
RE_MENTION = re.compile(rf"(?<![\w@.])@({REF})")
RE_FENCE = re.compile(r"^\s*(```|~~~)")

FIELDS = ["content", "meta", "link", "show", "ask"]   # cố định trong ngôn ngữ
BUILTIN_LINKS = ("contains", "mention", "contain")    # parser tự sinh
BUILTIN_KEYS = ("type", "contain")                    # khóa meta luôn được phép, không cần khai báo
DEFAULT_DAG = ["needs", "part-of"]                    # khi schema không khai báo link
HTML_NODE = {"shape", "color", "border", "border-color", "dash", "font", "font-size",
             "font-color", "size", "opacity", "radius"}       # radius: độ bo góc của box (0 = góc vuông)
HTML_LINK = {"color", "width", "dash", "arrows", "opacity"}
VALUE_TYPES = ("bool", "int", "number", "text")


# ====================== tiện ích ======================
def slug(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "node"


def strip_comment(line):
    line = re.sub(r"%%.*?%%", "", line)
    m = re.search(r"(^|\s)//", line)          # chỉ nhận // có khoảng trắng phía trước
    return (line[: m.start()] if m else line).rstrip()


RE_CODE_BLOCK = re.compile(r"^\s*(```|~~~).*?^\s*\1[^\n]*$", re.S | re.M)
RE_CODE_SPAN = re.compile(r"`[^`\n]*`")


def prose(text):
    """Bỏ khối ``` và `code` khỏi văn bản: @id trong ví dụ code không phải tham chiếu."""
    return RE_CODE_SPAN.sub("", RE_CODE_BLOCK.sub("", text))


def bracket_lines(lines, start=0):
    """Chỉ số các dòng nằm trong nội dung '[ ... ]' nhiều dòng của content / ask (không gồm dòng mở).
    Các dòng này là nội dung thuần: không phải node, heading hay trường."""
    out, inside, fence = set(), False, False
    for i in range(start, len(lines)):
        raw = lines[i]
        if inside:
            out.add(i)
            inside = not raw.strip().endswith("]")
            continue
        if RE_FENCE.match(raw):
            fence = not fence
            continue
        m = None if fence else RE_FIELD.match(strip_comment(raw))
        if m and m.group(1) in ("content", "ask"):
            v = m.group(2).strip()
            inside = v.startswith("[") and "]" not in v
    return out


def split_list(value):
    return [x.strip() for x in value.split(",") if x.strip()]


def split_top(value):
    """Tách theo dấu phẩy, bỏ qua dấu phẩy nằm trong "..." (ví dụ allow="role, important")."""
    out, buf, q = [], "", None
    for c in value:
        if q:
            buf += c
            q = None if c == q else q
        elif c in "\"'" and (not buf.strip() or buf.rstrip().endswith("=")):
            buf += c
            q = c
        elif c == ",":
            out.append(buf)
            buf = ""
        else:
            buf += c
    out.append(buf)
    return [x.strip() for x in out if x.strip()]


def parse_value(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def as_text(v):
    return ("true" if v else "false") if isinstance(v, bool) else str(v)


def parse_meta(value):
    out = {}
    for part in split_top(value):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = parse_value(v)
        else:
            out[part] = True
    return out


def format_value(v):
    if isinstance(v, bool):
        return as_text(v)
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if re.fullmatch(r"[\w.-]+", s) and parse_value(s) == s:
        return s
    return '"' + s.replace('"', "'") + '"'


def format_meta(meta):
    return ", ".join(f"{k}={format_value(v)}" for k, v in meta.items())


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def use_name(name):
    return name if name.endswith(".md") else name + ".kg.md"


SYSTEM_PREFIX = "king/"           # use: king/schema, king/style → schema / style của hệ thống (templates/)
PKG = os.path.dirname(os.path.abspath(__file__))


def system_file(name):
    """Đường dẫn file hệ thống (bộ mẫu đi kèm KING Markdown): templates/ trong gói, hoặc ở gốc repo."""
    for folder in (os.path.join(PKG, "templates"), os.path.join(PKG, "..", "..", "templates")):
        path = os.path.join(folder, use_name(name))
        if os.path.exists(path):
            return os.path.abspath(path)
    return None


def use_path(folder, name):
    """Tên trong use: → đường dẫn. 'king/x' là file hệ thống, còn lại tìm cạnh file đang đọc."""
    if name.startswith(SYSTEM_PREFIX):
        return system_file(name[len(SYSTEM_PREFIX):])
    return os.path.join(folder, use_name(name))


# ====================== schema + style (từ các file use:) ======================
def parse_select(s):
    """'' / '*' | '#id' | 'link' / 'link=needs' | 'k=v k2=v2 k3' (k=kind so với loại node)."""
    s = as_text(s).strip()
    if s in ("", "*"):
        return {"target": "node", "conds": [], "id": None, "rank": 0}
    if s.startswith("#"):
        return {"target": "node", "conds": [], "id": s[1:], "rank": 100}
    if s == "link" or s.startswith("link="):
        t = s[5:] or None
        return {"target": "link", "type": None if t in (None, "*") else t, "rank": 10 if t else 0}
    conds = []
    for part in s.split():
        k, eq, v = part.partition("=")
        conds.append((k, v if eq else None))
    return {"target": "node", "conds": conds, "id": None,
            "rank": sum(1 if k == "kind" else 10 for k, _ in conds)}


def def_role(n):
    """Node định nghĩa: 'schema' (meta kind=type|key|link), 'style' (meta select), hoặc None (node dữ liệu)."""
    if n["kind"] != "node":
        return None
    m = n["meta"]
    if m.get("kind") in ("type", "key", "link"):
        return "schema"
    return "style" if "select" in m else None


def collect_defs(nodes, tag, schema, rules, warnings):
    """Đưa các node định nghĩa vào schema / rules. tag: tên file (None = chính file đang parse)."""
    for n in nodes:
        if n["kind"] != "node":
            continue
        m, kind = n["meta"], n["meta"].get("kind")
        where = {"file": tag, "line": n["line"]} if tag else {"line": n["line"]}
        if kind == "type":
            schema["types"][n["id"]] = {
                "title": n["title"], **where,
                "allow": split_top(as_text(m["allow"])) if "allow" in m else None}
        elif kind == "key":
            vt = m.get("value")
            if vt is not None and vt not in VALUE_TYPES:
                warnings.append({**where, "msg": f"value={vt} lạ (dùng {', '.join(VALUE_TYPES)})"})
            schema["keys"][n["id"]] = {
                "title": n["title"], **where, "value": vt,
                "values": [x.strip() for x in as_text(m["values"]).split("|")] if "values" in m else None,
                "required": m.get("required") is True}
        elif kind == "link":
            schema["links"][n["id"]] = {
                "title": n["title"], **where, "dag": m.get("dag") is True,
                "from": m.get("from"), "to": m.get("to")}
        elif "select" in m:
            r = parse_select(m["select"])
            allowed = HTML_LINK if r["target"] == "link" else HTML_NODE
            html = {k[5:]: v for k, v in m.items() if k.startswith("html.")}
            for k in html:
                if k not in allowed:
                    warnings.append({**where, "msg": f"html.{k} không hỗ trợ cho {r['target']}"})
            rules.append({**r, **where, "rule": n["id"], "order": len(rules),
                          "html": {k: v for k, v in html.items() if k in allowed},
                          "typst": {k[6:]: v for k, v in m.items() if k.startswith("typst.")}})
        elif kind is not None:
            warnings.append({**where, "msg": f"kind={kind} lạ (dùng type, key, link)"})


def load_uses(paths):
    """Đọc các file use: → (schema, rules, errors, warnings).
    Node có meta kind=type|key|link là schema; node có meta select là luật style."""
    schema = {"types": {}, "keys": {}, "links": {}}
    rules, errors, warnings = [], [], []
    for path in paths:
        p = Parser(read(path), path, bare=True)
        p.build()
        tag = os.path.basename(path)
        errors += [{**e, "file": tag} for e in p.errors]
        warnings += [{**w, "file": tag} for w in p.warnings]
        collect_defs(p.nodes.values(), tag, schema, rules, warnings)
    return schema, rules, errors, warnings


def node_matches(rule, n):
    if rule["id"] is not None:
        return n["id"] == rule["id"]
    for k, v in rule["conds"]:
        have = n["kind"] if k == "kind" else n["meta"].get(k, n.get(k))
        if v is None:
            if have in (None, "", False):
                return False
        elif have is None or as_text(have) != v.strip("\"'"):
            return False
    return True


def apply_style(rules, nodes, links):
    ordered = sorted(rules, key=lambda r: (r["rank"], r["order"]))

    def pack(items):
        st = {"html": {}, "typst": {}}
        for r in items:
            st["html"].update(r["html"])
            st["typst"].update(r["typst"])
        return {k: v for k, v in st.items() if v}

    for n in nodes:
        st = pack(r for r in ordered if r["target"] == "node" and node_matches(r, n))
        if st:
            n["style"] = st
    for l in links:
        st = pack(r for r in ordered if r["target"] == "link" and r["type"] in (None, l["type"]))
        if st:
            l["style"] = st


# ====================== parser ======================
class Parser:
    def __init__(self, text, filename="<input>", bare=False):
        self.lines = text.splitlines()
        self.filename = filename
        self.dir = os.path.dirname(os.path.abspath(filename)) if filename != "<input>" else os.getcwd()
        self.bare = bare                       # bare = không nạp use: (dùng khi đọc chính schema/style)
        self.fm = {"kg": "0.2", "modules": [], "names": {}, "use": []}
        self.use_files = []
        self.use_shown = []                    # tên hiện trong JSON: "style.kg.md" hoặc "king/style.kg.md"
        self.schema = {"types": {}, "keys": {}, "links": {}}
        self.rules = []
        self.nodes, self.links = {}, []
        self.errors, self.warnings = [], []

    def err(self, line, msg):
        self.errors.append({"line": line, "msg": msg})

    def warn(self, line, msg):
        self.warnings.append({"line": line, "msg": msg})

    # ---------- frontmatter ----------
    def parse_frontmatter(self):
        if not self.lines or self.lines[0].strip() != "---":
            return 0
        for i in range(1, len(self.lines)):
            raw = self.lines[i]
            if raw.strip() == "---":
                self._load_uses()
                return i + 1
            line = strip_comment(raw).strip()
            if not line:
                continue
            if ":" not in line:
                self.err(i + 1, f"frontmatter không hiểu: {line}")
                continue
            key, value = (s.strip() for s in line.split(":", 1))
            if key == "kg":
                self.fm["kg"] = value
            elif key == "use":
                for name in split_list(value):
                    self.fm["use"].append(name)
                    path = use_path(self.dir, name)
                    if path and os.path.exists(path):
                        self.use_files.append(path)
                        self.use_shown.append((SYSTEM_PREFIX if name.startswith(SYSTEM_PREFIX) else "") + os.path.basename(path))
                    else:
                        self.err(i + 1, f"use: không tìm thấy {use_name(name)}"
                                 + (" trong schema / style của hệ thống" if name.startswith(SYSTEM_PREFIX) else ""))
            elif key == "import":
                for item in split_list(value):
                    if "." in item:
                        mod, name = item.split(".", 1)
                        self.fm["names"][name] = mod
                    else:
                        self.fm["modules"].append(item)
            elif key.startswith("from "):
                mod = key[5:].strip()
                for name in split_list(value):
                    self.fm["names"][name] = mod
            elif key in ("meta", "link", "node"):
                self.warn(i + 1, f"'{key}:' ở frontmatter không còn dùng (v0.2); khai báo trong schema, nạp bằng use:")
            else:
                self.warn(i + 1, f"khóa frontmatter lạ: {key}")
        self.err(1, "frontmatter không có dòng --- đóng")
        return len(self.lines)

    def _load_uses(self):
        if self.bare or not self.use_files:
            return
        self.schema, self.rules, e, w = load_uses(self.use_files)
        self.errors += e
        self.warnings += w

    # ---------- body ----------
    def add_node(self, nid, line, **kw):
        if nid in self.nodes:
            self.err(line, f"ID trùng: {nid} (đã khai báo ở dòng {self.nodes[nid]['line']})")
            return None
        node = {"id": nid, "line": line, "meta": {}, "content": "", "ask": "",
                "show": None, "external": False, **kw}
        self.nodes[nid] = node
        return node

    def parse_body(self, start):
        stack = []            # [(level, section_id)]
        cur = None            # node @ đang mở
        field = None          # trường đang được nối dòng
        in_fence = False
        raw_links = []        # (node_id, type, reversed, args, line)

        bracket = None        # content / ask dạng [ ... ] nhiều dòng: mọi dòng tới ']' cuối là nội dung
        for i in range(start, len(self.lines)):
            n, raw = i + 1, self.lines[i]
            if bracket:
                t = raw.strip()
                if t.endswith("]"):
                    if t[:-1].rstrip():
                        self._append(cur, bracket, t[:-1].rstrip())
                    bracket, field = None, None
                elif t:
                    self._append(cur, bracket, t)
                elif cur.get(bracket):
                    cur[bracket] += "\n"
                continue
            text_field = field if field in ("content", "ask") else "content"
            if RE_FENCE.match(raw):
                in_fence = not in_fence
                if cur:
                    self._append(cur, text_field, raw)
                continue
            if in_fence:
                if cur:
                    if raw.strip():
                        self._append(cur, text_field, raw)
                    elif cur.get(text_field):
                        cur[text_field] += "\n"          # dòng trống trong khối code
                continue
            line = strip_comment(raw)
            if not line.strip():
                if cur is not None and field in ("content", "ask") and cur.get(field):
                    cur[field] += "\n"                   # giữ dòng trống: tách đoạn văn
                field = None if field in ("link", "meta", "show") else field
                continue

            m = RE_HEADING.match(line)
            if m:
                level, title, explicit = len(m.group(1)), m.group(2).strip(), m.group(3)
                while stack and stack[-1][0] >= level:
                    stack.pop()
                if stack and level > stack[-1][0] + 1:
                    self.warn(n, f"heading nhảy cấp (từ {stack[-1][0]} xuống {level})")
                sid = explicit or self._unique(slug(title))
                parent = stack[-1][1] if stack else None
                self.add_node(sid, n, title=title, kind="section", level=level,
                              parent=parent, auto_id=explicit is None)
                stack.append((level, sid))
                cur, field = None, None
                continue

            m = RE_NODE.match(line.strip())
            if m:
                nid, title = m.group(1), (m.group(2) or "").strip()
                parent = stack[-1][1] if stack else None
                cur = self.add_node(nid, n, title=title or nid, kind="node",
                                    level=None, parent=parent, auto_id=False)
                field = None
                continue

            m = RE_FIELD.match(line)
            if m and cur is not None:
                key, value = m.group(1), m.group(2).strip()
                if key not in FIELDS:
                    hint = f" (là khóa meta: - meta: {key}={value})" if key in BUILTIN_KEYS else ""
                    self.err(n, f"trường lạ: {key} (chỉ có {', '.join(FIELDS)}){hint}")
                    continue
                field = key
                if key == "meta":
                    cur["meta"].update(parse_meta(value))
                    cur.setdefault("meta_line", n)
                elif key == "link":
                    self._collect_links(cur["id"], value, n, raw_links)
                elif key == "show":
                    cur["show"] = parse_value(value)
                elif value.startswith("[") and "]" not in value:     # - content: [ nội dung dài nhiều dòng ... ]
                    bracket = key
                    if value[1:].strip():
                        self._append(cur, key, value[1:].strip())
                elif re.fullmatch(r"\[[^\]]*\]", value):           # - content: [một dòng]
                    self._append(cur, key, value[1:-1].strip())
                else:
                    self._append(cur, key, value)
                continue

            if cur is None:
                continue                                  # văn bản thường của section
            if field == "link":
                self._collect_links(cur["id"], line, n, raw_links)
            else:
                self._append(cur, field if field in ("content", "ask") else "content",
                             line.strip())
        return raw_links

    def _unique(self, base):
        sid, k = base, 2
        while sid in self.nodes:
            sid, k = f"{base}-{k}", k + 1
        return sid

    @staticmethod
    def _append(node, key, text):
        if key not in node or not isinstance(node.get(key), str):
            node[key] = ""
        node[key] = (node[key] + "\n" + text).strip("\n") if node[key] else text

    def _collect_links(self, nid, value, line, out):
        rest = RE_LINK.sub("", value).replace(",", "").strip()
        if rest:
            self.err(line, f"link không đúng cú pháp: {rest}")
        for m in RE_LINK.finditer(value):
            out.append((nid, m.group(1), m.group(2) == "!", split_list(m.group(3)), line))

    # ---------- schema ----------
    def check_meta(self, node):
        S = self.schema
        if not (S["keys"] or S["types"]):
            return
        meta, line = node["meta"], node.get("meta_line", node["line"])
        t = as_text(meta["type"]) if "type" in meta else None
        if t is not None and S["types"] and t not in S["types"]:
            self.err(line, f"kiểu node không khai báo trong schema: {t}")
        allow = S["types"].get(t, {}).get("allow") if t else None
        for k, v in meta.items():
            if k in BUILTIN_KEYS:
                continue
            spec = S["keys"].get(k)
            if spec is None:
                self.err(line, f"khóa meta không khai báo trong schema: {k}")
                continue
            if allow is not None and k not in allow:
                self.err(line, f"khóa {k} không dùng cho kiểu {t}")
            if spec["values"] and as_text(v) not in spec["values"]:
                self.err(line, f"{k}={as_text(v)} không thuộc {' | '.join(spec['values'])}")
            vt = spec["value"]
            ok = {"bool": isinstance(v, bool),
                  "int": isinstance(v, int) and not isinstance(v, bool),
                  "number": isinstance(v, (int, float)) and not isinstance(v, bool)}.get(vt, True)
            if not ok:
                self.err(line, f"{k}={as_text(v)} phải là {vt}")
        for k in allow or []:
            if S["keys"].get(k, {}).get("required") and k not in meta:
                self.err(line, f"thiếu khóa bắt buộc {k} (kiểu {t})")

    def check_link_ends(self, typ, src, dst, line):
        spec = self.schema["links"].get(typ) or {}
        for end, nid in (("from", src), ("to", dst)):
            want = spec.get(end)
            n = self.nodes[nid]
            if want and n["kind"] != "external" and as_text(n["meta"].get("type", "")) != as_text(want):
                self.err(line, f"{typ}: {'nguồn' if end == 'from' else 'đích'} {nid} phải có type={want}")

    # ---------- resolve ----------
    def resolve(self, ref, line):
        if ref in self.nodes:
            return ref
        if "." in ref:
            mod = ref.split(".", 1)[0]
            if mod in self.fm["modules"]:
                return self._external(ref, line)
            self.err(line, f"module chưa import: {mod} (trong {ref})")
            return None
        if ref in self.fm["names"]:
            return self._external(f"{self.fm['names'][ref]}.{ref}", line)
        self.err(line, f"không tìm thấy node: {ref}")
        return None

    def _external(self, full, line):
        if full not in self.nodes:
            mod, name = full.split(".", 1)
            self.nodes[full] = {"id": full, "title": name, "kind": "external",
                                "module": mod, "external": True, "line": line,
                                "parent": None, "meta": {}, "content": "", "ask": "",
                                "show": None, "level": None, "auto_id": False}
        return full

    def nearest_explicit(self, nid):
        p = self.nodes[nid]["parent"]
        while p and self.nodes[p].get("auto_id"):
            p = self.nodes[p]["parent"]
        return p or self.nodes[nid]["parent"]

    def build(self):
        start = self.parse_frontmatter()
        raw_links = self.parse_body(start)
        for n in self.nodes.values():                   # bỏ dòng trống thừa ở cuối content / ask
            for f in ("content", "ask"):
                if isinstance(n.get(f), str):
                    n[f] = n[f].strip("\n")
        # schema / style viết ngay trong file này: áp cho chính file (sau các file use:, nên luật ở đây thắng khi cùng mức)
        for n in self.nodes.values():
            role = def_role(n)
            if role:
                n["def"] = role
        me = os.path.abspath(self.filename) if self.filename != "<input>" else None
        if not self.bare and me not in map(os.path.abspath, self.use_files):
            collect_defs(self.nodes.values(), None, self.schema, self.rules, self.warnings)
        types = self.schema["links"]
        seen = {}

        for nid, typ, rev, args, line in raw_links:
            if typ in BUILTIN_LINKS:
                hint = f" (viết - meta: contain=...)" if typ == "contain" else ""
                self.err(line, f"loại link {typ} do parser tự sinh, không viết tay{hint}")
                continue
            if types and typ not in types:
                self.err(line, f"loại link không khai báo trong schema: {typ}")
            for a in args or [None]:
                if a is None:
                    tgt = self.nearest_explicit(nid)
                    if tgt is None:
                        self.err(line, f"{typ}() không có node chứa để trỏ tới")
                        continue
                else:
                    tgt = self.resolve(a, line)
                    if tgt is None:
                        continue
                src, dst = (tgt, nid) if rev else (nid, tgt)
                key = (src, typ, dst)
                if key in seen:
                    self.err(line, f"cạnh {typ}: {src} → {dst} khai báo lại (lần đầu dòng {seen[key]})")
                    continue
                seen[key] = line
                self.check_link_ends(typ, src, dst, line)
                self.links.append({"source": src, "target": dst, "type": typ,
                                   "line": line, "declared_at": nid, "reversed": rev})

        for node in list(self.nodes.values()):          # tham chiếu @ trong văn bản
            if node["kind"] == "node" and not node.get("def"):     # node định nghĩa schema/style: không kiểm meta
                self.check_meta(node)
            for fld in ("content", "ask"):
                for m in RE_MENTION.finditer(prose(node.get(fld) or "")):
                    tgt = self.resolve(m.group(1), node["line"])
                    if tgt and (node["id"], "mention", tgt) not in seen:
                        seen[(node["id"], "mention", tgt)] = node["line"]
                        self.links.append({"source": node["id"], "target": tgt,
                                           "type": "mention", "line": node["line"],
                                           "declared_at": node["id"], "reversed": False})

        for node in list(self.nodes.values()):          # meta contain=a, b → cạnh contain
            if node["kind"] != "node" or "contain" not in node["meta"]:
                continue
            line, value = node.get("meta_line", node["line"]), node["meta"]["contain"]
            if not isinstance(value, str) or not value.strip():
                self.err(line, "contain cần danh sách ID: contain=a hoặc contain=\"a, b\"")
                continue
            for ref in split_list(value):
                tgt = self.resolve(ref, line)
                if tgt is None or (node["id"], "contain", tgt) in seen:
                    continue
                seen[(node["id"], "contain", tgt)] = line
                self.links.append({"source": node["id"], "target": tgt, "type": "contain",
                                   "line": line, "declared_at": node["id"], "reversed": False})

        for node in self.nodes.values():                # cạnh cây chứa
            if node.get("parent"):
                self.links.append({"source": node["parent"], "target": node["id"],
                                   "type": "contains", "tree": True})
        self.check_cycles()
        return self.to_json()

    def dag_types(self):
        L = self.schema["links"]
        dag = [t for t, s in L.items() if s["dag"]] if L else list(DEFAULT_DAG)
        return dag + ["contain"]

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

    def to_json(self):
        links = [{**l, "key": f"{l['type']}:{i}"} for i, l in enumerate(self.links)]
        full = [dict(nd) for nd in self.nodes.values()]      # cần trường rỗng để so selector
        apply_style(self.rules, full, links)
        nodes = [{k: v for k, v in nd.items() if v not in (None, "", {}) or k in ("id", "parent")}
                 for nd in full]
        return {
            "directed": True,
            "multigraph": True,
            "graph": {
                "file": os.path.basename(self.filename),
                "kg": self.fm["kg"],
                "use": self.use_shown,
                "fields": FIELDS,
                "schema": self.schema,
                "dag": self.dag_types(),
                "import_modules": self.fm["modules"],
                "import_names": self.fm["names"],
                "errors": self.errors,
                "warnings": self.warnings,
            },
            "nodes": nodes,
            "links": links,
        }
