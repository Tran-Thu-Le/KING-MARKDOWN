---
kg: v0.4
---

# KIR tutorial @kir-tutorial

**KIR** (KING Intermediate Representation, `kg: v0.4`) stores knowledge as triples inside a Markdown file. A small engine runs rules over those triples and prints whether statements are true, false or unknown. The pipeline is:

**KING lang** (KIR + sugar) → **KIR** (`@add s r o` only) → exports: **networkx JSON** and **RDF Turtle**.

Each section below is a short lesson. Examples are in `king` code blocks; copy one into a file such as `hello.kg.md` and run it with `kir run hello.kg.md` (or `python -m kir run hello.kg.md`). The output shown under each example is the real output.

## 1. One line, one fact @kir-fact

Pure KIR has exactly one form of command:

```king
@add newton born 1643
```

It means "add the fact `newton born 1643` to the store": subject `newton`, link `born`, object `1643`.

- The command must start at **column 0** with `@add` followed by a space, and have exactly **3 tokens**. Any other line is prose (so `@addx ...` or an indented `@add` is just text).
- Tokens: **names** (`[A-Za-z0-9._-]+`, `.` marks a namespace, e.g. `set.member`), **strings** (`"Isaac Newton"`, JSON escapes), **numbers** (`1643`, `2.5`), `true` / `false`.
- Subject and link must be names; the object can be anything.
- `//` starts a comment (outside strings). Lines inside ``` fences are ignored.
- The store is a set: writing the same triple twice adds it once.

A file starts with frontmatter `kg: v0.4`:

```king
---
kg: v0.4
---
@add newton name "Isaac Newton"   // a fact
@add newton born 1643
@print(newton born 1643)
@print(newton died 1727)
```

```text
newton born 1643: true
newton died 1727: unknown
```

`@print(...)` is sugar (lesson 2). `unknown` appears because the default world is open (lesson 4).

## 2. KING sugar and what it compiles to @kir-sugar

KING lang is KIR plus a few shorthands. The compiler rewrites each one into pure KIR and keeps pure KIR lines unchanged (`compile(KIR) = KIR`). See the result with `kir compile file.kg.md`.

| KING | KIR |
|---|---|
| `@add q = s r o` | `@add q k.subject s` · `@add q k.link r` · `@add q k.object o` |
| `@print(q)` | `@add k.terminal k.print q` |
| `@print(s r o)` | a statement `gen.N` (3 lines) + `@add k.terminal k.print gen.N` |
| `@print(A and B)`, `or`, `not`, `( )` | one `gen.N` statement per operator (lesson 6) |
| `@world closed` / `@world open` | `@add k.file set.member k.ClosedWorld` / `k.OpenWorld` |
| `@import set` / `@import "file.kg.md"` | `@add k.file k.import set` / `@add k.file k.import "file.kg.md"` |

`@use` is accepted as an alias of `@import`; `@import` is the preferred style. Malformed sugar is error **E2**.

### Named statements are not facts

`@add q = s r o` describes a statement named `q`. It does **not** assert the triple:

```king
@add q = newton born 1643
@print(q)
```

```text
newton born 1643: unknown
```

The same program in pure KIR, with the fact asserted:

```king
@add newton born 1643
@add q k.subject newton
@add q k.link born
@add q k.object 1643
@add k.terminal k.print q
```

```text
newton born 1643: true
```

## 3. Namespaces @kir-ns

| Prefix | Owner | Meaning |
|---|---|---|
| `k.` | core | understood by the engine: `k.then`, `k.else`, `k.subject`, `k.link`, `k.object`, `k.file`, `k.import`, `k.ClosedWorld`, `k.OpenWorld`, `k.terminal`, `k.print`, `k.and`, `k.or`, `k.not`, `k.of` |
| `set.` | library | `set.member` (∈), `set.subset` (⊆), `set.equal` (alias); rules written in KIR |
| `var.` | variables | `var.x` in a statement makes it a pattern; a fact may not contain `var.*` (E16) |
| `gen.` | compiler | names made by the compiler (`gen.1`, `gen.2`, ...); do not use them yourself |

Every other name is yours. Names are case-sensitive.

## 4. Open and closed world @kir-world

A file declares its world once. Default: **open**.

- **Open world**: a statement in the store is `true`; otherwise `unknown`.
- **Closed world**: a statement in the store is `true`; otherwise `false`.

```king
@world closed
@add newton born 1643
@print(newton born 1643)
@print(newton died 1727)
```

```text
newton born 1643: true
newton died 1727: false
```

Declaring both worlds is error E13. The world only changes how prints are evaluated; rule conditions always ask "is it in the store?".

## 5. Rules: k.then and k.else @kir-rules

A rule is the fact `A k.then B` or `A k.else B`, where A and B are statements (usually patterns with `var.*`).

- `A k.then B`: for every way to match A in the store, add B.
- `A k.else B`: if A does **not** match, add B.
- **Nesting = and**: if B is itself a rule statement, its condition is added to the chain. `c1 k.then r`, `r = c2 k.then h` means "c1 and c2 ⇒ h".
- **Two rules with the same conclusion = or.**

```king
@add newton set.member Scientist
@add newton wrote Principia
@add c1 = var.x set.member Scientist
@add c2 = var.x wrote var.b
@add h = var.x role author
@add r = c2 k.then h
@add c1 k.then r
@print(newton role author)
```

```text
newton role author: true
```

Constraints:

- **Safety (E11)**: every variable of the conclusion must appear in a positive (`k.then`) condition; a variable shared by a `k.else` condition and the conclusion must also appear in a positive condition.
- **Stratification (E12)**: links are ordered by dependency; a cycle that goes through `k.else` is refused. Rules run lowest stratum first, each to a fixpoint. Rules never create new nodes, so a run always stops.
- A conclusion may not have a `k.*` link, a variable link, or the link `set.equal` (E14). A conclusion whose subject would be a literal is skipped silently.
- Compound statements (`k.and`, `k.or`, `k.not`) cannot be rule conditions or conclusions (E14): use nesting, two rules, or `k.else`.

## 6. Logic for printing @kir-logic

`@print` accepts an expression of triples `s r o` and statement names joined by `and`, `or`, `not` and parentheses. Precedence: `not` > `and` > `or`.

```king
@world closed
@add rain today true
@print(rain today true and not wind today true)
@print(rain today true or wind today true and not rain today true)
@print((rain today true or wind today true) and not rain today true)
```

```text
(rain today true) and not (wind today true): true
(rain today true) or ((wind today true) and not (rain today true)): true
((rain today true) or (wind today true)) and not (rain today true): false
```

In a closed world this is **Boolean** logic. In an open world it is **Kleene** three-valued logic with false < unknown < true: `and` = minimum, `or` = maximum, `not` swaps true and false and keeps unknown.

| A | B | A and B (closed / open) | A or B (closed / open) |
|---|---|---|---|
| T | T | T / T | T / T |
| T | F·U | F / U | T / T |
| F·U | T | F / U | T / T |
| F·U | F·U | F / U | F / U |

Here "F·U" is a statement not in the store: `false` when closed, `unknown` when open. `not T` = F; `not` (absent) = T closed, U open.

The visible difference is the excluded middle `q or not q`:

```king
@add has-name = leibniz name "Leibniz"
@print(has-name or not has-name)
```

```text
(leibniz name "Leibniz") or not (leibniz name "Leibniz"): unknown
```

Add `@world closed` (anywhere in the file) and the same line prints `true`.

### Compound statements in pure KIR

The sugar builds compound statements; you can write them directly: `c = q1 k.and q2`, `d = q1 k.or q2`, `n = k.not k.of q`.

```king
@world closed
@add x p y
@add a = x p y
@add b = x q y
@add c = a k.and b
@add d = a k.or b
@add n k.subject k.not
@add n k.link k.of
@add n k.object b
@print(c)
@print(d)
@print(n)
```

```text
(x p y) and (x q y): false
(x p y) or (x q y): true
not (x q y): true
```

A compound statement that refers to itself, or that contains variables, cannot be printed (E14).

## 7. The set library @kir-set

`set` is a library of KIR rules (`src/kir/lib/set.kg.md`). It is **not** loaded by default: write `@import set`.

- membership through subsets: `x set.member A`, `A set.subset B` ⇒ `x set.member B`;
- subset transitivity: `A set.subset B`, `B set.subset C` ⇒ `A set.subset C` (cycles stop);
- `set.equal` aliases: symmetric, and `l1 set.equal l2` makes every `a l1 b` also `a l2 b` (never for `k.*` links).

```king
@import set
@add Physicist set.subset Scientist
@add Scientist set.subset Person
@add newton set.member Physicist
@add is-a set.equal set.member
@print(newton set.member Person)
@print(newton is-a Scientist)
```

```text
newton set.member Person: true
newton is-a Scientist: true
```

Without `@import set`, the first print is `unknown`.

## 8. Example: schema check with k.else @kir-schema

"Every Person without a name gets an error fact":

```king
@import set
@add Scientist set.subset Person
@add newton set.member Scientist
@add newton name "Isaac Newton"
@add leibniz set.member Person
@add w1 = var.x set.member Person
@add w2 = var.x name var.n
@add e = var.x error missing-name
@add r = w2 k.else e
@add w1 k.then r
@print(leibniz error missing-name)
@print(newton error missing-name)
```

```text
leibniz error missing-name: true
newton error missing-name: unknown
```

`var.n` only appears in the `k.else` condition, so it means "there exists some name". Running the library together with `k.else` does not cause E12.

## 9. Imports @kir-import

`@import name` loads `src/kir/lib/name.kg.md`; `@import "path.kg.md"` loads a file relative to the importing file.

- Each file is loaded once (import cycles are fine).
- An imported file contributes facts, statements and rules, but **not** its world declaration or its prints.
- `gen.N` names of an imported file are renamed `gen.<stem>.N`, so they never clash.
- A missing file is error E17.

With `schema.kg.md` holding the five rule lines of lesson 8 (plus its own `@print`, which is ignored):

```king
@import "schema.kg.md"
@add leibniz set.member Person
@add newton set.member Person
@add newton name "Isaac Newton"
@print(leibniz error missing-name)
@print(newton error missing-name)
```

```text
leibniz error missing-name: true
newton error missing-name: unknown
```

## 10. Errors @kir-errors

Errors are reported as `file:line: Ex: message` on stderr; any error stops the run before rules apply (no outputs) and exits with code 1.

| Code | When |
|---|---|
| E2 | syntax error: a plain `@add` line (`expected '@add token token token'`, `subject and link must be names`, `bad token: ...`) or malformed sugar: `@print()`, missing `)`, an operand that is neither a name nor `s r o`, `@add q = ...` without 6 tokens, bad `@world` / `@import` |
| E11 | unsafe variable in a rule |
| E12 | negation (`k.else`) inside a dependency cycle |
| E13 | both `k.ClosedWorld` and `k.OpenWorld` declared |
| E14 | misuse of `k.*`: `k.then` / `k.else` / `k.print` on something that is not a statement, printing a pattern, compound in a rule, conclusion with a `k.*` / variable / `set.equal` link |
| E15 | a statement without exactly one `k.subject` (name), `k.link` (name) and `k.object` |
| E16 | a fact containing `var.*` |
| E17 | an import that cannot be found |

Example: `@add k.terminal k.print newton` gives `file.kg.md:2: E14: k.print needs a statement: newton`.

## 11. Tools @kir-tools

```bash
kir run file.kg.md                        # compile + run, prints `s r o: true|false|unknown`
kir compile file.kg.md                    # show the pure KIR
kir export file.kg.md --json out.json     # networkx node-link JSON ('-' = stdout)
kir export file.kg.md --rdf out.ttl       # RDF Turtle (--base sets the IRI prefix, default urn:kir:)
kir view file.kg.md                       # open the KING web app (also: a folder, --view book, --keep)
```

**Export** reads pure KIR only (run `kir.compile` first if the file uses sugar). Name objects become nodes and edges (edge `key` = link); literal objects become node attributes. This JSON is separate from the KING 0.3 JSON format. For `@add newton born 1643` and `@add newton set.member Scientist` the Turtle output is:

```text
<urn:kir:newton> <urn:kir:born> 1643 .
<urn:kir:newton> <urn:kir:set.member> <urn:kir:Scientist> .
```

**Web app**: `kir view` opens a `kg: v0.4` file in the KING editor. The **Run** button (Ctrl+Enter) runs the file and shows prints and errors in the **OUTPUT** panel; the status bar shows the result. The server stops when the page is closed (unless `--keep`).

**Python API**:

```python
from kir.world import run_text
from kir.compile import compile_text

outputs, diags = run_text(text, "file.kg.md")   # lists of strings
kir = compile_text(text, "file.kg.md")          # pure KIR text; raises CompileError (E2)
```
