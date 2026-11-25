"""Bật/tắt template màu KING (.kg.md) trong settings NGƯỜI DÙNG của VS Code (áp cho mọi folder).
Cần extension Highlight (fabiospampinato.vscode-highlight). Tài liệu: tools/vscode-themes/README.md

  python tools/sync_vscode_highlight.py --list            # các template + template đang bật
  python tools/sync_vscode_highlight.py --theme python    # bật template (king | markdown | python)
  python tools/sync_vscode_highlight.py --off             # tắt màu KING
  python tools/sync_vscode_highlight.py                   # bật lại template đang dùng (mặc định: king)
  python tools/sync_vscode_highlight.py --theme X --dry-run

Template nằm ở tools/vscode-themes/<tên>.json (sinh bởi build_themes.py). Script chèn/thay khối giữa
'// >>> KING theme=<tên>' và '// <<< KING' trong "highlight.regexes", giữ nguyên phần còn lại (cả comment),
sao lưu settings.json.bak trước khi ghi. Sau khi đổi: Developer: Reload Window nếu màu chưa đổi ngay.
"""
import json, os, re, shutil, sys
from pathlib import Path

THEMES = Path(__file__).resolve().parent / "vscode-themes"
USER = Path(os.environ["APPDATA"]) / "Code" / "User" / "settings.json"
BEGIN_RE = re.compile(r"[ \t]*// >>> KING[^\n]*\n.*?// <<< KING[^\n]*\n", re.S)
IND = " " * 8


def themes():
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(THEMES.glob("*.json"))}


def current(s):
    m = re.search(r"// >>> KING theme=([\w-]+)", s)
    return m[1] if m else ("king" if "// >>> KING" in s else None)


def block(name, t):
    items = []
    for k, v in t["regexes"].items():
        body = json.dumps({k: v}, ensure_ascii=False, indent=4)[1:-1].strip("\n")
        items.append("\n".join(IND + l[4:] for l in body.splitlines()))
    head = f"{IND}// >>> KING theme={name} — {t['description']} (change: KING-markdown/tools/sync_vscode_highlight.py)\n"
    return head + ",\n".join(items) + f",\n{IND}// <<< KING\n"


def write(s):
    shutil.copy(USER, USER.with_suffix(".json.bak"))
    USER.write_text(s, encoding="utf-8")


def main(a):
    s = USER.read_text(encoding="utf-8"); ts = themes(); cur = current(s)
    if "--list" in a:
        for n, t in ts.items():
            print(f"{'*' if n == cur else ' '} {n:9} {t['description']}")
        print(f"active: {cur or 'off'}"); return
    if "--off" in a:
        if cur is None: print("already off"); return
        write(BEGIN_RE.sub("", s)); print(f"turned off (was: {cur})"); return
    name = a[a.index("--theme") + 1] if "--theme" in a else (cur or "king")
    if name not in ts: sys.exit(print(f"no template '{name}'. Available: {', '.join(ts)}") or 1)
    blk = block(name, ts[name])
    if "--dry-run" in a: print(blk); return
    if cur is not None:
        s = BEGIN_RE.sub(lambda _: blk, s, count=1)
    elif (m := re.search(r'"highlight\.regexes"\s*:\s*\{\n', s)):
        s = s[:m.end()] + blk + s[m.end():]
    else:
        i = s.rstrip().rfind("}")
        s = s[:i].rstrip() + ',\n    "highlight.regexes": {\n' + blk + "    }\n" + s[i:]
    flags = ts[name].get("regexFlags", "gm")
    if re.search(r'"highlight\.regexFlags"\s*:', s):
        s = re.sub(r'"highlight\.regexFlags"\s*:\s*"[^"]*"', f'"highlight.regexFlags": "{flags}"', s)
    else:
        s = s.replace('"highlight.regexes"', f'"highlight.regexFlags": "{flags}",\n    "highlight.regexes"', 1)
    write(s); print(f"enabled template '{name}' ({len(ts[name]['regexes'])} regexes){'' if cur in (None, name) else f', replacing {cur}'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
