"""Chuyển một file .kg.md v0.2 sang 0.3 (dùng một lần; đọc lại kết quả và sửa tay chỗ chưa đẹp).

    python dev/tools/migrate_02_03.py file.kg.md [...]      # ghi đè file
    python dev/tools/migrate_02_03.py --dry file.kg.md     # in ra màn hình

Không chuyển: node style (meta select=…) — file style giữ cú pháp v0.2.
"""
import re
import sys

ID = r"[a-z0-9][a-z0-9-]*"
RE_NODE = re.compile(rf"^@({ID})\s*(?::\s*(.*))?$")
RE_FIELD = re.compile(r"^\s*[-*]\s+([a-z][a-z0-9-]*)\s*:\s*(.*)$")
RE_LINK = re.compile(r"([a-z][a-z0-9-]*)(!?)\(\s*([^)]*?)\s*\)")


def cap(t):
    return t[:1].upper() + t[1:]


def split_meta(value):
    out, buf, q = [], "", None
    for c in value:
        if q:
            buf += c
            q = None if c == q else q
        elif c == '"':
            buf += c
            q = c
        elif c == ",":
            out.append(buf)
            buf = ""
        else:
            buf += c
    out.append(buf)
    res = []
    for part in (x.strip() for x in out if x.strip()):
        k, eq, v = part.partition("=")
        res.append((k.strip(), v.strip() if eq else "true"))
    return res


def val(v):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        inner = v[1:-1]
        return v if re.search(r"[,()\[\]]|//", inner) else inner
    return v


def comment_of(raw):
    m = re.search(r"(\s+//.*)$", raw)
    return m.group(1) if m else ""


def convert_block(head, fields, body_extra):
    """head: (id, title); fields: [(key, value, comment)] → các dòng 0.3."""
    nid, title = head
    meta = {}
    for k, v, _ in fields:
        if k == "meta":
            meta.update(dict(split_meta(v)))
    kind = meta.get("kind")
    if "select" in meta:
        return None
    if kind == "key":
        return [f"// (0.3: attribute tự do) {nid}: {title}"]
    out = []
    if kind == "type":
        out.append(f"@node {cap(nid)}")
    elif kind == "link":
        out.append(f"@link {nid}")
    else:
        out.append(f"@node {nid}")
    if title and title != nid:
        out.append(f"- label: {title}")
    content, links = [], []
    for k, v, c in fields:
        if k == "meta":
            for mk, mv in split_meta(v):
                if mk in ("kind", "allow", "values", "required", "value", "from", "to"):
                    continue
                if mk == "type":
                    out.append(f"- type: {cap(val(mv))}{c}")
                elif mk == "contain":
                    out.append(f"- contain: ({', '.join(x.strip() for x in val(mv).split(','))})")
                else:
                    out.append(f"- {mk}: {val(mv)}")
                c = ""
        elif k == "link":
            for m in RE_LINK.finditer(v):
                typ, rev, args = m.group(1), m.group(2), m.group(3)
                if rev:
                    out.append(f"// TODO 0.3: {typ}!({args}) — viết link ở node kia hoặc dùng inverse")
                elif not args.strip():
                    out.append(f"// TODO 0.3: {typ}() — ghi rõ tên section đích")
                else:
                    links.append((typ, args, c))
                c = ""
        elif k == "content":
            content.append(v)
        elif k == "ask":
            out.append(f"- ask: {v}{c}")
        else:
            out.append(f"- {k}: {v}{c}")
    merged = {}
    for typ, args, c in links:
        merged.setdefault(typ, [[], ""])
        merged[typ][0] += [x.strip() for x in args.split(",") if x.strip()]
        merged[typ][1] = merged[typ][1] or c
    out += [f"- link {t}: ({', '.join(a)}){c}" for t, (a, c) in merged.items()]
    text = "\n".join(content + body_extra).strip("\n")
    if text.startswith("[") and text.rstrip().endswith("]"):
        text = text.strip()[1:-1].strip("\n")
        lines = text.split("\n")
        ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
        text = "\n".join(l[ind:] for l in lines).strip("\n")
    if text:
        out += ["", text]
    return out


def migrate(text):
    lines = text.splitlines()
    out, i = [], 0
    if lines and lines[0].strip() == "---":
        out.append("---")
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            ln = lines[i]
            if re.match(r"\s*kg\s*:", ln):
                out.append("kg: 0.3")
            elif re.match(r"\s*use\s*:", ln):
                out.append("use:")
                out += [f"- {x.strip()}" for x in ln.split(":", 1)[1].split(",") if x.strip()]
            else:
                out.append(ln)
            i += 1
        out.append("---")
        i += 1
    cur, fields, extra, keep = None, [], [], []

    def flush():
        nonlocal cur, fields, extra
        if cur is None:
            return
        res = convert_block(cur, fields, extra)
        out.extend(res if res is not None else keep)
        cur, fields, extra = None, [], []

    while i < len(lines):
        raw = lines[i]
        line = re.sub(r"\s+//.*$", "", raw)
        m = RE_NODE.match(line.strip()) if raw.startswith("@") else None
        if m:
            flush()
            cur, keep = (m.group(1), (m.group(2) or "").strip()), [raw]
            i += 1
            continue
        if raw.startswith("#"):
            flush()
            out.append(raw)
            i += 1
            continue
        if cur is None:
            out.append(raw)
            i += 1
            continue
        keep.append(raw)
        f = RE_FIELD.match(line)
        if f and not extra:
            k, v = f.group(1), f.group(2).strip()
            if k == "content" and v.startswith("[") and not v.rstrip().endswith("]"):
                buf = [v]
                while i + 1 < len(lines):
                    i += 1
                    keep.append(lines[i])
                    buf.append(lines[i])
                    if lines[i].strip().endswith("]"):
                        break
                v = "\n".join(buf)
            fields.append((k, v, comment_of(raw)))
        elif not raw.strip():
            if fields and fields[-1][0] == "content" and i + 1 < len(lines) and lines[i + 1].strip() \
                    and not RE_FIELD.match(lines[i + 1]) and not lines[i + 1].startswith(("@", "#")):
                extra.append("")
            elif extra:
                extra.append("")
            else:
                pass
            if not extra:
                flush()
                out.append("")
        else:
            if fields and fields[-1][0] == "content" and not extra:
                k, v, c = fields[-1]
                fields[-1] = (k, v + "\n" + raw.strip(), c)
            else:
                extra.append(raw)
        i += 1
    flush()
    res = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", res).rstrip("\n") + "\n"


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry" in args
    for path in (a for a in args if a != "--dry"):
        with open(path, encoding="utf-8") as f:
            new = migrate(f.read())
        if dry:
            sys.stdout.buffer.write(new.encode("utf-8"))
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
            print("đã chuyển", path)
