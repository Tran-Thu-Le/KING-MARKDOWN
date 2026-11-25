# KING Markdown

**KING** (Knowledge In Nodes & Graphs) is a Markdown extension for writing knowledge graphs (nodes, grouping trees, typed links) as plain text in `.kg.md` files. Data, schema and style use the same syntax, the parser emits networkx node-link JSON, and a local web editor shows each file as text, graph, tree, book or nested modules. The repo also contains **kir**, a small triple-based intermediate representation (`kg: v0.4`). *Knowledge is KING.*

```markdown
---
kg: 0.3
use:
- king/schema.node: Concept, Group
- king/schema.link: part-of, needs
---

# Calculus @calculus

@node integral
- label: Integral
- type: Concept
- link part-of: (calculus)
- link needs: (derivative)

Area under a curve; builds on @derivative.
```

## Layout

| Path | Contents |
|---|---|
| `src/king_markdown/` | KING Markdown 0.3: parser (`parser.py`, `values.py`, `legacy.py` for 0.1/0.2), text edits (`ops.py`, `ops03.py`), local server, CLI `king`, web editor (`web/`), starter `templates/` |
| `src/kir/` | KING IR `kg: v0.4`: parser, query, networkx backend, CLI `kir` |
| `tests/` | Test suite (`tests/kir/` for kir) |
| `examples/kir/` | `demo.kg.md`, its output `demo.json`, and one file per error code in `errors/` |
| `docs/` | [documentation.kg.md](docs/documentation.kg.md) (language reference), [architecture.md](docs/architecture.md) (internals) |
| `tools/` | Helper scripts (see below) |

## Install

Python 3.9+, no runtime dependencies (the browser loads `vis-network` from a CDN).

```bash
pip install -e .              # commands: king, kir
pip install -e .[networkx]    # optional: networkx backend for kir
```

Without installing: `PYTHONPATH=src python -m king_markdown ...` / `python -m kir ...`.

## kir (KING IR, `kg: v0.4`)

A file is Markdown prose plus command lines that start with `@`. Features:

- `@add s r o` adds an edge `s -r-> o`; `@add p = s r o` names the statement `p`.
- `@ask pattern[, pattern ...]` stores a query; patterns are triples with variables `?x`.
- `@block name` followed by a fenced code block (```` ```lang ````) stores raw code; the language must be known (`markdown`, `latex`, `typst`, `python`, `cpp`, `json`, or declared with `@add rust is-a language`).
- Names are `[A-Za-z0-9._-]`, case-insensitive (`Bob` = `bob`), and namespaced by file stem in the output (`demo:bob`). `_` is a fresh anonymous node; `a.b` refers to the object of edge `a b …`.
- Values: `"strings"` (with `\"` escapes), numbers, `true`, `false`, `none`.
- `//` starts a comment (not inside strings or code blocks). `@` in mid-line, or `\@` at line start, is plain text.
- Statements containing `?x` in `@add p = …` are stored as derived patterns, not evaluated.
- Output is networkx node-link JSON (directed multigraph, edge `key` = link name); `kir.backends.networkx` round-trips it.
- Diagnostics are `file:line: CODE: message`; a warning `W` flags names used only once (likely typos).

```text
---
kg: v0.4
---
@add alice friend-of bob
@add carol friend-of Bob
@add alice age 30
@ask ?x friend-of bob
```

```bash
kir run examples/kir/demo.kg.md -o out.json     # parse, write node-link JSON
kir ask examples/kir/demo.kg.md "?x friend-of bob"   # prints: ?x / alice / carol
kir open docs/documentation.kg.md --view book   # open the KING web app (needs king_markdown); --keep, --no-browser
```

| Code | Meaning |
|---|---|
| E1 | Missing or unsupported version (`kg: v0.4` required) |
| E2 | Syntax: wrong token count or position, unknown command, bad `@block` fence, undeclared language |
| E3 | Invalid or reserved name |
| E4 | Name defined twice |
| E5 | Attribute reference `a.b` with no edge `a b …` |
| E6 | Variable `?x` outside `@ask` or `@add p = …` |

Any error makes `kir` exit with code 1.

## KING Markdown 0.3

```bash
king serve docs                          # web editor; stops when the page closes (--keep to keep it)
king parse file.kg.md -o graph.json      # JSON for networkx; --strict exits 1 on errors
king html file.kg.md file.html           # standalone read-only page (opens in Book view)
```

Load the JSON with `nx.node_link_graph(data, edges="links")` (always pass `edges="links"`).

Editor: the menubar has an Explorer toggle (☰) and a Fullscreen button; two panes with tabs (Text, Graph, Tree, Book, Module); **Ctrl+S** saves, **Ctrl+1..4** switch views, **L** / **Shift+L** change and re-run the graph layout, **G** toggles the grid, **Ctrl+H** shows hidden nodes.

## Tools

| Script | Purpose |
|---|---|
| `tools/king_open.py <file\|folder> [--view book] [--keep]` | Open the editor directly on a file, on a free port; stops when the page closes |
| `tools/sync_vscode_highlight.py --list \| --theme <name> \| --off` | VS Code colour templates for `.kg.md` ([details](tools/vscode-themes/README.md)) |
| `tools/king_status.py` | Report CHANGELOG entries not yet seen |
| `tools/migrate_02_03.py` | Convert 0.2 files to 0.3 |

## Tests

```bash
python -m pytest tests -q
```

See [CHANGELOG.md](CHANGELOG.md) for what changed and [docs/documentation.kg.md](docs/documentation.kg.md) for the full language reference.
