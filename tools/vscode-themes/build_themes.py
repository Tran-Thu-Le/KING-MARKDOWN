"""Sinh các template màu KING cho extension VS Code "Highlight" → <tên>.json trong thư mục này.

  python tools/vscode-themes/build_themes.py

Sửa màu ở đây rồi chạy lại, sau đó bật bằng tools/sync_vscode_highlight.py --theme <tên>.
Theme 'king' lấy nguyên từ .vscode/settings.json của repo (nguồn gốc của bảng màu web app).
Regex theo cú pháp JavaScript (VS Code); Python chỉ dùng để kiểm tra sơ bộ.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
F = r".*\.kg\.md$"


def R(decs): return {"filterFileRegex": F, "decorations": decs}


# ---------- mẫu dùng chung ----------
NODE_ID    = r"^(@node)([ \t]+)([a-z0-9][a-z0-9-]*)[ \t]*$"
NODE_TYPE  = r"^(@node)([ \t]+)([A-Z][A-Za-z0-9-]*)[ \t]*$"
LINK_DEF   = r"^(@link)([ \t]+)(\S+)[ \t]*$"
LINK_ATTR  = r"^(- )(link)( +)([a-z0-9][a-z0-9-]*)(:)([^\n]*?)(?=\s//|$)"
FROM_TO    = r"^(- )(from)( .*? )(to)( [^\n]*?)(?=\s//|$)"
TYPE_ATTR  = r"^(- )(type)(:)( *[A-Z][A-Za-z0-9-]*)"
REF_INLINE = r"(?<=^|\s)@(?!node\b|link\b)[a-z0-9][a-z0-9-]*"
COMMENT    = r"(?:^|(?<=\s))//[^\n]*"
FRONT      = r"^(kg|use|import)(:)"
KEY  = r"(?!link |from |type:)([A-Za-z_][\w-]*)"
NUM  = r"-?\d+(?:\.\d+)?"
BOOL = r"true|false|True|False|None|null"
V_ANY  = rf"^(- ){KEY}(:)( *[^\n]*?)(?=\s//|$)"
END  = r"[ \t]*(?:$|(?=\s//))"          # hết dòng, hoặc trước comment //
V_NUM  = rf"^(- ){KEY}(:)( *(?:{NUM})){END}"
V_BOOL = rf"^(- ){KEY}(:)( *(?:{BOOL})){END}"
V_REF  = rf"^(- ){KEY}(:)( *\([^\n]*?\)){END}"
V_STR  = rf"^(- ){KEY}(:)(?![ \t]*(?:{NUM}|{BOOL}){END})(?![ \t]*\()( *[^\n]*?)(?=\s//|$)"


def theme_king():
    t = "\n".join(l for l in (REPO / ".vscode/settings.json").read_text(encoding="utf-8").splitlines()
                  if not l.strip().startswith("//"))
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", t))["highlight.regexes"]


def theme_markdown():
    # Chỉ tô node, link, value. Heading, content, code, chuỗi để Markdown của theme VS Code tự tô.
    return {
        NODE_ID:    R([{"color": "#C586C0"}, {}, {"color": "#E8D48A", "fontWeight": "bold"}]),
        NODE_TYPE:  R([{"color": "#C586C0"}, {}, {"color": "#4EC9B0", "fontWeight": "bold"}]),
        LINK_DEF:   R([{"color": "#C586C0"}, {}, {"color": "#A5ABB6", "fontWeight": "bold"}]),
        LINK_ATTR:  R([{}, {"color": "#C586C0"}, {}, {"color": "#A5ABB6"}, {}, {"color": "#E8D48A"}]),
        FROM_TO:    R([{}, {"color": "#C586C0"}, {"color": "#E8D48A"}, {"color": "#C586C0"}, {"color": "#E8D48A"}]),
        TYPE_ATTR:  R([{}, {}, {}, {"color": "#4EC9B0"}]),
        V_ANY:      R([{}, {}, {}, {"color": "#CE9178"}]),
        REF_INLINE: R([{"color": "#E8D48A"}]),
    }


def theme_python():
    # Dark+ của VS Code: node như def/class, link nổi bật, key như biến, value như literal Python.
    P = {"punct": "#808080", "kw": "#569CD6", "fn": "#DCDCAA", "cls": "#4EC9B0", "var": "#9CDCFE",
         "str": "#CE9178", "num": "#B5CEA8", "ctrl": "#C586C0", "rel": "#4FC1FF"}
    B, U = "bold", "underline"
    kv = lambda c: R([{"color": P["punct"]}, {"color": P["var"]}, {"color": P["punct"]}, {"color": c}])
    return {
        NODE_ID:    R([{"color": P["kw"], "fontWeight": B}, {}, {"color": P["fn"], "fontWeight": B, "textDecoration": U}]),
        NODE_TYPE:  R([{"color": P["kw"], "fontWeight": B}, {}, {"color": P["cls"], "fontWeight": B, "textDecoration": U}]),
        LINK_DEF:   R([{"color": P["ctrl"], "fontWeight": B}, {}, {"color": P["rel"], "fontWeight": B}]),
        LINK_ATTR:  R([{"color": P["punct"]}, {"color": P["ctrl"], "fontWeight": B}, {}, {"color": P["rel"], "fontWeight": B},
                       {"color": P["punct"]}, {"color": P["fn"]}]),
        FROM_TO:    R([{"color": P["punct"]}, {"color": P["ctrl"]}, {"color": P["fn"]}, {"color": P["ctrl"]}, {"color": P["fn"]}]),
        TYPE_ATTR:  kv(P["cls"]),
        V_NUM:      kv(P["num"]),
        V_BOOL:     kv(P["kw"]),
        V_REF:      kv(P["fn"]),
        V_STR:      kv(P["str"]),
        FRONT:      R([{"color": P["var"]}, {"color": P["punct"]}]),
        REF_INLINE: R([{"color": P["fn"], "fontWeight": B}]),
        COMMENT:    R([{"color": "#6A9955", "fontStyle": "italic"}]),
    }


THEMES = {
    "king":     ("Bảng màu gốc của KING web app: tô cả heading, chuỗi, comment.", theme_king),
    "markdown": ("Tôn trọng màu Markdown: chỉ tô @node, @link, link và value; heading/content/code giữ màu Markdown.", theme_markdown),
    "python":   ("Kiểu code Python (dark): @node như def/class (đậm, gạch chân), link nổi bật, key như biến, "
                 "value như literal Python (số, True/None, (ref), chuỗi); content giữ Markdown.", theme_python),
}


def main():
    for name, (desc, fn) in THEMES.items():
        regs = fn()
        for k in regs:
            try: re.compile(k, re.M)
            except re.error as e: print(f"  (bỏ qua kiểm tra Python cho 1 regex của {name}: {e})")
        (HERE / f"{name}.json").write_text(json.dumps(
            {"name": name, "description": desc, "regexFlags": "gm", "regexes": regs},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{name}.json: {len(regs)} regex")


if __name__ == "__main__":
    main()
