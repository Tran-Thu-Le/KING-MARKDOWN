---
kg: 0.3
use:
- king/schema.node: Concept, Group
- king/schema.link: needs, part-of
- king/style
---

# KING Markdown Documentation @documentation

KING Markdown (Knowledge In Nodes & Graphs), language version 0.3. This document is itself a `.kg.md` file: open it with `king serve docs` to read it as a Graph, Tree, Book or Module.

## 1. Goals and author @goals-and-author

@node what
- label: What is KING Markdown
- type: Concept

KING Markdown is a Markdown dialect for writing **knowledge graphs** as plain text. A `.kg.md` file is valid Markdown: headings are sections, `@node` and `@link` blocks declare nodes and links, and the `- key: value` lines right under a block are its attributes.

The parser turns a file into a node-link graph in JSON that networkx, the HTML editor or Typst can use. *Knowledge is KING.* See also @goals, @blocks.

@node goals
- label: Goals
- type: Concept

- Write knowledge once, as text, and read it as a graph, a tree, a book or nested modules.
- Keep the text as the single source of truth, so files work with Git and any text editor.
- Make prerequisites, part-whole structure and references explicit with typed links.
- Let teachers, students and AI assistants work on the same file: an `ask` attribute marks a node waiting to be written.
- Stay small: the Python side uses only the standard library.

@node author
- label: Dr. Thu-Le Tran
- important: true

KING Markdown is designed and written by **Dr. Thu-Le Tran**: the language, the parser, the editor and this documentation.

@node tooling
- label: Tools in this repository

- `king serve [folder]` opens the editor in the browser.
- `king parse file.kg.md [-o graph.json] [--strict]` prints or writes JSON; `--strict` exits with code 1 on errors.
- `king html file.kg.md [out.html]` writes a static, read-only page.
- Run without installing: `PYTHONPATH=src python -m king_markdown ...`.

## 2. Basic syntax @basic-syntax

@node blocks
- label: Blocks
- type: Concept

A file is cut into blocks:

| Block | Starts with | Ends |
|---|---|---|
| Section | `#` … `######` | before a heading of the same or a higher level, or at the end of the file |
| Node | `@node name` at column 1 | before the next `@` at column 1, the next heading, or the end of the file |
| Link | `@link name` at column 1 | same as a node |

The opening line has no `:` and no label. `@` inside a fenced code block or an indented `@` does not open a block.

@node attributes
- label: Attributes and content
- type: Concept
- link needs: (blocks)

The `- ` lines right under the opening line (or under a heading) are the **attributes** of the block. After a blank line comes the **content**: plain Markdown until the end of the block, including list items.

```markdown
@node circle
- label: Circle
- type: Concept
- role: Output
- link needs: (disc)

The set of points at distance R from a centre O.
- Area: S = πR².
```

`- label:` is only the text shown to readers. Attributes are free: any `- key: value` is allowed.

@node names
- label: Names and types
- type: Concept
- link needs: (blocks)

- `@node circle` declares the **name** `circle`, like a variable in a program. Its scope is the file. There is no separate ID: links and references use the name.
- Node names and link names are lower case with hyphens: `part-of`, `circle-area`.
- Type names start with a capital letter: `Concept`, `Group`. `@node Concept` declares a node type instead of a node.
- A section can be named at the end of its heading: `# Calculus @calculus`. Without a name, one is generated from the title (it changes when the title changes).

@node node-links
- label: Links inside a node
- type: Concept
- link needs: (attributes)

`- link needs: (a, b)` creates the edges `this → a` and `this → b` of type `needs`. Read it as "the **needs** of this node are a and b".

@node link-blocks
- label: Link types and inverse
- type: Concept
- link needs: (node-links)

```markdown
@link author
- label: Author
- inverse: works

@node kieu
- label: The Tale of Kieu
- link author: (nguyen-du)

@node nguyen-du
- label: Nguyen Du
- link works: (kieu)
```

`- inverse: works` lets a node write the link from the other side. `- link works: (kieu)` on `nguyen-du` is stored as `kieu → nguyen-du` of type `author`. The graph keeps only the original direction, and duplicate links are merged into one edge.

A `@link` block can also list links directly: `- from a to (b, c)`.

@node values
- label: Values
- type: Concept
- link needs: (attributes)

| Type | Example |
|---|---|
| Num | `3`, `-2`, `0.5` |
| Bool | `true`, `false` |
| None | `none` |
| Str | `free text`, `"with, commas"` |
| List | `(a, b)`; `(a)` is a list of one |
| Dict | `(w=3, h=2)` |
| Content | `[ ... ]`, raw text such as Typst, LaTeX, Markdown or Python; may span several lines |
| code | `` `f(x) // not a comment` `` |

`//` starts a comment when it is at the start of a line or after a space, outside quotes and backticks, so `https://…` is safe.

@node frontmatter
- label: Frontmatter and imports
- type: Concept
- link needs: (names)

```markdown
---
kg: 0.3
use:
- king/schema.node: Concept, Group
- king/schema.link: part-of, needs
- king/style
import: math, lop11.tangent
---
```

- Node types and link types must be imported (or declared in the file). Using a name that is not imported is an error.
- `- schema` without `.node:` / `.link:` imports every type of `schema.kg.md` in the same folder. `king/…` names the system files.
- `import: math` makes `math.limit` a valid target; `import: lop11.tangent` makes `tangent` usable by its short name.

## 3. Advanced syntax @advanced-syntax

@node schema-files
- label: Schema files
- type: Concept
- link needs: (names, link-blocks)

A schema is a `.kg.md` file of declarations:

```markdown
@node Concept
- label: Concept

@link needs
- label: Needs
- inverse: needed-by
- dag: true
```

`- dag: true` forbids cycles for that link type. `templates/schema.kg.md` declares the node types `Concept`, `Group`, `Example` and `Warning`. Declarations can also be written inside a data file.

@node sections-text
- label: Sections and generated edges
- type: Concept
- link needs: (blocks)

- Text under a heading, before the first `@` block, is the content of the section itself.
- The parser generates `contains` edges from a section to each node and sub-section under it.
- `@name` in content (outside code) generates a `mention` edge.
- `contains` and `mention` are never written by hand.

@node hide
- label: Hiding nodes and links
- type: Concept
- link needs: (attributes, sections-text)

`- hide:` removes a node, a section or a link type from some views, so you can focus on one part of a large file.

```markdown
# Exercises
- hide: graph, module      // only in Graph and Module

@node draft
- hide: all                // every view (true means the same)

@link mention-of
- hide: book               // every link of this type
```

- Views: `graph`, `tree`, `book`, `module`, or `all`. Write them as `graph, module` or `(graph, module)`.
- Hiding a section or a group node also hides everything under it: the nodes in the section and the nodes that are `part-of` it.
- The Outline in the Explorer still lists hidden nodes (dimmed), so you can find and edit them.
- View › *Show hidden nodes* (Ctrl+H) shows everything again for a moment.

@node style
- label: Style
- type: Concept

Style files keep the 0.2 format in KING 0.3: a rule is `@rule: Title` with `- meta: select="…", html.*=…`. Selectors: `kind=section`, `type=Concept`, `role=Output`, `#name`, `link`, `link=needs`. See `templates/style.kg.md`.

Every node look has five colours, so all views draw a node the same way:

| Key | Meaning |
|---|---|
| `html.color` | fill |
| `html.border-color` | border |
| `html.font-color` | main text (if missing, black or white is chosen for contrast with the fill) |
| `html.label-color` | title of a group or section box |
| `html.sub-color` | secondary text (type, role) |

@node validation
- label: Validation
- type: Concept
- link needs: (schema-files)

| Level | Rule |
|---|---|
| Error | Duplicate name; attribute written twice; malformed attribute line; missing `)` / `]` / `"` |
| Error | Node type or link type not imported; type name not capitalised; link to a missing node; cycle in a `dag` link type |
| Error | 0.2 syntax (`@id: Title`) or a label on the opening line |
| Warning | An attribute used once that looks like another one (`rol` vs `role`); `has` not supported yet; skipped heading level |

@node json
- label: JSON output
- type: Concept
- link needs: (validation)

A networkx node-link graph. Every node has `id` (its name), `kind`, `type`, `label`, `attrs`, `content`, `parent` and `line`; every link has `source`, `target`, `type` and `line`. `title` and `meta` are kept for older tools.

@node views
- label: The editor
- link needs: (tooling)

- Views: **Text**, **Graph**, **Tree**, **Book**, **Module**. Every view follows the text.
- Two panes, each with tabs. The **+** button of a pane adds a view to it, e.g. Tree on the left and Graph or Book on the right. Tabs can be closed or dragged to the other pane; the layout is remembered.
- **Ctrl+S** saves the file (as does the Save button).
- **Tree** shows each node's label, its type and, only when the role is `output`, its role. The Tree and the Outline do not list attributes.
- **Graph** is laid out as a tree by default: the root on the left, each level one column to the right, nodes snapped to the grid (parent: `part-of`, then `contain`, then the section). Pick the layout from the drop-down on the Graph toolbar (or press **L** for the next one): *Indented* (parent level with its first child, the default), *Tidy* (parent centred on its children), *Radial* (rings around the root) and *Force*; **Shift+L** lays the file out again. The grid (button or **G**) snaps dragged nodes to grid points. Hand-placed positions are saved per file and kept when you add or remove nodes and reload: known nodes stay put and only new nodes are laid out.
- **Ctrl+H** shows hidden nodes for a moment (see @hide).
- In 0.3 the Inspector and graph editing tools are frozen (read-only).

@node vscode-colors
- label: Colours in VS Code
- type: Concept
- link needs: (views)

To colour `.kg.md` files in VS Code like the KING editor, install the extension *Highlight* (`fabiospampinato.vscode-highlight`) and add `highlight.regexes` rules with `filterFileRegex` set to `.*\.kg\.md$` in `.vscode/settings.json`. Palette: node `#E8D48A`, link `#A5ABB6`, keyword `#C586C0`, key `#9CDCFE`, type `#4EC9B0`, string `#CE9178`, comment `#6A9955` italic, punctuation `#808080`. The colouring works line by line, so it is only close to the KING editor.

## 4. Improvement plan @roadmap

@node r-has
- label: Child nodes (has)
- ask: Choose a syntax for child nodes with their types.

@node r-types
- label: Type inheritance
- ask: `<:` for inheritance and `::` for type annotations.

@node r-operators
- label: Operators
- ask: Arithmetic and comparison operators in values (0.4).

@node r-style
- label: Style in 0.3 syntax
- ask: Rewrite the style format in 0.3 syntax and allow style inside data files again.

@node r-inspector
- label: Inspector and graph editing
- ask: Unfreeze the Inspector and the graph tools on top of the new block tree.

@node r-typst
- label: Typst output
- ask: Export Content `[ ]` as Typst markup.
