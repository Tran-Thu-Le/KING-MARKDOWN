"""Trạng thái KING cho người dùng và Claude: phiên bản, mục changelog mới nhất, có gì mới từ lần xem trước.

  python tools/king_status.py            # in trạng thái (1–3 dòng) + mục changelog chưa xem
  python tools/king_status.py --ack      # đánh dấu đã xem (sau khi Claude đã đọc/báo người dùng)
  python tools/king_status.py --hook     # dùng cho SessionStart hook: chỉ in JSON khi có cập nhật chưa xem

"Đã xem" lưu ở ~/.claude/king-seen.json (dấu vân tay = version + tiêu đề mục changelog trên cùng + git HEAD).
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEEN = Path.home() / ".claude" / "king-seen.json"


def info():
    ver = re.search(r'^version\s*=\s*"([^"]+)"', (REPO / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    log = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    heads = [m.start() for m in re.finditer(r"^## ", log, re.M)]
    entries = [log[a:b].strip() for a, b in zip(heads, heads[1:] + [len(log)])]
    try:
        head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        head = "?"
    top = entries[0].splitlines()[0] if entries else ""
    h = hashlib.sha1((entries[0] if entries else "").encode()).hexdigest()[:10]
    return {"version": ver[1] if ver else "?", "head": head, "top": top, "hash": h, "entries": entries}


def unseen(i):
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}
    if seen.get("fp") == [i["version"], i["hash"], i["head"]]:
        return []
    old = seen.get("top")
    out = []
    for e in i["entries"]:
        if e.splitlines()[0] == old: break
        out.append(e)
    return out or i["entries"][:1]


def main(a):
    i = info()
    if "--ack" in a:
        SEEN.write_text(json.dumps({"fp": [i["version"], i["hash"], i["head"]], "top": i["top"]}), encoding="utf-8")
        print(f"acknowledged: KING {i['version']} · {i['top']} · {i['head']}"); return
    new = unseen(i)
    if "--hook" in a:
        if not new: return
        ctx = (f"[KING] Có cập nhật KING chưa xem (package {i['version']}, git {i['head']}). Mục mới trong "
               f"{(REPO / 'CHANGELOG.md').as_posix()}:\n\n" + "\n\n".join(new)[:3000] +
               "\n\nKhi phù hợp, báo người dùng ngắn gọn điểm mới (1–3 dòng), dùng skill `king` nếu cần giải thích, "
               f"rồi chạy `python {(REPO / 'tools/king_status.py').as_posix()} --ack`.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}, ensure_ascii=False))
        return
    print(f"KING package {i['version']} · git {i['head']} · latest: {i['top']}")
    print("Unseen:\n\n" + "\n\n".join(new) if new else "Nothing new since last check.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        main(sys.argv[1:])
    except Exception as e:                      # hook không bao giờ được làm hỏng phiên
        if "--hook" not in sys.argv: raise
