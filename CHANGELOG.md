# Changelog

This file is the main record of what is new in KING. `tools/king_status.py` compares the **top entry** with the last one seen and reports new entries.

When changing KING:
1. Add a new entry **at the top**: `## <version or Unreleased> (YYYY-MM-DD)`.
2. Group items: **Language**, **API/CLI**, **Editor/VS Code**, **Docs**.
3. Syntax changes also update `docs/documentation.kg.md` and the examples; cite the section id (e.g. `@basic-syntax`).
4. State **compatibility**: do old files still work, what must change.

## Unreleased (2026-11-25)
**API/CLI**
- New package `src/kir/` (KING IR, `kg: v0.4`): triple statements `@add [p =] s r o`, `@ask`, `@block` with fenced code, `_` anonymous nodes, `?x` variables, `a.b` attribute references, string/number/boolean/none values, `//` comments. Errors E1–E6 reported as `file:line`, plus a warning for names used once. Pattern matching for `@ask`; networkx node-link backend (lossless round-trip). CLI: `kir run f.kg.md -o out.json`, `kir ask f.kg.md "?x friend-of bob"`. Example in `examples/kir/`, tests in `tests/kir/`. Independent of `king_markdown`.
- `king html` pages open in the Book view (unless `?view=` is given).
- `kir open <file|folder> [--view ...] [--keep] [--no-browser]` opens the KING web app (shared `king_markdown.open.open_in_browser`, also used by `tools/king_open.py`).
- Parser: an unsupported `kg:` version is now an error instead of being read as 0.3. Supported: 0.1, 0.2 (legacy), 0.3.
- User-facing text is now English: CLI help/output (`king`, `kir`, `tools/*.py`), parser and kir diagnostics (E1–E6), server messages, and web app UI labels. Code comments unchanged. Scripts matching on the old Vietnamese messages must be updated.
- networkx: read JSON with `nx.node_link_graph(data, edges="links")` (NetworkX 3.6 changed the default); round-trip test added.

**Editor/VS Code**
- Graph edits on `kg: 0.3` files now write 0.3 syntax (`@node id` + `- label:`, `- link rel: (a, b)`) instead of 0.2 syntax. New module `ops03.py`; the server picks it by the file's `kg:` (0.1/0.2 still use `ops.py`). Supported: add_node, rename (node and section), add_link, delete_link, delete_node (also removes links to it), move_node, comment_nodes. Not yet on 0.3 (refused, nothing written): set_style, schema_add, set_meta, set_field, paste_nodes.
- New files are created as `kg: 0.3`.
- Menubar: Explorer collapse/expand button (☰, Ctrl+B, state remembered) and a Fullscreen toggle (Esc exits), in the live app and static pages.
- `tools/king_open.py <file.kg.md | folder>` opens the editor on a file, picks a free port, stops when the page closes (`--keep` to keep it).
- Three VS Code colour templates for `.kg.md` (`king`, `markdown`, `python`) via `tools/sync_vscode_highlight.py --list | --theme <name> | --off`; see `tools/vscode-themes/README.md`.

**Docs**
- This changelog and `tools/king_status.py`.

Compatibility: 0.2 and 0.3 files read and write as before; files declaring an unknown `kg:` now report an error. The 0.3 web app does not read `kg: v0.4` files (use `kir`).

## 0.3.0 (2026-11-11), commit `dd09173`
**Language**: KING Markdown `kg: 0.3`: `@node`, `- attr: value`, `- link rel: (x)`, schema and style written in KING itself, `use:` / `import:`, `hide:`. See `docs/documentation.kg.md` (`@basic-syntax`, `@advanced-syntax`).
**API/CLI**: `king serve | parse [--strict] | html`.
**Editor**: web app with Text/Graph/Tree/Book/Module views, graph layouts, saved node positions.

## 0.2 (2026-11-08), commit `0319a68`
First version (the old parser now lives in `src/king_markdown/legacy.py`: style files, ops).
