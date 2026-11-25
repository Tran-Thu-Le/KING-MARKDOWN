"""KIR world engine: facts, statements, rules (k.then / k.else), Open/Closed world, logic, print.

    python -m kir.world file.kg.md     # outputs on stdout, `file:line: Ex: msg` on stderr

Pipeline: load the user file and, recursively, every file it imports with
`@add k.file k.import X` (X a name -> lib/X.kg.md, or a "path" relative to the
importing file; each file once; imported files contribute facts, statements
and rules, but not their world declaration or prints) -- compiled with
kir.compile, line map kept -> split meta (k.subject/k.link/k.object) from facts -> validate
statements -> flatten rules -> tier 0 set.equal closure + alias expansion ->
stratify by link -> naive fixpoint per stratum -> print `s r o: true|false|unknown`.

Logic for printing: compound statements `c = q1 k.and q2`, `c = q1 k.or q2`,
`n = k.not k.of q`. Closed world: Boolean (absent = false). Open world: Kleene
three-valued logic with F < U < T: and = min, or = max, not swaps T and F.
Any diagnostic stops the run before rules are applied (no outputs).
"""
import json
import sys
from pathlib import Path

from .compile import CompileError, compile_lines
from .export import KirError, parse_line

LIBDIR = Path(__file__).parent / "lib"
LIB = LIBDIR / "set.kg.md"
META = ("k.subject", "k.link", "k.object")
RULE = ("k.then", "k.else")
EQ = ("n", "set.equal")
USE = (("n", "k.file"), ("n", "k.import"))
COMB = ("k.and", "k.or")
NOT, OF = ("n", "k.not"), ("n", "k.of")
F, U, T = 0, 1, 2
WORD = {F: "false", U: "unknown", T: "true"}


class WorldError(Exception):
    pass


def _term(kind, v):
    """Hashable term; keeps bool / number / string / name apart (True != 1)."""
    if kind == "name":
        return ("n", v)
    return ("b" if isinstance(v, bool) else "s" if isinstance(v, str) else "f", v)


def _isvar(t):
    return t[0] == "n" and t[1].startswith("var.")


def _isk(t):
    return t[0] == "n" and t[1].startswith("k.")


def _show(t):
    if t[0] == "s":
        return json.dumps(t[1], ensure_ascii=False)
    if t[0] == "b":
        return "true" if t[1] else "false"
    return str(t[1])


def _resolve(x, fname):
    if x[0] == "n":
        return LIBDIR / f"{x[1]}.kg.md"
    if x[0] == "s":
        return Path(fname).parent / x[1]
    return None


def _load(text, fname, triples, seen, main=True):
    """Compile + parse one file into triples, following k.import imports (each file once)."""
    mine = []
    for kline, n, cmd in compile_lines(text, fname):
        if cmd:
            try:
                s, r, (k, o) = parse_line(kline)
            except KirError as e:
                raise WorldError(f"{fname}:{n}: E2: {e}") from None
            t = [("n", s), ("n", r), _term(k, o)]
            if not main:                                    # gen.N is per file: gen.<stem>.N in imports
                stem = Path(fname).name.split(".")[0]
                t = [("n", f"gen.{stem}.{x[1][4:]}") if x[0] == "n" and x[1].startswith("gen.") else x
                     for x in t]
            mine.append((*t, (fname, n)))
    for t in mine:
        if t[:2] == USE:
            p = _resolve(t[2], fname)
            if p is None or not p.is_file():
                raise WorldError(f"{fname}:{t[3][1]}: E17: cannot import {_show(t[2])}")
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                _load(p.read_text(encoding="utf-8"), str(p), triples, seen, main=False)
        elif not main and t[0][1] in ("k.file", "k.terminal"):
            continue                                        # world and prints are per file
        triples.append(t)


def _match(pat, K, th):
    """Yield every extension of binding th that makes pattern pat a fact of K."""
    for f in K:
        if _isvar(pat[1]) and _isk(f[1]):
            continue
        b = dict(th)
        for p, v in zip(pat, f):
            if _isvar(p):
                if b.setdefault(p, v) != v:
                    break
            elif p != v:
                break
        else:
            yield b


def _sub(pat, th):
    return tuple(th.get(t, t) for t in pat)


def _solve(conds, K, th):
    if not conds:
        yield th
        return
    (pos, pat), rest = conds[0], conds[1:]
    if pos:
        for b in _match(pat, K, th):
            yield from _solve(rest, K, b)
    elif next(_match(_sub(pat, th), K, th), None) is None:
        yield from _solve(rest, K, th)


def _vars(*ts):
    return {t for t in ts if _isvar(t)}


class World:
    def __init__(self):
        self.diags = []

    def err(self, loc, code, msg):
        self.diags.append(f"{loc[0]}:{loc[1]}: {code}: {msg}")

    def run(self, triples):
        meta, facts = {}, []
        for s, r, o, loc in triples:
            if r[1] in META:
                meta.setdefault(s, []).append((r[1], o, loc))
            elif _vars(s, r, o):
                self.err(loc, "E16", "a fact may not contain var.* (variables belong in statements)")
            else:
                facts.append((s, r, o, loc))
        st = {}
        for q, items in meta.items():
            got = {k: [o for kk, o, _ in items if kk == k] for k in META}
            if any(len(v) != 1 for v in got.values()) or got["k.subject"][0][0] != "n" \
                    or got["k.link"][0][0] != "n":
                self.err(items[0][2], "E15", f"statement {q[1]} needs exactly one "
                         "k.subject (name), k.link (name) and k.object")
            else:
                st[q] = tuple(got[k][0] for k in META)
        K = {f[:3] for f in facts}
        wf = [f for f in facts if f[:2] == (("n", "k.file"), ("n", "set.member"))]
        closed = [f[3] for f in wf if f[2] == ("n", "k.ClosedWorld")]
        opened = [f[3] for f in wf if f[2] == ("n", "k.OpenWorld")]
        if closed and opened:
            self.err(max(closed[0], opened[0]), "E13", "both k.ClosedWorld and k.OpenWorld declared")
        rules = [r for f in facts if f[1][1] in RULE for r in [self.flatten(f, st)] if r]
        rules = self.tier0(rules, K)
        prints = [f for f in facts if f[:2] == (("n", "k.terminal"), ("n", "k.print"))]
        for f in prints:
            bad = self.check(f[2], st)
            if bad:
                self.err(f[3], "E14", bad)
        strata = self.stratify(rules) if not self.diags else []
        if self.diags:
            return []
        for layer in strata:
            changed = True
            while changed:
                changed = False
                for conds, head, _ in layer:
                    for th in list(_solve(conds, K, {})):
                        t = _sub(head, th)
                        if t[0][0] == "n" and t not in K:   # literal subject: skip
                            K.add(t)
                            changed = True
        miss = F if closed else U
        return [self.text(f[2], st) + ": " + WORD[self.truth(f[2], st, K, miss)] for f in prints]

    @staticmethod
    def kind(q, st):
        s, r, o = st[q]
        return r[1] if r[1] in COMB else "k.not" if (s, r) == (NOT, OF) else None

    def check(self, q, st, stack=()):
        """Message if q cannot be printed (not a statement, variables, cycle), else None."""
        if q not in st:
            return f"k.print needs a statement: {_show(q)}"
        if q in stack:
            return f"compound statement {_show(q)} refers to itself"
        k = self.kind(q, st)
        if k is None:
            return None if not _vars(*st[q]) else f"k.print needs a statement without variables: {_show(q)}"
        s, _, o = st[q]
        for part in ([s, o] if k in COMB else [o]):
            bad = self.check(part, st, stack + (q,))
            if bad:
                return bad
        return None

    def truth(self, q, st, K, miss):
        k, (s, _, o) = self.kind(q, st), st[q]
        if k == "k.and":
            return min(self.truth(s, st, K, miss), self.truth(o, st, K, miss))
        if k == "k.or":
            return max(self.truth(s, st, K, miss), self.truth(o, st, K, miss))
        if k == "k.not":
            return T - self.truth(o, st, K, miss)
        return T if st[q] in K else miss

    def text(self, q, st, top=True):
        k, (s, _, o) = self.kind(q, st), st[q]
        if k in COMB:
            t = f"{self.text(s, st, False)} {k[2:]} {self.text(o, st, False)}"
        elif k == "k.not":
            return "not " + self.text(o, st, False)
        else:
            t = " ".join(map(_show, st[q]))
        return t if top else f"({t})"

    def flatten(self, f, st):
        """`A k.then B` / `A k.else B` -> ([(positive, pattern)], conclusion, loc)."""
        (a, r, b), loc, conds, seen = f[:3], f[3], [], set()
        while True:
            if a not in st or b not in st or b in seen:
                self.err(loc, "E14", f"{r[1]} needs statements on both sides")
                return None
            seen.add(b)
            if self.kind(a, st):
                self.err(loc, "E14", f"compound statement {a[1]} cannot be a rule condition "
                         "(use nested k.then for and, two rules for or, k.else for not)")
                return None
            conds.append((r[1] == "k.then", st[a]))
            if st[b][1][1] not in RULE:
                break
            a, r, b = st[b]
        head = st[b]
        if self.kind(b, st):
            self.err(loc, "E14", f"compound statement {b[1]} cannot be a rule conclusion")
            return None
        if _isk(head[1]) or (head[1] == EQ and loc[0] != str(LIB)):
            self.err(loc, "E14", f"a rule may not conclude link {head[1][1]}")
            return None
        if _isvar(head[1]) and not any(p and c[1] == EQ and head[1] in (c[0], c[2]) for p, c in conds):
            self.err(loc, "E14", "a rule conclusion may not have a variable link")
            return None
        return conds, head, loc

    def tier0(self, rules, K):
        """set.equal closure (written facts + symmetry), expand alias rules, check safety."""
        eq = {(s, o) for s, r, o in K if r == EQ and s[0] == o[0] == "n"}
        eq |= {(o, s) for s, o in eq}
        K |= {(s, EQ, o) for s, o in eq}
        out = []
        for conds, head, loc in rules:
            if head[1] == EQ:
                continue                                    # lib symmetry: done above
            if not _isvar(head[1]):
                out.append((conds, head, loc))
                continue
            i = next(i for i, (p, c) in enumerate(conds) if p and c[1] == EQ and head[1] in (c[0], c[2]))
            c = conds[i][1]
            for a, b in sorted(eq):
                if _isk(a) or _isk(b):
                    continue                                # never alias to k.*
                th = {c[0]: a, c[2]: b}
                rest = [(p, _sub(x, th)) for p, x in conds[:i] + conds[i + 1:]]
                out.append((rest, _sub(head, th), loc))
        for conds, head, loc in out:
            pos = set().union(*[_vars(*c) for p, c in conds if p])
            neg = set().union(*[_vars(*c) for p, c in conds if not p])
            hv = _vars(*head)
            bad = (hv - pos) | ((neg & hv) - pos)
            if bad or _isvar(head[1]):
                names = ", ".join(sorted(t[1] for t in bad)) or head[1][1]
                self.err(loc, "E11", f"unsafe variable(s): {names}")
        return out

    def stratify(self, rules):
        """Strata by link; a negative edge inside a cycle -> E12."""
        links = {h[1] for _, h, _ in rules} | {c[1] for cs, _, _ in rules for _, c in cs}
        links = {l for l in links if not _isvar(l)}
        level, top = dict.fromkeys(links, 0), len(links)
        for _ in range(top + 2):
            changed = False
            for conds, h, loc in rules:
                for pos, c in conds:
                    for l in (links if _isvar(c[1]) else [c[1]]):
                        if level[h[1]] < level[l] + (not pos):
                            level[h[1]] = level[l] + (not pos)
                            changed = True
                            if level[h[1]] > top:
                                self.err(loc, "E12", "negation (k.else) inside a dependency cycle")
                                return []
            if not changed:
                break
        return [[r for r in rules if level[r[1][1]] == k] for k in sorted(set(level.values()))]


def run_text(text, fname="<text>"):
    """Compile + run; returns (outputs, diagnostics)."""
    triples, seen = [], set()
    try:
        main = Path(fname)
        if main.is_file():
            seen.add(str(main.resolve()))
        _load(text, fname, triples, seen)
    except (WorldError, CompileError) as e:
        return [], [str(e)]
    w = World()
    return w.run(triples), w.diags


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m kir.world file.kg.md", file=sys.stderr)
        return 2
    try:
        text = Path(argv[0]).read_text(encoding="utf-8")
    except OSError as e:
        print(e, file=sys.stderr)
        return 1
    out, diags = run_text(text, argv[0])
    for line in out:
        print(line)
    for d in diags:
        print(d, file=sys.stderr)
    return 1 if diags else 0


if __name__ == "__main__":
    sys.exit(main())
