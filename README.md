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
| `src/kir/` | KING IR `kg: v0.4`: compiler (`compile.py`), world engine (`world.py`), export (`export.py`), `lib/set.kg.md`, CLI `kir`; `parser.py`/`query.py`/`model.py`/`backends/` are the legacy 0.4.0 parser |
| `tests/` | Test suite (`tests/kir/` for kir) |
| `examples/kir/` | `world-*.kg.md`, `logic-*.kg.md` with `*.expected.txt` outputs; `demo.kg.md` and `errors/` use the legacy 0.4.0 syntax |
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

KIR has one command, `@add subject link object`, at column 0 (tokens: names with `.` namespaces, `"strings"`, numbers, `true`/`false`; `//` comments). KING sugar compiles to it: `@add q = s r o` (named statement, not asserted), `@print(...)` with `and`/`or`/`not`, `@world closed|open`, `@import set` / `@import "file.kg.md"`. Rules use `k.then` / `k.else`; the `set` library adds `set.member`, `set.subset`, `set.equal`. Open world prints `true`/`unknown`, closed world `true`/`false`.

```king
@import set
@add Scientist set.subset Person
@add newton set.member Scientist
@print(newton set.member Person)      // newton set.member Person: true
```

```bash
kir run file.kg.md                        # run, print results; errors as file:line: Ex: msg
kir compile file.kg.md                    # show the pure KIR
kir export file.kg.md --json out.json --rdf out.ttl
kir view file.kg.md                       # KING web app with Run button and OUTPUT panel
```

Tutorial: [`docs/kir.kg.md`](docs/kir.kg.md). Since 0.4.1 `kir run` runs the world engine; the 0.4.0 JSON export is `kir export`, and `kir ask` / `@ask` / `@block` / `?x` (legacy parser) are no longer available from the CLI.

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
