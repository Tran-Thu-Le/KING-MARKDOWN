"""king_markdown.ops03 - phép sửa văn bản cho file KING 0.3 (thao tác đồ thị từ web app).

ops.py viết cho cú pháp 0.2 (@id: Tiêu đề, - link: loại(x)); dùng nó trên file 0.3 sẽ trộn cú pháp.
Ở đây mỗi thao tác sinh đúng cú pháp 0.3:
    @node id            - label: Tiêu đề            - link loai: (a, b)
Thao tác chưa có bản 0.3 thì báo lỗi rõ ràng (sửa trong khung Text), không ghi gì.
Chữ ký hàm giống ops.py: op(d, **args) -> (text, extra); d là Doc03.
"""
import re

from .legacy import slug
from .parser import Parser

ID = r"[a-z0-9][a-z0-9-]*"
RE_LINKLINE = re.compile(rf"^(- link[ \t]+)({ID})([ \t]*:[ \t]*)(.*?)([ \t]+//.*)?$")
RE_LABEL = re.compile(r"^- label[ \t]*:")
RE_ATTR = re.compile(r"^- ")
RE_HEAD = re.compile(r"^(#{1,6})[ \t]+(.*?)([ \t]+@" + ID + r")?([ \t]+//.*)?$")


class Doc03:
    def __init__(self, text, path, bare=False):
        self.path, self.bare = path, bare
        self.lines = text.replace("\r\n", "\n").split("\n")
        g = Parser("\n".join(self.lines), path, bare=bare).build()
        self.nodes = {n["id"]: n for n in g["nodes"] if n.get("line")}
        self.links = g["links"]

    @property
    def text(self):
        return "\n".join(self.lines)

    def again(self):
        return Doc03(self.text, self.path, self.bare)

    def need(self, nid, kind=None):
        n = self.nodes.get(nid)
        if not n or (kind and n["kind"] != kind):
            raise ValueError(f"không tìm thấy {kind or 'node'}: {nid}")
        return n

    def block(self, nid):
        """(đầu, cuối) 0-based, nửa mở, của khối node (bỏ dòng trống cuối)."""
        n = self.need(nid, "node")
        s, e = n["line"] - 1, n["end"]
        while e > s + 1 and not self.lines[e - 1].strip():
            e -= 1
        return s, e

    def attr_end(self, nid):
        """Vị trí sau dòng thuộc tính cuối liền sau @node."""
        s, e = self.block(nid)
        j = s + 1
        while j < e and RE_ATTR.match(self.lines[j]):
            j += 1
        return j

    def subtree_end(self, sid):
        ids, todo = {sid}, [sid]
        while todo:
            p = todo.pop()
            for n in self.nodes.values():
                if n.get("parent") == p and n["id"] not in ids:
                    ids.add(n["id"]); todo.append(n["id"])
        e = max(self.nodes[i]["end"] for i in ids)
        while e > 0 and not self.lines[e - 1].strip():
            e -= 1
        return e

    def unique(self, base):
        base = base or "node"
        nid, k = base, 2
        while nid in self.nodes:
            nid, k = f"{base}-{k}", k + 1
        return nid


def _insert(d, pos, rows):
    if pos > 0 and d.lines[pos - 1].strip():
        rows = [""] + rows
    if pos < len(d.lines) and d.lines[pos].strip():
        rows = rows + [""]
    d.lines[pos:pos] = rows


def op_add_node(d, title, id=None, section=None):
    title = title.strip()
    nid = id or d.unique(slug(title))
    if not re.fullmatch(ID, nid):
        raise ValueError(f"ID không hợp lệ: {nid}")
    if nid in d.nodes:
        raise ValueError(f"ID đã có: {nid}")
    if section:
        d.need(section, "section")
        pos = d.subtree_end(section)
    else:
        pos = len(d.lines)
        while pos > 0 and not d.lines[pos - 1].strip():
            pos -= 1
    _insert(d, pos, [f"@node {nid}", f"- label: {title}"])
    return d.text, {"id": nid}


def op_rename(d, id, title):
    n = d.need(id)
    j = n["line"] - 1
    if n["kind"] == "section":
        m = RE_HEAD.match(d.lines[j])
        d.lines[j] = f"{m.group(1)} {title}{m.group(3) or ''}{m.group(4) or ''}"
        return d.text, {}
    s, e = d.block(id)
    for k in range(s + 1, d.attr_end(id)):
        if RE_LABEL.match(d.lines[k]):
            d.lines[k] = f"- label: {title}"; break
    else:
        d.lines.insert(s + 1, f"- label: {title}")
    return d.text, {}


def op_add_link(d, source, target, type):
    if not re.fullmatch(ID, type) or type in ("contains", "mention"):
        raise ValueError(f"loại link không dùng được: {type}")
    if any((l["source"], l["target"], l["type"]) == (source, target, type) for l in d.links):
        raise ValueError(f"cạnh {type}: {source} → {target} đã có")
    d.need(source, "node"); d.need(target)
    s, end = d.block(source)
    for k in range(s + 1, d.attr_end(source)):
        m = RE_LINKLINE.match(d.lines[k])
        if m and m.group(2) == type:
            items = [x.strip() for x in m.group(4).strip().strip("()").split(",") if x.strip()]
            items.append(target)
            d.lines[k] = f"{m.group(1)}{type}{m.group(3)}({', '.join(items)}){m.group(5) or ''}"
            break
    else:
        d.lines.insert(d.attr_end(source), f"- link {type}: ({target})")
    return d.text, {"msg": f"Đã nối {source} → {target} ({type})"}


def _remove_link(d, spec):
    l = next((l for l in d.links if not l.get("tree") and l["type"] != "mention" and l.get("line")
              and (l["source"], l["target"], l["type"]) == (spec["source"], spec["target"], spec["type"])), None)
    if not l:
        raise ValueError(f"không tìm thấy link {spec['type']}: {spec['source']} → {spec['target']}")
    j = l["line"] - 1
    other = l["source"] if l.get("reversed") else l["target"]
    m = RE_LINKLINE.match(d.lines[j])
    if not m:
        raise ValueError(f"dòng {j + 1} không phải '- link …:' (sửa trong khung Text)")
    items = [x.strip() for x in m.group(4).strip().strip("()").split(",") if x.strip()]
    hit = next((x for x in items if x == other or other.endswith("." + x) or x.endswith("." + other)), None)
    if not hit:
        raise ValueError(f"không sửa được dòng {j + 1}")
    items.remove(hit)
    if items:
        d.lines[j] = f"{m.group(1)}{m.group(2)}{m.group(3)}({', '.join(items)}){m.group(5) or ''}"
    else:
        del d.lines[j]


def op_delete_link(d, links):
    for spec in links:
        _remove_link(d, spec)
        d = d.again()
    return d.text, {"msg": f"Đã xóa {len(links)} link"}


def _cut(d, nid):
    s, e = d.block(nid)
    rows = d.lines[s:e]
    del d.lines[s:e]
    while s < len(d.lines) and s > 0 and not d.lines[s].strip() and not d.lines[s - 1].strip():
        del d.lines[s]
    return rows


def op_delete_node(d, ids):
    dropped, mentions = 0, []
    for nid in ids:
        d.need(nid, "node")
        mentions += [f"@{nid} (dòng {l['line']})" for l in d.links
                     if l["type"] == "mention" and l["target"] == nid and l.get("declared_at") != nid]
        # gỡ các link khai báo ở node KHÁC trỏ tới nid (tránh link treo)
        while True:
            l = next((l for l in d.links if l.get("line") and not l.get("tree") and l["type"] != "mention"
                      and nid in (l["source"], l["target"]) and l.get("declared_at") != nid), None)
            if not l:
                break
            _remove_link(d, l); d = d.again(); dropped += 1
        _cut(d, nid)
        d = d.again()
    msg = f"Đã xóa {', '.join(ids)}" + (f" và {dropped} link trỏ tới" if dropped else "")
    if mentions:   # văn xuôi của người viết: không tự sửa, chỉ báo
        msg += f". Còn nhắc trong văn bản, cần sửa tay: {', '.join(mentions)}"
    return d.text, {"msg": msg}


def op_move_node(d, ids, section):
    for nid in ids:
        d.need(nid, "node"); d.need(section, "section")
        rows = _cut(d, nid)
        d = d.again()
        _insert(d, d.subtree_end(section), rows)
        d = d.again()
    return d.text, {"msg": f"Đã chuyển {', '.join(ids)} vào {section}"}


def op_comment_nodes(d, ids):
    for nid in ids:
        s, e = d.block(nid)
        for j in range(s, e):
            if d.lines[j].strip():
                d.lines[j] = "// " + d.lines[j]
    return d.text, {"msg": f"Đã comment {', '.join(ids)} (bỏ comment: Ctrl+/ trong khung văn bản, hoặc Ctrl+Z)"}


def _todo(name):
    def f(d, **_):
        raise ValueError(f"'{name}' chưa hỗ trợ trên file kg 0.3: sửa trong khung Text")
    return f


OPS03 = {"add_node": op_add_node, "rename": op_rename, "add_link": op_add_link,
         "delete_link": op_delete_link, "delete_node": op_delete_node, "move_node": op_move_node,
         "comment_nodes": op_comment_nodes}
for _n in ("set_style", "schema_add", "set_meta", "set_field", "paste_nodes"):
    OPS03[_n] = _todo(_n)
