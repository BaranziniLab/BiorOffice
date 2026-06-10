---
name: bioroffice-powerpoint
description: Create and edit PowerPoint (.pptx) presentations with the BiorOffice officecli tool — slides, shapes, text styling, images, tables, charts, transitions, animations, and speaker notes.
---

# BiorOffice — PowerPoint (.pptx)

Use the `officecli` MCP tool (bioroffice extension). Read the
`bioroffice-office-suite` skill for the calling convention. For substantive
decks, first call `{"command":"load_skill","name":"pptx"}` (or `pitch-deck` /
`morph-ppt` when those fit) and follow its design rules.

## Slides

```json
{"command":"create","file":"/abs/deck.pptx"}
{"command":"add","file":"/abs/deck.pptx","parent":"/","type":"slide",
 "props":["title=Q4 Report","background=1A1A2E"]}
```

Default canvas is 960×540 pt (16:9). Clone a styled slide:
`{"command":"add","parent":"/","from":"/slide[1]"}` style via `batch` op `add`
with `from`. Reorder with `move`/`swap`. Speaker notes:
`{"command":"add","parent":"/slide[1]","type":"notes","props":["text=..."]}`.

## Shapes and text

`shape[1]` is usually the title placeholder — content shapes start at `shape[2]`.

```json
{"command":"add","file":"/abs/deck.pptx","parent":"/slide[1]","type":"shape",
 "props":["text=Revenue grew 25%","x=2cm","y=5cm","w=20cm","h=3cm",
          "font=Arial","size=24","color=FFFFFF","bold=true","align=center"]}
```

Useful shape props: `shapeType` (rect, roundRect, ellipse, rightArrow…),
`fill`, `line.color`, `line.width`, `rotation`, `shadow`, `glow`,
`fill.transparency`. Format matched text inside a shape:
`set` with `"find=25%"` + format props. Multi-paragraph text: `\n` in the text
value; per-paragraph control via `add` type `paragraph`/`run` under the shape.

## Images, tables, charts

```json
{"command":"add","file":"/abs/deck.pptx","parent":"/slide[2]","type":"picture",
 "props":["src=/abs/figure.png","x=1cm","y=3cm","w=10cm","fillMode=contain"]}
{"command":"add","file":"/abs/deck.pptx","parent":"/slide[2]","type":"table",
 "props":["rows=3","cols=4","x=2cm","y=4cm","w=20cm"]}
{"command":"add","file":"/abs/deck.pptx","parent":"/slide[3]","type":"chart",
 "props":["type=bar","categories=Q1,Q2,Q3,Q4","series=Revenue:10,14,18,25",
          "title=Revenue by Quarter","anchor=2cm,4cm,20cm,10cm"]}
```

Table cells addressed as `/slide[N]/table[@id=...]/tr[R]/tc[C]` — set `text`,
`fill`, `bold` per cell.

## Transitions and animations

```json
{"command":"set","file":"/abs/deck.pptx","path":"/slide[1]","props":["transition=fade"]}
{"command":"add","file":"/abs/deck.pptx","parent":"/slide[1]/shape[2]","type":"animation",
 "props":["preset=fadeIn","trigger=onClick"]}
```

## Verify

`{"command":"view","mode":"outline"}` after each few slides;
`{"command":"get","path":"/slide[N]","depth":1}` to list shapes with positions;
`validate` + `{"command":"view","mode":"issues"}` at the end. For a visual
check, `{"command":"view","mode":"html"}` or `screenshot` (slow, needs a
headless browser). Check overlapping/overflowing text with `issues`.
