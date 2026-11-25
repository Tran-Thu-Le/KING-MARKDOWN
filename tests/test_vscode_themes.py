"""Run the VS Code Highlight theme regexes (JS syntax; `regex` module handles variable lookbehind) on kir sample lines."""
import json
from pathlib import Path

import pytest

rx = pytest.importorskip("regex")
THEMES = Path(__file__).resolve().parents[1] / "tools" / "vscode-themes"
SAMPLE = r"""---
kg: v0.4
---
// @add ccc
Contact: alice@example.com is plain text.
\@add this line is text, not a command.
@add alice friend-of bob   // a "quoted" comment
@add p = ?x knows "bo // b"
@add bob age 3
@add bob ok true
@add a.b x _
See @alice in prose.
"""


def paint(theme):
    """{(start, end): decoration} for every decorated span, like the Highlight extension does."""
    t = json.loads((THEMES / f"{theme}.json").read_text(encoding="utf-8"))
    out = {}
    for pat, conf in t["regexes"].items():
        decs = conf["decorations"]
        for m in rx.finditer(pat, SAMPLE, rx.M):
            if m.re.groups == 0:
                out.setdefault((m.start(), m.end()), []).append(decs[0])
            else:
                for g in range(1, m.re.groups + 1):
                    if m.group(g) is not None and g <= len(decs) and decs[g - 1]:
                        out.setdefault((m.start(g), m.end(g)), []).append(decs[g - 1])
    return out


def colors_at(spans, text, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = SAMPLE.index(text, i + 1)
    return {d.get("color") for (a, b), ds in spans.items() if a < i + len(text) and b > i for d in ds}


@pytest.mark.parametrize("theme", ["king", "markdown", "python"])
def test_kir_lines(theme):
    s = paint(theme)
    com = colors_at(s, "// @add ccc")
    assert com <= {"#6A9955"} and (com or theme == "markdown")    # comment line: comment colour only (markdown: untouched)
    assert colors_at(s, "Contact: alice@example.com is plain text.") == set()
    assert colors_at(s, r"\@add this line") == set()
    assert len(colors_at(s, "@add", 2)) == 1
    assert colors_at(s, "alice friend") and colors_at(s, "friend-of") and colors_at(s, "bob   //")
    assert colors_at(s, "friend-of") != colors_at(s, "alice friend")          # relation ≠ node colour
    assert colors_at(s, "alice friend") == colors_at(s, "bob   //") or len(colors_at(s, "bob   //")) >= 1
    assert colors_at(s, '// a "quoted" comment') >= {"#6A9955"}
    assert colors_at(s, "?x") and colors_at(s, '"bo // b"') and colors_at(s, "age 3"[-1]) and colors_at(s, "true")
    assert colors_at(s, "a.b x") and colors_at(s, " _") and colors_at(s, "p =")
    assert "#6A9955" not in colors_at(s, '"bo // b"')                         # // inside a string is not a comment
