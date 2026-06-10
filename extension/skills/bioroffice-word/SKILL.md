---
name: bioroffice-word
description: Create and edit rich-formatted Word (.docx) documents with the BiorOffice officecli tool — headings, styles, runs, tables, images, headers/footers, TOC, footnotes, hyperlinks, tracked changes, and find/replace.
---

# BiorOffice — Word (.docx)

Use the `officecli` MCP tool (bioroffice extension). Read the
`bioroffice-office-suite` skill for the calling convention. For substantive
documents, first call `{"command":"load_skill","name":"word"}` (or
`academic-paper` for scholarly work) and follow its rules.

## Create and structure

```json
{"command":"create","file":"/abs/report.docx"}
{"command":"add","file":"/abs/report.docx","parent":"/body","type":"paragraph",
 "props":["text=Executive Summary","style=Heading1"]}
{"command":"add","file":"/abs/report.docx","parent":"/body","type":"paragraph",
 "props":["text=Revenue increased by 25% year-over-year."]}
```

Built-in styles: `Title`, `Subtitle`, `Heading1`..`Heading9`, `Normal`, `Quote`,
`ListParagraph`. List all docx elements: `{"command":"help","format":"docx"}`.

## Rich run formatting

Format matched text inside a paragraph (auto-splits runs) via `set` + `find` prop:

```json
{"command":"set","file":"/abs/report.docx","path":"/body/p[2]",
 "props":["find=25%","bold=true","color=C00000"]}
```

Whole-paragraph formatting: `props` like `align=center`, `font=Georgia`,
`size=14pt`, `spacing.before=12pt`, `lineSpacing=1.5x`, `indent.left=1cm`.
Run-level: `bold`, `italic`, `underline`, `strike`, `color`, `highlight`,
`font`, `size`, `subscript`/`superscript`, `smallCaps`.

## Tables

```json
{"command":"add","file":"/abs/report.docx","parent":"/body","type":"table",
 "props":["rows=3","cols=3","style=TableGrid"]}
{"command":"set","file":"/abs/report.docx","path":"/body/tbl[1]/tr[1]/tc[1]",
 "props":["text=Metric","bold=true","fill=1A1A2E","color=FFFFFF"]}
```

Header row shading via cell `fill`; column ops on `/body/tbl[N]/col[M]`.

## Document furniture

```json
{"command":"add","file":"/abs/report.docx","parent":"/","type":"header","props":["text=Confidential"]}
{"command":"add","file":"/abs/report.docx","parent":"/","type":"footer","props":["text=Page ","pageNumber=true"]}
{"command":"add","file":"/abs/report.docx","parent":"/body","type":"toc","index":0}
{"command":"add","file":"/abs/report.docx","parent":"/body/p[3]","type":"footnote","props":["text=Source: internal data."]}
{"command":"add","file":"/abs/report.docx","parent":"/body/p[2]","type":"hyperlink","props":["text=our website","url=https://example.com"]}
{"command":"add","file":"/abs/report.docx","parent":"/body","type":"image","props":["src=/abs/chart.png","width=12cm"]}
{"command":"add","file":"/abs/report.docx","parent":"/","type":"watermark","props":["text=DRAFT"]}
```

Document defaults: `{"command":"set","path":"/","props":["docDefaults.font=Calibri","docDefaults.fontSize=11pt"]}`.

## Find & replace (whole document)

```json
{"command":"set","file":"/abs/report.docx","path":"/","props":["find=draft","replace=final"]}
```

Tracked: add `"revision.author=Alice"`. Regex: add `"regex=true"` (case-insensitive: `(?i)` prefix).

## Verify

`{"command":"view","mode":"outline"}` → structure;
`{"command":"view","mode":"annotated"}` → text + formatting;
`{"command":"validate"}` and `{"command":"view","mode":"issues"}` before delivering.
