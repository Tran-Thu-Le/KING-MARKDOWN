"""`ask`: so khớp hội các mẫu bộ ba (có ?biến) trên cạnh của đồ thị."""
from .parser import _builtin, classify, tokenize, value_id


def parse_patterns(text):
    pats, cur = [], []
    for t in tokenize(text) + [classify(",")]:
        if t.text == ",":
            if len(cur) != 3:
                raise ValueError("each pattern needs exactly 3 tokens")
            pats.append(cur)
            cur = []
        else:
            cur.append(t)
    return pats


def _term(t, stem, i):
    """-> ('var', tên) hoặc ('const', id/link)."""
    if t.kind == "var":
        return ("var", t.value)
    if t.kind == "anon":
        return ("var", f"_{i}")
    if t.kind == "eq":
        return ("const", "=")
    if t.kind == "name":
        return ("const", t.value)
    return ("const", value_id(t.value))


def _node_id(name, stem):
    if name.startswith("value:"):
        return name
    return f"kg:{name}" if _builtin(name) else f"{stem}:{name}"


def ask(graph, patterns):
    """graph: model.Graph; patterns: chuỗi `?x r o, ...` hoặc list Tok. Trả (cột, hàng)."""
    if isinstance(patterns, str):
        patterns = parse_patterns(patterns)
    stem = graph.stem
    compiled = []
    for i, (s, r, o) in enumerate(patterns):
        cs, cr, co = _term(s, stem, i), _term(r, stem, i), _term(o, stem, i)
        if cs[0] == "const":
            cs = ("const", _node_id(cs[1], stem))
        if co[0] == "const":
            co = ("const", _node_id(co[1], stem))
        compiled.append((cs, cr, co))
    cols = []
    for pat in compiled:
        for kind, v in pat:
            if kind == "var" and not v.startswith("_") and v not in cols:
                cols.append(v)

    def show(x):
        n = graph.nodes.get(x)
        if n is not None and "value" in n:
            return n["value"]
        if n is not None and n.get("label"):
            return n["label"]
        return x

    def match(term, val, env):
        kind, v = term
        if kind == "const":
            return env if v == val else None
        if v in env:
            return env if env[v] == val else None
        return {**env, v: val}

    envs = [{}]
    for cs, cr, co in compiled:
        nxt = []
        for env in envs:
            for s, o, k, _ in graph.edges:
                e = match(cs, s, env)
                if e is not None:
                    e = match(cr, k, e)
                if e is not None:
                    e = match(co, o, e)
                if e is not None:
                    nxt.append(e)
        envs = nxt
    rows, seen = [], set()
    for env in envs:
        row = tuple(show(env[c]) if c in env else None for c in cols)
        key = repr(row)
        if key not in seen:
            seen.add(key)
            rows.append(row)
    return cols, rows
