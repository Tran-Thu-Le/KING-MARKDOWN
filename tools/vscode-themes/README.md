# VS Code colour templates for `.kg.md`

Colours `.kg.md` files with the **Highlight** extension (`fabiospampinato.vscode-highlight`), which uses regexes, so no grammar is needed. The template is installed in your **user settings**, so it applies in every folder, only to `*.kg.md`.

## Templates
| Name | Use when | Colours |
|---|---|---|
| `king` | You want the look of the KING editor's text pane | Everything: headings, `@node`, links, keys, strings, comments (palette from the repo's `.vscode/settings.json`) |
| `markdown` | You write mostly prose and want your theme's Markdown colours | Only `@node`, `@link`, `- link …:`, `- type:`, attribute values, inline `@ref`; the rest is left to Markdown |
| `python` | Dark theme, read it like Python | `@node` like `def`/`class`; links purple/light blue; keys `#9CDCFE`; values as Python literals (numbers `#B5CEA8`, `True/False/None/null` `#569CD6`, `(ref)` `#DCDCAA`, strings `#CE9178`); `//` comments green italic |

## Enable / switch / disable
Run from the repo root:
```
python tools/sync_vscode_highlight.py --list            # list; * marks the active one
python tools/sync_vscode_highlight.py --theme markdown  # enable or switch
python tools/sync_vscode_highlight.py --off             # remove KING colours
python tools/sync_vscode_highlight.py                   # re-apply the active one (after editing colours)
```
If nothing changes, run **Developer: Reload Window**.

The script only replaces the block between `// >>> KING theme=<name>` and `// <<< KING` inside `"highlight.regexes"` of `%APPDATA%/Code/User/settings.json`, backs the file up to `settings.json.bak` first, and sets `"highlight.regexFlags": "gm"` (no `i`: KING distinguishes `Type` from `node-id`).

## Edit or add a template
1. Edit or add `theme_<name>()` in `build_themes.py` and register it in `THEMES`.
2. `python tools/vscode-themes/build_themes.py` regenerates `<name>.json`.
3. `python tools/sync_vscode_highlight.py --theme <name>`.

Notes: regexes are **JavaScript** syntax (Python only pre-checks them; variable-length lookbehinds are skipped). Each regex colours its `( )` groups in `decorations` order; `{}` means no colour. The `king` template comes from the repo's `.vscode/settings.json`, which also overrides user settings when the KING repo itself is the open workspace.
