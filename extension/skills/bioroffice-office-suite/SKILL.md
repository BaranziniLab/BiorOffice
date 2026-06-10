---
name: bioroffice-office-suite
description: Core guide for the BiorOffice officecli tool — create, read, analyze, and modify Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) documents. Covers the tool calling convention, DOM paths, the built-in help system, and dynamic loading of specialized Office skills.
---

# BiorOffice Office Suite (officecli MCP tool)

The **bioroffice** extension exposes one MCP tool: `officecli`. It creates, reads,
analyzes, and modifies Office documents (.docx, .xlsx, .pptx) with no Microsoft
Office installation. Use it whenever the user asks for Word documents, Excel
spreadsheets, or PowerPoint presentations.

## Tool calling convention

Every call is `officecli` with a JSON argument object. `command` is required:

| command | key arguments |
|---|---|
| `create` | `file` — blank .docx/.xlsx/.pptx (type inferred from extension) |
| `view` | `file`, `mode`: `outline` \| `stats` \| `issues` \| `text` \| `annotated` \| `html` \| `screenshot` |
| `get` | `file`, `path`, `depth` (default 1) |
| `query` | `file`, `selector` (CSS-like), optional `text` filter |
| `set` | `file`, `path`, `props` (array of `"key=value"` strings) |
| `add` | `file`, `parent`, `type`, `props`, optional `index`/`after`/`before` |
| `remove` | `file`, `path` |
| `move` | `file`, `path`, `to`, optional `index`/`after`/`before` |
| `swap` | `file`, `path`, `path2` |
| `validate` | `file` — validate against the OpenXML schema |
| `batch` | `file`, `commands` (JSON array as a string) — many ops, one save cycle |
| `raw` | `file`, `part` — raw XML escape hatch |
| `help` | `format` (`docx`/`xlsx`/`pptx`), optional `type` for one element's schema |
| `load_skill` | `name` — load a specialized skill (see below) |

Example — add a slide:

```json
{"command": "add", "file": "/abs/path/deck.pptx", "parent": "/",
 "type": "slide", "props": ["title=Q4 Report", "background=1A1A2E"]}
```

## Dynamic specialized skills (IMPORTANT)

Before substantive document work, load the matching specialized skill **once per
artifact** with `load_skill` — it returns authoritative design/structure rules:

| `name` | When to use |
|---|---|
| `word` | Reports, letters, memos, proposals, generic documents |
| `academic-paper` | Journal/conference/thesis with citations, equations, cross-refs |
| `pptx` | Generic decks: board reviews, sales decks, all-hands |
| `pitch-deck` | Fundraising decks only |
| `morph-ppt` / `morph-ppt-3d` | Morph-animated / 3D presentations |
| `excel` | Generic workbooks, formulas, pivots, trackers |
| `financial-model` | Financial models, scenarios, projections |
| `data-dashboard` | KPI/analytics dashboards with charts and sparklines |

Pick the most specific match; if none fits, load the format default
(`word` / `pptx` / `excel`). Load **one** skill per artifact, never stack.
Loaded rules persist across turns.

## Paths (DOM addressing)

- Paths are **1-based** (XPath convention): `/body/p[3]` = third paragraph;
  `/slide[1]/shape[2]`; `/Sheet1/A1`; `/Sheet1/A1:D10`.
- `--index`-style `index` argument is **0-based** (Excel row/col add: 1-based).
- Prefer stable-ID paths returned by the tool (`/slide[1]/shape[@id=550950021]`,
  `/body/p[@paraId=1A2B3C4D]`) in multi-step edits — positional indices shift.
- In PPT, `shape[1]` is usually the title placeholder; content starts at `shape[2]`.

## Help system — never guess

When unsure about property names, value formats, or element types, call help
instead of guessing:

```json
{"command": "help", "format": "docx"}                      // list all elements
{"command": "help", "format": "docx", "type": "paragraph"} // full element schema
```

## Workflow

1. `create` (or inspect an existing file with `view` mode `outline` / `stats`).
2. `load_skill` for the artifact type.
3. Build content with `add` / `set` (use `batch` for many operations — much faster).
4. Verify: `view` mode `outline` or `text`, then `validate` and `view` mode `issues`.
5. For visual checks, `view` mode `html` (no browser server needed) or `screenshot`.

## Pitfalls

- All attributes go through `props` as `"key=value"` strings — e.g. `"bold=true"`,
  `"color=FF0000"`, `"size=24"`, `"text=Hello"`.
- Colors: hex with/without `#`, named (`red`), `rgb(...)`, theme (`accent1`..`accent6`).
- Dimensions: `2cm`, `1in`, `72pt`, `96px`, or raw EMU. Spacing: `12pt`, `1.5x`, `150%`.
- Newlines inside text props: use `\n` inside the JSON string value.
- After modifications, run `validate` and `view` mode `issues` before declaring done.
- Always pass absolute file paths.
