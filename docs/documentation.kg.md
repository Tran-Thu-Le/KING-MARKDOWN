---
kg: 0.2
use: king/schema, king/style
---

# KING Markdown Documentation @documentation

KING Markdown (Knowledge In Nodes & Graphs), language version 0.2. This document is itself a `.kg.md` file: open it with `king serve docs` to read it as a Graph, Tree, Book or Module. It uses the system schema and style (`use: king/schema, king/style`).

## 1. Goals and author @goals-and-author

@what: What is KING Markdown
- content: KING Markdown is a Markdown dialect for writing **knowledge graphs** as plain text. A `.kg.md` file is valid Markdown: headings are sections, lines starting with `@id` are nodes, and a few `- field:` lines attach metadata, content and typed links to a node.

  Data, schema (vocabulary and validation rules) and style (presentation rules) are written in the same syntax and read by a single parser. The result is a node-link graph in JSON that tools such as networkx, an HTML editor or Typst can use. *Knowledge is KING.*
  See also @goals, @file-structure.

@goals: Goals
- content: KING Markdown aims to:
  - Write knowledge once, as text, and read it as a graph, a tree, a book or nested modules.
  - Keep the text as the single source of truth: every action in the editor becomes a text edit, so files work with Git and any text editor.
  - Make prerequisites, part-whole structure and references explicit with typed links, so that a course or a body of knowledge can be checked and navigated.
  - Let teachers, students and AI assistants work on the same file: an `ask` field marks a node that is waiting to be written.
  - Validate knowledge with a schema and present it with style rules for HTML and Typst.
  - Stay small: the Python side uses only the standard library.
  See also @principles.

@principles: Design principles
- content: 
  - Text is the only source. The editor keeps no private data; graph actions are turned into text edits. Only node positions on screen are stored in the browser.
  - One syntax for three layers: data, schema and style are all `.kg.md`, so one parser reads all three.
  - One parser. The server and the editor never parse the language again; the browser receives parsed JSON.
  - No external dependencies. Python uses the standard library; the browser loads only vis-network from a CDN.

@author: Dr. Thu-Le Tran
- meta: important=true
- content: KING Markdown is designed and written by **Dr. Thu-Le Tran**: the language, the parser, the editor and this documentation.
  See also @what.

@tooling: Tools in this repository
- content: 
  - `king serve [folder]` opens the editor in the browser (local server, standard library only).
  - `king parse file.kg.md [-o graph.json] [--strict]` prints or writes JSON; `--strict` exits with code 1 on errors (for CI).
  - `king html file.kg.md [out.html]` writes a static, read-only page with the same interface.
  - Install with `pip install -e .`, or run without installing: `PYTHONPATH=src python -m king_markdown ...`.
  - Code lives in `src/king_markdown/` (parser, ops, server, cli, web); internals are described in `docs/architecture.md`.
  See also @cli, @views.

## 2. Basic syntax @basic-syntax

@file-structure: File structure
- content: A file has an optional frontmatter, then headings (sections) and nodes. A complete example:
  ```markdown
  ---
  kg: 0.2
  use: schema, style
  import: math, lop11.tiep-tuyen
  ---

  # Calculus @calculus

  @integral: Integral
  - meta: type=concept, role=Xuất
  - content: Area under a curve. Related to @derivative.
  - ask: Explain intuitively, with a picture.
  - link: part-of(analysis), needs(derivative, math.limit)
  - show: none
  ```
- link: needs(frontmatter, sections, nodes, fields, links)

@frontmatter: Frontmatter
- content: Optional block between two `---` lines at the top of the file. One key per line, values separated by commas.

  | Key | Meaning |
  |---|---|
  | `kg` | Language version, currently `0.2` |
  | `use` | Rule files applied to this file: `schema` reads `schema.kg.md`, `style` reads `style.kg.md` next to the file; `king/schema`, `king/style` read the system files |
  | `import` | Nodes from elsewhere: `math` imports a whole module (refer to `math.limit`), `lop11.tiep-tuyen` imports one node (refer to `tiep-tuyen`) |
  | `from M` | `from lop11: tiep-tuyen, dao-ham` imports two single nodes |

  Without `use:` (and without schema or style inside the file) nothing is validated and nothing is styled. The v0.1 keys `meta:` and `link:` in the frontmatter are ignored with a warning.
  See also @attach, @imports.

@sections: Sections
- content: 
  - Headings `#` to `######` are sections. Go down one level at a time; skipping a level gives a warning.
  - An `@id` at the end of a heading gives it an explicit, stable ID: `# Calculus @calculus`. Without it the ID is generated from the title and changes when the title changes, so do not link to it.
  - Plain text under a heading that does not belong to a node is a free note; it is not part of the graph.
  - Every node and section belongs to the nearest section above it. The parser generates a `contains` edge from the section to it.

@nodes: Nodes
- content: 
  - A line `@id: Title` opens a node; without a title the ID is used as title.
  - IDs use `a-z`, `0-9` and `-`, are unique in the file and **never change**: links refer to them.
  - A node ends at the next node or the next heading.
- link: needs(sections)

@fields: The five fields
- content: Under a node, each field is one line `- name: value`. There are exactly five fields; any other name is an error.

  | Field | Value |
  |---|---|
  | `meta` | `key=value` pairs separated by commas; values become `true` / `false`, numbers or strings; put strings with commas in quotes: `allow="role, important"` |
  | `content` | The text of the node. Following lines that are not fields are appended (indent them for readability); fenced code blocks are kept as they are. Long text can be wrapped in square brackets: everything from the opening bracket to the line that ends with the closing bracket is plain content, even lines that look like fields, nodes or headings (the brackets are removed). Same for `ask` |
  | `ask` | An instruction for an AI or a co-author. A node that still has `ask` is waiting to be written |
  | `link` | Typed links to other nodes |
  | `show` | `none`: the node is in the graph but not in the book |
  See also @links, @builtin-meta.
- link: needs(nodes)

@links: Links
- content: A link has a type and arguments; A is the node being written:
  ```text
  type(B)       edge A → B
  type!(B)      edge B → A   (reversed)
  type(B, C)    two edges
  type()        edge to the nearest enclosing section that has an explicit ID
  ```
  Example: `needs(derivative)`, `part-of(analysis)`, `export()`. Several links can share one line, separated by commas. An edge may be declared only once. Arguments may be IDs in the file, `module.id` for imported modules, or the short name of a single imported node.
  See also @generated-links, @schema.
- link: needs(fields)

@comments: Comments and text rules
- content: 
  - Two slashes start a comment only when preceded by a space (or at the start of the line), so URLs are safe.
  - Double percent signs mark a comment inside a line.
  - An `@` starts a reference only at the start of the text or after a space; `@` inside code (backticks or fenced blocks) is not a reference.
  - Fenced code blocks are kept unchanged.
  ```markdown
  - link: export()        // a comment until the end of the line
  - link: needs(a) %% a comment in the middle %%, see(b)
  ```

@naming: Naming conventions
- content: 
  - Field names and meta keys are **English verbs in the infinitive**, lower case, joined with `-`: `ask`, `show`, `link`, `contain`. Write `contain`, not `contains`, `containing` or `container`. New link types should follow the same rule.
  - Kept for compatibility: the fields `content` and `meta`, the key `type`, the link types `needs` and `part-of`, and the generated edges `contains` and `mention`.
  - The extension is `.kg.md`; the repository is `king-markdown`; the command is `king`.

## 3. Advanced syntax @advanced-syntax

@builtin-meta: Built-in meta keys
- content: Two meta keys belong to the language. They are always allowed, need no schema declaration and are not limited by `allow`.

  | Key | Value |
  |---|---|
  | `type` | The node type; with a schema it must be a declared `kind=type` |
  | `contain` | IDs of child nodes: `contain=a` or `contain="a, b"`. Each ID generates a `contain` edge from this node to the child, even across sections. Cycles are errors |
  ```markdown
  @analysis: Analysis
  - meta: type=group, contain="derivative, integral"
  ```
  See also @generated-links.
- link: needs(fields)

@generated-links: Generated edges
- content: The parser creates three kinds of edges; never write them by hand in `- link:`.
  - `contains`: from a section to each node and sub-section under it (the outline tree).
  - `mention`: from a node to every `@id` written in its `content` or `ask`.
  - `contain`: from a node to every ID in its `meta: contain=...`.
- link: needs(links, builtin-meta)

@schema: Schema
- content: A schema is a set of nodes whose meta has `kind`. Headings in a schema are only for reading.
  ```markdown
  @concept
  - meta: kind=type, allow="role, important"

  @role
  - meta: kind=key, values="Nạp | Xuất | Cầu | Phụ", required=true

  @important
  - meta: kind=key, value=bool

  @part-of
  - meta: kind=link, dag=true, to=group
  ```
  | `kind` | Options |
  |---|---|
  | `type` | `allow`: meta keys allowed for this type (empty means any key) |
  | `key` | `values="a \| b"` allowed values; `value=bool\|int\|number\|text`; `required=true` for types that allow the key |
  | `link` | `dag=true` forbids cycles; `from=` / `to=` required types of source and target |

  With a schema, undeclared node types, meta keys and link types are errors. A schema without link declarations accepts every link type, and `needs` and `part-of` are acyclic by default.
  See also @attach, @validation.
- link: needs(fields, links)

@style: Style
- content: A style rule is a node with `select` plus `html.*` and `typst.*` keys.
  ```markdown
  @section-look
  - meta: select="kind=section", html.shape=box, html.radius=0, html.color=lightgray

  @key-idea
  - meta: select="role=Xuất important=true", html.border=3, typst.frame=highlight

  @needs-look
  - meta: select="link=needs", html.color=red, html.width=2, html.arrows=both
  ```
  | Selector | Matches | Priority |
  |---|---|---|
  | `*` or empty | every node | 0 |
  | `kind=section`, `kind=node`, `kind=external` | by node kind | 1 |
  | `type=concept`, `role=Nạp`, `show=none`, `ask` | by meta or field (a bare name means "has a value"); combine with spaces | 10 per condition |
  | `#integral` | one node | 100 |
  | `link`, `link=needs` | every link / one link type | 0 / 10 |

  Higher priority wins; on equal priority the later rule wins.
  - `html.*` for nodes: `shape` (ellipse, box, circle, square, diamond, hexagon, triangle, star, dot, database, text), `color`, `border`, `border-color`, `dash`, `radius` (corner radius of a box, `0` = square corners), `font`, `font-size`, `font-color`, `size`, `opacity`.
  - `html.*` for links: `color`, `width`, `dash`, `arrows` (`to`, `from`, `both`, `none`), `opacity`.
  - Colors are CSS names (`red`, `green`, `blue`, `orange`, `purple`, `gray`, `lightblue`, …) or `#rrggbb`.
  - `typst.*` only names a format (`typst.frame=highlight`); the parser passes it to the JSON for a Typst template.
  See also @attach.
- link: needs(fields)

@attach: Three ways to attach schema and style
- content: The same knowledge graph can take its rules from three places (see `examples/hinh-thcs/hinh1.kg.md`, `hinh2.kg.md`, `hinh3.kg.md`):

  | Source | How |
  |---|---|
  | System | `use: king/schema, king/style`: the files in `templates/` shipped with KING Markdown |
  | Current folder | `use: schema, style`: `schema.kg.md` and `style.kg.md` next to the file |
  | Inside the file | Nodes with `kind=type/key/link` or `select=` (usually under `# Schema` and `# Style`); no `use:` needed |

  Rules inside the file come after rules from `use:`, so they win on equal priority. Definition nodes are not validated as data; the editor hides them from Graph and Book and shows them faded in Tree and Outline. The editor never writes to system files: formatting a file that uses `king/style` writes to the folder's `style.kg.md` and adds `style` to `use:`.
- link: needs(schema, style)

@imports: Imports and external nodes
- content: 
  - `import: math` makes every `math.x` a valid link target; `import: lop11.tiep-tuyen` or `from lop11: tiep-tuyen` makes `tiep-tuyen` usable by its short name.
  - Imported nodes appear as `kind=external` nodes in the graph; they are read-only.
  - A reference to a module that is not imported is an error.
- link: needs(frontmatter, links)

@validation: Validation rules
- content: 
  | Level | Rule |
  |---|---|
  | Error | Duplicate ID; field outside the five fields; malformed link |
  | Error | Link to a missing node or to a module that is not imported; edge declared twice; `contains`, `mention` or `contain` written by hand |
  | Error | `contain` pointing to a missing node, empty, or making a cycle |
  | Error (schema) | Undeclared meta key, node type or link type; key not in the type's `allow`; value outside `values` or of the wrong `value` type; missing `required` key |
  | Error (schema) | Source or target with the wrong type (`from` / `to`); cycle in a `dag` link type |
  | Error | File in `use:` not found |
  | Warning | Skipped heading level; unknown frontmatter key; unsupported `html.*`; unknown `kind` |
  See also @json.
- link: needs(schema)

@json: JSON output
- content: The parser outputs a networkx node-link graph. Every node and link has `line`, the line number in the source file, which the editor uses to edit the right place.
  ```json
  {
    "directed": true, "multigraph": true,
    "graph": { "file": "vidu.kg.md", "use": ["schema.kg.md", "style.kg.md"],
               "schema": { "types": {}, "keys": {}, "links": {} }, "dag": ["needs", "part-of", "contain"],
               "errors": [], "warnings": [] },
    "nodes": [ { "id": "derivative", "title": "Derivative", "kind": "node", "parent": "calculus", "line": 26,
                 "meta": { "type": "concept" }, "style": { "html": { "shape": "circle" }, "typst": {} } } ],
    "links": [ { "source": "derivative", "target": "analysis", "type": "part-of", "line": 29, "key": "part-of:0" } ]
  }
  ```
  ```python
  import json, networkx as nx
  G = nx.node_link_graph(json.load(open("graph.json", encoding="utf-8")), edges="links")
  ```
- link: needs(validation)

@views: The editor
- content: `king serve [folder]` opens a dark, VS Code-like editor: Explorer | text | view | Inspector, all resizable. Closing the last tab stops the server (use `--keep` to keep it running).
  - Views: **Graph** (Ctrl+1), **Tree** (Ctrl+2), **Book** (Ctrl+3), **Module** (Ctrl+4). Module draws nested groups: sections as rectangles, groups as rounded rectangles, content nodes as circles; each group can show or hide its children.
  - Inspector: edit the title, meta, content, ask, show, links and format of the selected node or link; every change is written back to the `.kg.md` file or to the style file.
  - Explorer: files of the folder (schema and style files can be opened and edited directly) and an outline of the current file.
  - Graph tools: Select, Add node, Connect (with a link type), Move to section, Fold.
  - One palette everywhere (text editor, Graph, Tree, Book, Module, Inspector): section titles blue; IDs, nodes and imported modules light yellow; link types orange; field names and meta keys pink; values after `=` brown; plain content white. The system style (`king/style`) uses the same colors for shapes and lines.
  - In Graph, plain nodes are ellipses and every label is drawn below its shape. Format › Labels hides node, section or link labels (also in Module).
  - Text shortcuts: Ctrl+/ toggles comments, Ctrl+C / Ctrl+X copy or cut the whole line when nothing is selected, Ctrl+V pastes it above, Alt+Z toggles word wrap, Ctrl+S saves.
  - Node shortcuts (in Graph, Tree, Book): Ctrl+C / Ctrl+X / Ctrl+V copy, cut and paste whole nodes (IDs are renamed when needed), Ctrl+/ comments out the selected nodes, Delete removes them, Ctrl+Z undoes.
- link: needs(tooling)

@cli: Command line
- content: 
  ```bash
  king serve examples/python-course          # editor; stops when the last tab closes
  king serve docs --keep --port 8800         # keep running, other port
  king parse file.kg.md -o graph.json        # JSON
  king parse file.kg.md --strict             # exit code 1 on errors (CI)
  king html  file.kg.md file.html            # static, read-only page
  python -m unittest discover -s tests       # tests
  ```
  See also @tooling.

## 4. Improvement plan @roadmap

@r-name-check: Check the name and choose a license
- ask: Priority high. Check that `king-markdown` is free on GitHub and PyPI, then choose a license (MIT or Apache-2.0) and add the `LICENSE` file.

@r-packaging: Ship templates inside the package and publish
- ask: Priority medium. `templates/` is found from the repository root, which only works with `pip install -e .`. Move the system schema and style into `src/king_markdown/templates/`, then publish to PyPI.
- link: needs(r-name-check)

@r-typst: Typst output
- ask: Priority high. A Typst template that reads the JSON and the `typst.*` style keys to typeset a book (frames for roles, hidden nodes with `show: none`).
  See also @style.

@r-layout: Hierarchical layout for Graph
- ask: Priority medium. Lay out the graph by the containment tree (sections above, nodes below) instead of the force layout, and optionally save node positions in a shared layout file so that the layout is the same on every machine.

@r-sections: Create sections from the graph
- ask: Priority medium. Today a section is created by typing a heading in the text. Add it to the Graph tools and to the Inspector.

@r-fold-edges: Reroute edges of folded nodes in Graph
- ask: Priority low. The Module view already attaches the edges of hidden children to the folded group; do the same in the Graph view.

@r-editor-safety: Safer edits and undo for rule files
- ask: Priority medium.
  - Undo also for edits written to `schema.kg.md` and `style.kg.md`.
  - Keep inline comments when the editor rewrites a `- link:` line.
  - Detect two tabs editing the same file and merge instead of overwrite.

@r-naming: Apply the naming convention to built-in names
- ask: Priority low. Open question: rename `needs` to `need`, and the generated `contains` edge to a name that cannot be confused with `contain`, with warnings for the old names.
  See also @naming.

@r-negation: Negated links
- ask: Priority low. Open question: a syntax such as `needs*(algebra)` for "does not need algebra", or a dedicated link type declared in the schema.
  See also @links.

@r-external: Editing imported nodes
- ask: Priority low. Open question: should the editor open and edit the source of an imported node, or keep imported nodes read-only?
  See also @imports.
