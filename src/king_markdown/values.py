"""king_markdown.values - đọc / ghi giá trị của KING Markdown 0.3.

Kiểu dữ liệu (đặt theo Typst):
    Num      3, -2, 0.5
    Bool     true, false
    None     none
    Str      chữ tự do, "có, dấu phẩy"
    List     (a, b, c)        (x) là List một phần tử
    Dict     (a=1, b=(x, y))
    Content  [ ... ]          nguyên văn (Typst / LaTeX / Markdown / Python ...)
    code     `...`            chuỗi nguyên văn

Giá trị Python tương ứng: int/float, bool, None, str, list, dict,
{"content": "..."} và {"code": "..."}.
"""
import re

OPEN = {"(": ")", "[": "]"}
DATA_TYPES = ("Num", "Str", "Bool", "None", "List", "Dict", "Content")


class ValueError_(Exception):
    """Lỗi cú pháp giá trị; col là vị trí (tính từ 0) trong chuỗi."""
    def __init__(self, msg, col=0):
        super().__init__(msg)
        self.col = col


def strip_comment(line):
    """Bỏ '// ...' tới cuối dòng. '//' chỉ là comment khi đứng đầu dòng hoặc sau khoảng trắng
    (nên https://... không bị cắt) và không nằm trong "...", `...`."""
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q:
                q = None
        elif c in "\"`":
            q = c
        elif c == "/" and line.startswith("//", i) and (i == 0 or line[i - 1].isspace()):
            return line[:i].rstrip()
    return line.rstrip()


def split_top(s, sep=","):
    """Tách theo sep ở mức ngoài cùng; tôn trọng ( ), [ ], "...", `...`."""
    out, buf, depth, q, i = [], [], [], None, 0
    while i < len(s):
        c = s[i]
        if q:
            buf.append(c)
            if c == q:
                q = None
        elif c in "\"`":
            q = c
            buf.append(c)
        elif c in OPEN:
            depth.append(OPEN[c])
            buf.append(c)
        elif depth and c == depth[-1]:
            depth.pop()
            buf.append(c)
        elif not depth and s.startswith(sep, i):
            out.append("".join(buf))
            buf = []
            i += len(sep)
            continue
        else:
            buf.append(c)
        i += 1
    out.append("".join(buf))
    return [x.strip() for x in out]


def _closing(s, start):
    """Vị trí ngoặc đóng khớp với ngoặc mở ở s[start]; -1 nếu thiếu."""
    stack, q = [], None
    for i in range(start, len(s)):
        c = s[i]
        if q:
            if c == q:
                q = None
        elif c in "\"`":
            q = c
        elif c in OPEN:
            stack.append(OPEN[c])
        elif stack and c == stack[-1]:
            stack.pop()
            if not stack:
                return i
    return -1


def has_eq(item):
    """'a=1' (khóa Dict) — dấu = ở mức ngoài cùng, trước mọi ngoặc / chuỗi."""
    m = re.match(r"\s*([A-Za-z_][\w-]*)\s*=(?!=)", item)
    return bool(m)


def parse_value(s):
    """Chuỗi → giá trị Python. Ném ValueError_ khi sai cú pháp."""
    v = s.strip()
    if v == "":
        return ""
    if v[0] == "[":
        end = _closing(v, 0)
        if end == -1:
            raise ValueError_("Content thiếu ']'", len(s))
        if v[end + 1:].strip():
            raise ValueError_("thừa chữ sau ']'", end + 1)
        return {"content": v[1:end].strip("\n").strip() if "\n" not in v[1:end] else _dedent(v[1:end])}
    if v[0] == "`":
        if v.count("`") == 1:
            raise ValueError_("code thiếu '`' đóng", len(s))
        if len(v) >= 2 and v.endswith("`") and "`" not in v[1:-1]:
            return {"code": v[1:-1]}
        return v                                       # `a` và `b`: chuỗi có code bên trong
    if v[0] == "(":
        end = _closing(v, 0)
        if end == -1:
            raise ValueError_("thiếu ')'", len(s))
        if v[end + 1:].strip():
            return v                                   # "(a) b": chuỗi thường
        inner = v[1:end].strip()
        if not inner:
            return []
        items = split_top(inner)
        if items and items[-1] == "":                  # (a,) → List một phần tử
            items = items[:-1]
        if any(x == "" for x in items):
            raise ValueError_("phần tử rỗng giữa hai dấu phẩy", 0)
        dicts = [has_eq(x) for x in items]
        if all(dicts):
            out = {}
            for x in items:
                k, val = x.split("=", 1)
                k = k.strip()
                if k in out:
                    raise ValueError_(f"Dict trùng khóa: {k}", 0)
                out[k] = parse_value(val)
            return out
        if any(dicts):
            raise ValueError_("trộn List và Dict trong cùng một ( )", 0)
        return [parse_value(x) for x in items]
    if len(v) >= 2 and v[0] == '"' and not (v.endswith('"') and '"' not in v[1:-1]):
        if v.count('"') > 1:
            return v                                   # "a" và "b": chuỗi thường
    if len(v) >= 2 and v[0] == '"':
        if not v.endswith('"'):
            raise ValueError_('chuỗi thiếu \'"\' đóng', len(s))
        return v[1:-1]
    if v == '"':
        raise ValueError_('chuỗi thiếu \'"\' đóng', len(s))
    if v in ("true", "false"):
        return v == "true"
    if v == "none":
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def _dedent(text):
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return "\n".join(l[ind:] for l in lines)


def type_of(v):
    """Tên kiểu dữ liệu của một giá trị đã đọc."""
    if v is None:
        return "None"
    if isinstance(v, bool):
        return "Bool"
    if isinstance(v, (int, float)):
        return "Num"
    if isinstance(v, list):
        return "List"
    if isinstance(v, dict):
        if set(v) == {"content"}:
            return "Content"
        if set(v) == {"code"}:
            return "Str"
        return "Dict"
    return "Str"


def format_value(v):
    """Giá trị → văn bản; parse_value(format_value(v)) == v."""
    if v is None:
        return "none"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        if len(v) == 1:
            return "(" + format_value(v[0]) + ")"
        return "(" + ", ".join(format_value(x) for x in v) + ")"
    if isinstance(v, dict):
        if set(v) == {"content"}:
            return "[" + v["content"] + "]"
        if set(v) == {"code"}:
            return "`" + v["code"] + "`"
        return "(" + ", ".join(f"{k}={format_value(x)}" for k, x in v.items()) + ")"
    s = str(v)
    plain = (s == s.strip() and s and not re.search(r'[,()\[\]"`]|\s//|=', s)
             and parse_value(s) == s and not s.startswith("("))
    return s if plain else '"' + s.replace('"', "'") + '"'


def as_text(v):
    """Giá trị → chữ để hiển thị / so khớp selector style."""
    if isinstance(v, dict) and set(v) in ({"content"}, {"code"}):
        return next(iter(v.values()))
    if isinstance(v, (list, dict)) or v is None or isinstance(v, bool):
        return format_value(v)
    return str(v)
