"""Export pure KIR (`@add token token token`) to networkx node-link JSON and RDF (Turtle).

Standalone on purpose: it reads only the KIR core (no sugar) and its JSON is
NOT the KING 0.3 JSON format. The two are not synchronised yet.

KIR line:   @add <subject> <link> <object>
token:      name | "string" | number | true | false
Other lines (prose, frontmatter, fences) are ignored. `//` starts a comment.

    python -m kir.export file.kg.md --json out.json
    python -m kir.export file.kg.md --rdf out.ttl
"""
import argparse
import json
import re
import sys

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[^\s"]+')
NUMBER = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?$")
NAME = re.compile(r"[A-Za-z0-9._-]+$")
DEFAULT_BASE = "urn:kir:"


class KirError(ValueError):
    pass


def _value(tok):
    """Token -> ('name', str) or ('literal', python value)."""
    if tok.startswith('"'):
        return "literal", json.loads(tok)
    if tok in ("true", "false"):
        return "literal", tok == "true"
    if NUMBER.match(tok):
        return "literal", float(tok) if re.search(r"[.eE]", tok) else int(tok)
    if NAME.match(tok):
        return "name", tok
    raise KirError(f"bad token: {tok}")


def _strip_comment(line):
    out, in_str, i = [], False, 0
    while i < len(line):
        c = line[i]
        if c == "\\" and in_str:
            out.append(line[i:i + 2]); i += 2; continue
        if c == '"':
            in_str = not in_str
        elif not in_str and line.startswith("//", i):
            break
        out.append(c); i += 1
    return "".join(out)


ADD = re.compile(r"@add\s")


def parse_line(raw):
    """One `@add` line -> (s, r, (kind, o)). Raises KirError without location."""
    toks = TOKEN.findall(_strip_comment(raw))
    if toks[0] != "@add" or len(toks) != 4:
        raise KirError("expected '@add token token token'")
    (ks, s), (kr, r), o = (_value(t) for t in toks[1:])
    if ks != "name" or kr != "name":
        raise KirError("subject and link must be names")
    return s, r, o


def parse_lines(text, fname="<text>"):
    """Return [(s, r, (kind, o), line)]. Only `@add` + whitespace at column 0, outside fences."""
    out, in_fence = [], False
    for n, raw in enumerate(text.splitlines(), 1):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not ADD.match(raw):
            continue
        try:
            out.append((*parse_line(raw), n))
        except KirError as e:
            raise KirError(f"{fname}:{n}: E2: {e}") from None
    return out


def parse(text, fname="<text>"):
    """Return a list of triples (s, r, (kind, o))."""
    return [t[:3] for t in parse_lines(text, fname)]


def to_networkx_json(triples):
    """node-link JSON, same shape as nx.node_link_data(MultiDiGraph, edges="links").

    Name objects become nodes + edges (key = link). Literal objects become
    node attributes: link -> value (a list if the same link repeats).
    """
    nodes, links, seen = {}, [], set()
    for s, r, (kind, o) in triples:
        nodes.setdefault(s, {})
        if kind == "name":
            nodes.setdefault(o, {})
            if (s, r, o) not in seen:          # graph is a set
                seen.add((s, r, o))
                links.append({"source": s, "target": o, "key": r})
        else:
            attrs = nodes[s]
            if r not in attrs:
                attrs[r] = o
            else:
                cur = attrs[r] if isinstance(attrs[r], list) else [attrs[r]]
                if o not in cur:
                    cur.append(o)
                attrs[r] = cur if len(cur) > 1 else cur[0]
    return {"directed": True, "multigraph": True, "graph": {"kir": "0.1"},
            "nodes": [{"id": n, **a} for n, a in nodes.items()], "links": links}


def to_networkx(triples):
    import networkx as nx
    return nx.node_link_graph(to_networkx_json(triples), edges="links")


def _lit(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return json.dumps(v, ensure_ascii=False)


def to_turtle(triples, base=DEFAULT_BASE):
    """RDF Turtle. Names -> IRIs `<base+name>`; strings/numbers/booleans -> literals."""
    lines, seen = [], set()
    for s, r, (kind, o) in triples:
        obj = f"<{base}{o}>" if kind == "name" else _lit(o)
        t = f"<{base}{s}> <{base}{r}> {obj} ."
        if t not in seen:
            seen.add(t); lines.append(t)
    return "\n".join(lines) + ("\n" if lines else "")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m kir.export", description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--json", metavar="OUT", help="write networkx node-link JSON ('-' = stdout)")
    ap.add_argument("--rdf", metavar="OUT", help="write RDF Turtle ('-' = stdout)")
    ap.add_argument("--base", default=DEFAULT_BASE, help=f"IRI prefix for names (default {DEFAULT_BASE})")
    a = ap.parse_args(argv)
    try:
        with open(a.file, encoding="utf-8") as f:
            from .compile import compile_text            # KING sugar -> pure KIR first
            triples = parse(compile_text(f.read(), a.file), a.file)
    except (OSError, KirError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr); return 1
    outs = []
    if a.json or not a.rdf:
        outs.append((a.json or "-", json.dumps(to_networkx_json(triples), ensure_ascii=False, indent=2) + "\n"))
    if a.rdf:
        outs.append((a.rdf, to_turtle(triples, a.base)))
    for path, data in outs:
        if path == "-":
            sys.stdout.write(data)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
