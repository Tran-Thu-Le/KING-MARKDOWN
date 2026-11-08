"""king_markdown.ops - phép sửa văn bản .kg.md.

Mọi thao tác trên đồ thị (thêm node, nối link, đổi style...) được đổi thành phép sửa
văn bản trên lớp Doc. Server gọi các hàm trong OPS qua /api/op.
"""
import os
import re
import shutil

from .parser import (BUILTIN_LINKS, ID, RE_FENCE, RE_FIELD, RE_HEADING, RE_LINK, RE_NODE, SYSTEM_PREFIX,
                     Parser, as_text, bracket_lines, format_meta, parse_value, read, slug, split_list,
                     strip_comment, system_file, use_path)
HEADS = {"type": "Kiểu node", "key": "Khóa meta", "link": "Loại link"}
SKELETON = {
    "schema": "---\nkg: 0.2\n---\n\n# Kiểu node\n\n# Khóa meta\n\n# Loại link\n",
    "style": "---\nkg: 0.2\n---\n\n# Theo loại\n\n# Theo meta\n\n# Node cụ thể\n\n# Link\n",
}


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def split_tail(raw):
    """'- link: a(b)   // ghi chú' → ('- link: a(b)', '   // ghi chú')."""
    m = re.search(r"(^|\s)//", raw)
    code = (raw[: m.start()] if m else raw).rstrip()
    return code, raw[len(code):]


# ====================== văn bản .kg.md ======================
class Doc:
    """Văn bản + kết quả parse, kèm vị trí heading/node để chèn, cắt khối."""

    def __init__(self, text, path, bare=False):
        self.path, self.bare = path, bare
        self.lines = text.replace("\r\n", "\n").split("\n")
        self.p = Parser("\n".join(self.lines), path, bare=bare)
        self.p.build()
        self.inbr = bracket_lines(self.lines)          # dòng trong nội dung [ ... ]: không phải node / heading / trường
        self.body, self.bounds = self._outline()
        self.at = {n["id"]: n["line"] - 1 for n in self.p.nodes.values() if n["kind"] != "external"}

    @property
    def text(self):
        return "\n".join(self.lines)

    def again(self):
        return Doc(self.text, self.path, self.bare)

    def _outline(self):
        L, out, i, fence = self.lines, [], 0, False
        if L and L[0].strip() == "---":
            i = 1
            while i < len(L) and L[i].strip() != "---":
                i += 1
            i += 1
        for j in range(i, len(L)):
            if j in self.inbr:
                continue
            if RE_FENCE.match(L[j]):
                fence = not fence
                continue
            if fence:
                continue
            code = strip_comment(L[j])
            if RE_HEADING.match(code):
                out.append((j, "section"))
            elif RE_NODE.match(code.strip()):
                out.append((j, "node"))
        return i, out

    def kind(self, nid):
        n = self.p.nodes.get(nid)
        return n and n["kind"]

    def need(self, nid, kind):
        if self.kind(nid) != kind:
            raise ValueError(f"không có {kind} '{nid}'")

    def nxt(self, i, kinds=("section", "node")):
        return next((j for j, k in self.bounds if j > i and k in kinds), len(self.lines))

    def trim(self, s, e):
        while e > s + 1 and not self.lines[e - 1].strip():
            e -= 1
        return e

    def node_range(self, nid):
        i = self.at[nid]
        return i, self.trim(i, self.nxt(i))

    def insert_pos(self, sid=None):
        """Cuối phần node trực tiếp của section (trước heading kế tiếp), hoặc cuối file."""
        if sid:
            i = self.at[sid]
            return self.trim(i, self.nxt(i, ("section",)))
        return self.trim(self.body - 1, len(self.lines))

    def insert(self, pos, block):
        L = self.lines
        pre = [""] if pos > 0 and L[pos - 1].strip() else []
        post = [""] if pos < len(L) and L[pos].strip() else []
        L[pos:pos] = pre + block + post

    def cut(self, nid):
        s, e = self.node_range(nid)
        block = self.lines[s:e]
        del self.lines[s:e]
        while 0 < s < len(self.lines) and not self.lines[s - 1].strip() and not self.lines[s].strip():
            del self.lines[s]
        return block

    def field_lines(self, nid, key):
        s, e = self.node_range(nid)
        out, fence = [], False
        for j in range(s + 1, e):
            if j in self.inbr:
                continue
            if RE_FENCE.match(self.lines[j]):
                fence = not fence
                continue
            m = None if fence else RE_FIELD.match(strip_comment(self.lines[j]))
            if m and m.group(1) == key:
                out.append(j)
        return out

    def section_titled(self, title):
        return next((n["id"] for n in self.p.nodes.values()
                     if n["kind"] == "section" and n["title"].strip().lower() == title.lower()), None)

    def ensure_section(self, title, *fallback):
        """Trả (doc, id section có tiêu đề title, hoặc một tiêu đề trong fallback nếu đã có),
        thêm heading cấp 1 '# title' cuối file nếu chưa có cái nào."""
        for t in (title, *fallback):
            sid = self.section_titled(t)
            if sid:
                return self, sid
        d = self
        d.insert(d.insert_pos(), [f"# {title}"])
        d = d.again()
        return d, d.section_titled(title)

    def unique(self, base):
        nid, k = base, 2
        while nid in self.p.nodes:
            nid, k = f"{base}-{k}", k + 1
        return nid

    def ref(self, nid):
        """Tên viết trong link: node import lẻ viết ngắn, node của module viết đủ."""
        if self.kind(nid) == "external":
            mod, name = nid.split(".", 1)
            return name if self.p.fm["names"].get(name) == mod else nid
        return nid


# ====================== thao tác trên .kg.md ======================
def op_add_node(d, title, id=None, section=None):
    title = title.strip()
    if section:
        d.need(section, "section")
    nid = id or d.unique(slug(title))
    if not re.fullmatch(ID, nid):
        raise ValueError(f"ID không hợp lệ: {nid}")
    if nid in d.p.nodes:
        raise ValueError(f"ID đã có: {nid}")
    d.insert(d.insert_pos(section), [f"@{nid}: {title}"])
    return d.text, {"id": nid}


def op_move_node(d, ids, section):
    for nid in ids:
        d.need(nid, "node")
        d.need(section, "section")
        block = d.cut(nid)
        d = d.again()
        d.insert(d.insert_pos(section), block)
        d = d.again()
    return d.text, {"msg": f"Đã chuyển {', '.join(ids)} vào {section}"}


def op_delete_node(d, ids):
    for nid in ids:
        d.need(nid, "node")
        d.cut(nid)
        d = d.again()
    return d.text, {"msg": f"Đã xóa {', '.join(ids)}"}


def op_rename(d, id, title):
    j, n = d.at[id], d.p.nodes[id]
    code, tail = split_tail(d.lines[j])
    if n["kind"] == "node":
        d.lines[j] = f"@{id}: {title}" + tail
    else:
        m = RE_HEADING.match(code)
        d.lines[j] = f"{m.group(1)} {title}" + (f" @{m.group(3)}" if m.group(3) else "") + tail
    return d.text, {}


def op_add_link(d, source, target, type):
    if not re.fullmatch(r"[a-z][a-z0-9-]*", type) or type in BUILTIN_LINKS:
        raise ValueError(f"loại link không dùng được: {type}")
    if any((l["source"], l["target"], l["type"]) == (source, target, type) for l in d.p.links):
        raise ValueError(f"cạnh {type}: {source} → {target} đã có")
    if d.kind(source) == "node":
        holder, token = source, f"{type}({d.ref(target)})"
    elif d.kind(target) == "node":
        holder, token = target, f"{type}!({d.ref(source)})"
    else:
        raise ValueError("link cần ít nhất một đầu là node (section và node import không có dòng link)")
    rows = d.field_lines(holder, "link")
    if rows:
        code, tail = split_tail(d.lines[rows[0]])
        sep = ", " if RE_FIELD.match(code).group(2).strip() else " "
        d.lines[rows[0]] = code + sep + token + tail
    else:
        s, e = d.node_range(holder)
        d.lines[e:e] = [f"- link: {token}"]
    return d.text, {"msg": f"Đã nối {source} → {target} ({type})"}


def _remove_link(d, spec):
    l = next((l for l in d.p.links if not l.get("tree") and l["type"] != "mention"
              and (l["source"], l["target"], l["type"]) == (spec["source"], spec["target"], spec["type"])), None)
    if not l:
        raise ValueError(f"không tìm thấy link {spec['type']}: {spec['source']} → {spec['target']}")
    j = l["line"] - 1
    other = l["source"] if l["reversed"] else l["target"]
    code, tail = split_tail(d.lines[j])
    m = RE_FIELD.match(code)
    prefix, value = (code[: m.start(2)], code[m.start(2):]) if m else ("", code)
    toks = [[t.group(1), t.group(2), split_list(t.group(3))] for t in RE_LINK.finditer(value)]
    done = False
    for t in toks:
        if done or t[0] != l["type"] or (t[1] == "!") != l["reversed"]:
            continue
        if not t[2]:
            if d.p.nearest_explicit(l["declared_at"]) == other:
                t[2], done = None, True
            continue
        hit = next((a for a in t[2] if a == other or other.endswith("." + a)), None)
        if hit:
            t[2].remove(hit)
            t[2] = t[2] or None
            done = True
    if not done:
        raise ValueError(f"không sửa được dòng {j + 1}")
    toks = [t for t in toks if t[2] is not None]          # [] = loại() chưa bị xóa, giữ lại
    if toks:
        d.lines[j] = prefix + ", ".join(f"{a}{b}({', '.join(c)})" for a, b, c in toks) + tail
    else:
        del d.lines[j]


def op_delete_link(d, links):
    for spec in links:
        _remove_link(d, spec)
        d = d.again()
    return d.text, {"msg": f"Đã xóa {len(links)} link"}


# ====================== thao tác trên schema / style ======================
def role_of(path, parser=None):
    p = parser
    if p is None:
        p = Parser(read(path), path, bare=True)
        p.build()
    roles = set()
    for n in p.nodes.values():
        if "select" in n["meta"]:
            roles.add("style")
        if n["meta"].get("kind") in HEADS:
            roles.add("schema")
    return roles


def template(role):
    """Bản mẫu schema/style của hệ thống (cũng là file mà use: king/schema, king/style trỏ tới)."""
    return system_file(role)


def seed(path, role):
    src = template(role)
    if src and os.path.abspath(src) != os.path.abspath(path):
        shutil.copyfile(src, path)
    else:
        write(path, SKELETON[role])


def add_use(text, name):
    L = text.split("\n")
    if L and L[0].strip() == "---":
        for i in range(1, len(L)):
            if L[i].strip() == "---":
                L.insert(i, f"use: {name}")
                break
            if L[i].split(":", 1)[0].strip() == "use":
                code, tail = split_tail(L[i])
                L[i] = code + f", {name}" + tail
                break
        return "\n".join(L)
    return f"---\nkg: 0.2\nuse: {name}\n---\n\n" + text


def use_file(d, role):
    """File schema/style mà .kg.md đang dùng; chưa có thì tạo và thêm vào use:."""
    folder = os.path.dirname(d.path)
    mine = role_of(d.path, d.p)
    if role in mine:                          # đang mở chính file schema/style: sửa thẳng văn bản này
        return d.text, d.path
    names = d.p.fm["use"]
    for name in names:
        if name.startswith(SYSTEM_PREFIX):    # không sửa schema / style hệ thống (dùng chung): ghi vào file của thư mục
            continue
        f = use_path(folder, name)
        if os.path.exists(f) and role in role_of(f):
            return d.text, f
    f = os.path.join(folder, role + ".kg.md")
    if not os.path.exists(f):
        seed(f, role)
    if role in names or mine:                 # file schema/style không cần use: (ví dụ đang mở schema.kg.md)
        return d.text, f
    return add_use(d.text, role), f


def op_set_style(d, selectors, props):
    """props=None: xóa định dạng html.* của các selector."""
    text, spath = use_file(d, "style")
    same = os.path.abspath(spath) == os.path.abspath(d.path)
    sd = Doc(d.text if same else read(spath), spath, bare=True)
    for sel in selectors:
        rule = next((n for n in sd.p.nodes.values()
                     if n["kind"] == "node" and as_text(n["meta"].get("select", "")) == sel), None)
        if rule:
            meta = dict(rule["meta"])
            if props is None:
                meta = {k: v for k, v in meta.items() if not k.startswith("html.")}
            else:
                for k, v in props.items():
                    if v in (None, ""):
                        meta.pop("html." + k, None)
                    else:
                        meta["html." + k] = v
            rows = sd.field_lines(rule["id"], "meta")
            if set(meta) <= {"select"}:
                sd.cut(rule["id"])
            else:
                sd.lines[rows[0]] = "- meta: " + format_meta(meta)
                for j in reversed(rows[1:]):
                    del sd.lines[j]
        elif props and any(v not in (None, "") for v in props.values()):
            sd, sid = sd.ensure_section("Link" if sel.startswith("link") else "Node cụ thể", "Style")
            meta = {"select": sel, **{"html." + k: v for k, v in props.items() if v not in (None, "")}}
            sd.insert(sd.insert_pos(sid), [f"@{sd.unique('s-' + slug(sel))}", "- meta: " + format_meta(meta)])
        sd = sd.again()
    if same:
        return sd.text, {"msg": f"Đã sửa {os.path.basename(spath)}"}
    write(spath, sd.text)
    return text, {"msg": f"Đã ghi {os.path.basename(spath)}"}


def op_schema_add(d, kind, id, title="", extra=None):
    if kind not in HEADS:
        raise ValueError(f"kind lạ: {kind}")
    if not re.fullmatch(ID, id or ""):
        raise ValueError(f"ID không hợp lệ: {id}")
    text, spath = use_file(d, "schema")
    same = os.path.abspath(spath) == os.path.abspath(d.path)
    sd = Doc(d.text if same else read(spath), spath, bare=True)
    if id in sd.p.nodes:
        raise ValueError(f"{id} đã có trong {os.path.basename(spath)}")
    sd, sid = sd.ensure_section(HEADS[kind], "Schema")
    meta = {"kind": kind, **(extra or {})}
    sd.insert(sd.insert_pos(sid), [f"@{id}" + (f": {title}" if title else ""), "- meta: " + format_meta(meta)])
    if same:
        return sd.text, {"msg": f"Đã sửa {os.path.basename(spath)}"}
    write(spath, sd.text)
    return text, {"msg": f"Đã thêm {id} vào {os.path.basename(spath)}"}


# ====================== meta, content / ask / show của một node ======================
def _field_blocks(d, nid, key):
    """Các khối (đầu, cuối) của trường key: dòng '- key:' cùng các dòng nối tiếp.
    meta/link/show dừng ở dòng trống; content/ask nối tới trường kế tiếp (giống parser)."""
    s, e = d.node_range(nid)
    out = []
    for j in d.field_lines(nid, key):
        k, fence = j + 1, False
        while k < e:
            line = d.lines[k]
            if k in d.inbr:                      # nội dung [ ... ]: thuộc khối này tới dấu ']'
                k += 1
                continue
            if RE_FENCE.match(line):
                fence = not fence
            elif not fence:
                code = strip_comment(line)
                if RE_FIELD.match(code) or (key in ("meta", "link", "show") and not code.strip()):
                    break
            k += 1
        while k > j + 1 and not d.lines[k - 1].strip():
            k -= 1
        out.append((j, k))
    return out


def _replace_field(d, nid, key, block):
    """Xóa mọi khối của trường key rồi chèn block vào chỗ khối đầu (hoặc chỗ hợp thứ tự)."""
    d.need(nid, "node")
    blocks = _field_blocks(d, nid, key)
    s, e = d.node_range(nid)
    if blocks:
        pos = blocks[0][0]
    else:                                   # thứ tự trường: meta, content, ask, link, show
        order = ["meta", "content", "ask", "link", "show"]
        later = [j for f in order[order.index(key) + 1:] for j in d.field_lines(nid, f)]
        pos = min(later) if later else e
    for a, b in reversed(blocks):
        del d.lines[a:b]
    d.lines[pos:pos] = block
    return d.text


def op_set_meta(d, id, meta):
    """meta: dict khóa → giá trị (chuỗi được hiểu như khi viết tay: true/false, số, chuỗi)."""
    clean = {}
    for k, v in (meta or {}).items():
        k = str(k).strip()
        if not re.fullmatch(r"[A-Za-z][\w.-]*", k):
            raise ValueError(f"khóa meta không hợp lệ: {k}")
        clean[k] = parse_value(v) if isinstance(v, str) else v
    text = _replace_field(d, id, "meta", ["- meta: " + format_meta(clean)] if clean else [])
    return text, {"msg": f"Đã ghi meta của {id}"}


def op_set_field(d, id, key, value):
    """content / ask / show. Giá trị rỗng thì xóa trường. Dòng sau của content/ask thụt 2 dấu cách."""
    if key not in ("content", "ask", "show"):
        raise ValueError(f"không sửa được trường {key} bằng set_field")
    lines = [x.rstrip() for x in str(value or "").replace("\r\n", "\n").strip("\n").split("\n")]
    if key == "show":
        lines = lines[:1]
    if not "".join(lines).strip():
        block = []
    else:
        block = [f"- {key}: {lines[0].strip()}"] + [("  " + x.strip()) if x.strip() else "" for x in lines[1:]]
    return _replace_field(d, id, key, block), {"msg": f"Đã ghi {key} của {id}"}


# ====================== sao chép / dán / comment node (Ctrl+C, V, / trên đồ thị) ======================
def _node_blocks(text):
    """Tách văn bản thành các khối node: [(id, [dòng...])]. Dòng trước node đầu tiên bị bỏ."""
    blocks, cur, fence = [], None, False
    for line in text.replace("\r\n", "\n").split("\n"):
        if RE_FENCE.match(line):
            fence = not fence
        m = None if fence else RE_NODE.match(strip_comment(line).strip())
        if m:
            cur = (m.group(1), [line.strip()])
            blocks.append(cur)
        elif cur is not None and not (not fence and RE_HEADING.match(strip_comment(line))):
            cur[1].append(line)
        elif cur is not None:
            cur = None                       # gặp heading: hết khối
    for _, lines in blocks:
        while len(lines) > 1 and not lines[-1].strip():
            lines.pop()
    return blocks


def op_paste_nodes(d, clip, section=None):
    """Dán các khối node (từ Ctrl+C). ID trùng thì đổi sang ID mới; tham chiếu giữa các node vừa dán đổi theo."""
    if section:
        d.need(section, "section")
    blocks = _node_blocks(clip)
    if not blocks:
        raise ValueError("nội dung dán không có node nào (dòng @id)")
    taken, rename = set(d.p.nodes), {}
    for old, _ in blocks:
        new, k = old, 2
        while new in taken:
            new, k = f"{old}-{k}", k + 1
        taken.add(new)
        rename[old] = new
    pat = re.compile(r"(?<![\w.@-])(@?)(" + "|".join(map(re.escape, sorted(rename, key=len, reverse=True))) + r")(?![\w-])")
    out = []
    for i, (old, lines) in enumerate(blocks):
        body = [pat.sub(lambda m: m.group(1) + rename[m.group(2)], x) for x in lines]
        out += ([""] if i else []) + body
    d.insert(d.insert_pos(section), out)
    ids = [rename[old] for old, _ in blocks]
    return d.text, {"ids": ids, "msg": f"Đã dán {len(ids)} node: {', '.join(ids)}"}


def op_comment_nodes(d, ids):
    """Ctrl+/ trên đồ thị: thêm '// ' trước mọi dòng của các node (node biến mất khỏi đồ thị, văn bản còn giữ)."""
    spans = []
    for nid in ids:
        d.need(nid, "node")
        spans.append(d.node_range(nid))
    for s, e in sorted(spans, reverse=True):
        for j in range(s, e):
            if d.lines[j].strip():
                d.lines[j] = "// " + d.lines[j]
    return d.text, {"msg": f"Đã comment {', '.join(ids)} (bỏ comment: Ctrl+/ trong khung văn bản, hoặc Ctrl+Z)"}


OPS = {"add_node": op_add_node, "move_node": op_move_node, "delete_node": op_delete_node,
       "rename": op_rename, "add_link": op_add_link, "delete_link": op_delete_link,
       "set_style": op_set_style, "schema_add": op_schema_add,
       "set_meta": op_set_meta, "set_field": op_set_field,
       "paste_nodes": op_paste_nodes, "comment_nodes": op_comment_nodes}
