"""Compile KING sugar to pure KIR.

    @add q = s r o   ->  @add q k.subject s / @add q k.link r / @add q k.object o
    @print(q)        ->  @add k.terminal k.print q
    @print(s r o)    ->  statement gen.N (3 lines) + @add k.terminal k.print gen.N
    @world closed    ->  @add k.file set.member k.ClosedWorld   (open -> k.OpenWorld)
    @import set      ->  @add k.file k.import set     (@import "schema.kg.md" -> a path;
                         @use is accepted as an alias, @import is the style)
    @print(E)        ->  E built from `s r o` triples or statement names with
                         and / or / not and parentheses (not > and > or); every
                         compound gets a gen.N statement:
                         gen.N = A k.and B / A k.or B / k.not k.of A

Pure KIR lines and non-command lines are kept unchanged (compile(KIR) == KIR).
Line map: `compile_lines` returns [(kir_line, source_line, is_command)], so every
emitted KIR line remembers the ORIGINAL source line it came from; `compile_text`
just joins the KIR lines. Malformed sugar raises CompileError('file:line: E2: msg').

    python -m kir.compile file.kg.md
"""
import re
import sys

from .export import ADD, TOKEN, _strip_comment

PRINT = re.compile(r"@print(\(|\s|$)")
WORLD = re.compile(r"@world(\s|$)")
USE = re.compile(r"@(?:import|use)(\s|$)")
EXPR = re.compile(r'"(?:[^"\\]|\\.)*"|[()]|[^\s"()]+')
OPS = ("and", "or", "not", "(", ")")


class CompileError(ValueError):
    pass


def compile_lines(text, fname="<text>"):
    out, gen, fence = [], 0, False
    for n, raw in enumerate(text.splitlines(), 1):
        def err(msg):
            raise CompileError(f"{fname}:{n}: E2: {msg}")

        def emit(*lines):
            out.extend((l, n, True) for l in lines)

        def stmt(q, s, r, o):
            emit(f"@add {q} k.subject {s}", f"@add {q} k.link {r}", f"@add {q} k.object {o}")

        if raw.lstrip().startswith("```"):
            fence = not fence
        if fence or raw.lstrip().startswith("```"):
            out.append((raw, n, False)); continue
        body = _strip_comment(raw).strip()
        if PRINT.match(raw):
            m = re.fullmatch(r"@print\((.*)\)", body)
            toks = EXPR.findall(m.group(1)) if m else []
            if not toks:
                err("expected '@print(q)', '@print(s r o)' or '@print(A and B)'")
            pos = [0]

            def peek():
                return toks[pos[0]] if pos[0] < len(toks) else None

            def take():
                pos[0] += 1
                return toks[pos[0] - 1]

            def new(s_, r_, o_):
                nonlocal gen
                gen += 1
                stmt(f"gen.{gen}", s_, r_, o_)
                return f"gen.{gen}"

            def p_or():
                a = p_and()
                while peek() == "or":
                    take(); a = new(a, "k.or", p_and())
                return a

            def p_and():
                a = p_not()
                while peek() == "and":
                    take(); a = new(a, "k.and", p_not())
                return a

            def p_not():
                if peek() == "not":
                    take()
                    return new("k.not", "k.of", p_not())
                if peek() == "(":
                    take(); a = p_or()
                    if take_if(")") is None:
                        err("missing ')'")
                    return a
                atom = []
                while peek() is not None and peek() not in OPS:
                    atom.append(take())
                if len(atom) == 1:
                    return atom[0]
                if len(atom) == 3:
                    return new(*atom)
                err("each operand must be a statement name or 's r o'")

            def take_if(t):
                return take() if peek() == t else None

            top = p_or()
            if peek() is not None:
                err(f"unexpected '{peek()}'")
            emit(f"@add k.terminal k.print {top}")
        elif USE.match(raw):
            toks = TOKEN.findall(body)
            if len(toks) != 2:
                err("expected '@import name' or '@import \"path.kg.md\"'")
            emit(f"@add k.file k.import {toks[1]}")
        elif WORLD.match(raw):
            toks = body.split()
            if len(toks) != 2 or toks[1] not in ("closed", "open"):
                err("expected '@world closed' or '@world open'")
            emit(f"@add k.file set.member k.{'Closed' if toks[1] == 'closed' else 'Open'}World")
        elif ADD.match(raw):
            toks = TOKEN.findall(body)
            if "=" in toks:
                if len(toks) != 6 or toks[2] != "=":
                    err("expected '@add q = s r o'")
                stmt(toks[1], *toks[3:])
            else:
                emit(raw)
        else:
            out.append((raw, n, False))
    return out


def compile_text(text, fname="<text>"):
    return "\n".join(l for l, _, _ in compile_lines(text, fname)) + ("\n" if text.endswith("\n") else "")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m kir.compile file.kg.md", file=sys.stderr); return 2
    try:
        with open(argv[0], encoding="utf-8") as f:
            sys.stdout.write(compile_text(f.read(), argv[0]))
    except (OSError, CompileError) as e:
        print(e, file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
