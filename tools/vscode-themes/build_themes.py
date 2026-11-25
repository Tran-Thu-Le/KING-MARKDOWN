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
REF_INLINE_03 = r"(?<=^|\s)@(?!node\b|link\b)[a-z0-9][a-z0-9-]*"      # old rule (still in .vscode/settings.json)
REF_INLINE = r"(?<=^|\s)(?<!//.*)@(?!(?:node|link|add|ask|block|print)\b)[a-z0-9][a-z0-9-]*"   # not in a // comment, not a kir command
COMMENT_03 = r"(?:^|(?<=\s))//[^\n]*"                                  # old rule (still in .vscode/settings.json)
COMMENT    = r'(?<=^(?:[^"\n]|"[^"\n]*")*)(?:^|(?<=\s))//[^\n]*'      # not inside a "string"
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

# ---------- kir v0.4 (kg: v0.4): same roles as the web app hlKing (book.js KING_TOK) ----------
# Only lines starting at column 0 with @add/@ask/@block/@print are commands; every other line is prose.
# Positions are found with (variable-length) lookbehinds: fine in JavaScript, checked in tests with the `regex` module.
KT    = r'(?:"(?:[^"\\n]|\.)*"|(?!//)[^\s"]+)'                      # one token: "string" or a bare word
KHEAD = rf"^@(?:add|ask)[ \t]+(?:{KT}[ \t]*=[ \t]*)?"                   # command + optional "p ="
KSTR, KNUM, KBOOL = r'("(?:[^"\\n]|\.)*")', r"(-?\d+(?:\.\d+)?)(?![\w.-])", r"(true|false|none)(?![\w.-])"
KVAR, KNAME = r"(\?[A-Za-z_][\w-]*|_(?![\w.-]))", r"([A-Za-z_][\w.-]*)"
KOUT  = r'(?:[^"/\n]|/(?!/)|"(?:[^"\\n]|\.)*")*'                     # rest of a command line, outside strings, before //
K_CMD     = r"^@(?:add|ask|block|print)\b"
K_DEFNAME = r"(?<=^@(?:add|ask)[ \t]+)([A-Za-z_][\w.-]*)([ \t]*)(=)"
K_SUBJ    = rf"(?<={KHEAD})(?:{KSTR}|{KNUM}|{KBOOL}|{KVAR}|{KNAME})"
K_REL     = rf"(?<={KHEAD}{KT}[ \t]+)(?:{KVAR}|((?!//)[^\s\"]+))"
K_OBJ     = rf"(?<={KHEAD}{KT}[ \t]+{KT}[ \t]+)(?:{KSTR}|{KNUM}|{KBOOL}|{KVAR}|{KNAME})"
K_BLOCK   = r"(?<=^@(?:block|print)[ \t]+)([A-Za-z_?][\w.-]*)"
K_COMMENT = rf"(?<=^@(?:add|ask|block|print)\b{KOUT})//[^\n]*"


def kir_rules(kw, node, link, val, num, boolc, var, com):
    tok = [val, num, boolc, var, node]
    return {
        K_CMD:     R([kw]),
        K_DEFNAME: R([node, {}, link]),
        K_SUBJ:    R(tok),
        K_REL:     R([var, link]),
        K_OBJ:     R(tok),
        K_BLOCK:   R([node]),
        K_COMMENT: R([com]),
    }


def theme_king():
    t = "\n".join(l for l in (REPO / ".vscode/settings.json").read_text(encoding="utf-8").splitlines()
                  if not l.strip().startswith("//"))
    regs = json.loads(re.sub(r",(\s*[}\]])", r"\1", t))["highlight.regexes"]
    regs = {({REF_INLINE_03: REF_INLINE, COMMENT_03: COMMENT}.get(k, k)): v for k, v in regs.items()}   # no @ref inside comments / on kir commands
    c = lambda h, **x: {"color": h, **x}
    regs.update(kir_rules(c("#C586C0"), c("#E8D48A"), c("#A5ABB6"), c("#CE9178"), c("#CE9178"), c("#CE9178"),
                          c("#4EC9B0"), c("#6A9955", fontStyle="italic")))
    return regs


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
        **kir_rules({"color": "#C586C0"}, {"color": "#E8D48A"}, {"color": "#A5ABB6"}, {"color": "#CE9178"},
                    {"color": "#CE9178"}, {"color": "#CE9178"}, {"color": "#4EC9B0"}, {"color": "#6A9955", "fontStyle": "italic"}),
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
        **kir_rules({"color": P["kw"], "fontWeight": B}, {"color": P["fn"]}, {"color": P["rel"], "fontWeight": B},
                    {"color": P["str"]}, {"color": P["num"]}, {"color": P["kw"]}, {"color": P["cls"]},
                    {"color": "#6A9955", "fontStyle": "italic"}),
    }


THEMES = {
    "king":     ("The KING web app's original palette: colours headings, strings and comments too.", theme_king),
    "markdown": ("Respects Markdown colours: only @node, @link, links and values are coloured; headings/content/code keep Markdown colours.", theme_markdown),
    "python":   ("Python code style (dark): @node like def/class (bold, underlined), links highlighted, keys like variables, "
                 "values like Python literals (numbers, True/None, (ref), strings); content keeps Markdown.", theme_python),
}


def main():
    for name, (desc, fn) in THEMES.items():
        regs = fn()
        for k in regs:
            try:
                import regex as rx; rx.compile(k, rx.M)               # supports variable-length lookbehind like JS
            except ImportError:
                try: re.compile(k, re.M)
                except re.error as e: print(f"  (skipped Python check of one regex in {name}: {e})")
        (HERE / f"{name}.json").write_text(json.dumps(
            {"name": name, "description": desc, "regexFlags": "gm", "regexes": regs},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{name}.json: {len(regs)} regex")


if __name__ == "__main__":
    main()
