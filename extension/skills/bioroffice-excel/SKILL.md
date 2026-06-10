---
name: bioroffice-excel
description: Create and edit Excel (.xlsx) workbooks with the BiorOffice officecli tool — cells, complex formulas (150+ functions with auto-evaluation), charts, pivot tables, conditional formatting, named ranges, data validation, sorting, and tables.
---

# BiorOffice — Excel (.xlsx)

Use the `officecli` MCP tool (bioroffice extension). Read the
`bioroffice-office-suite` skill for the calling convention. For substantive
workbooks, first call `{"command":"load_skill","name":"excel"}` (or
`financial-model` / `data-dashboard` when those fit) and follow its rules.

## Cells and values

Cell paths are `/SheetName/A1`. Set values, formatting, and formulas with `set`:

```json
{"command":"set","file":"/abs/data.xlsx","path":"/Sheet1/A1",
 "props":["value=Region","bold=true","fill=1A1A2E","color=FFFFFF"]}
{"command":"set","file":"/abs/data.xlsx","path":"/Sheet1/B2","props":["value=1250.75","format=#,##0.00"]}
```

Common cell props: `value`, `formula`, `format` (number format code), `bold`,
`italic`, `color`, `fill`, `border`, `align`, `wrap`, `merge=range`,
`font.size`, `width` (on columns). Bulk-fill a row: `add` type `row` with
`"c1=Name"`, `"c2=Score"` shorthand props.

## Formulas — auto-evaluated, 150+ functions

Values starting with `=` are auto-detected as formulas and **evaluated on save**
(no Excel needed). Dynamic-array functions get `_xlfn.` auto-prefixed.

```json
{"command":"set","file":"/abs/data.xlsx","path":"/Sheet1/D2",
 "props":["formula==IF(C2>=90,\"A\",IF(C2>=80,\"B\",\"C\"))"]}
{"command":"set","file":"/abs/data.xlsx","path":"/Sheet1/E2",
 "props":["formula==VLOOKUP(A2,Lookup!$A$2:$B$50,2,FALSE)"]}
{"command":"set","file":"/abs/data.xlsx","path":"/Sheet1/F1",
 "props":["formula==SUMIFS(Sales!C:C,Sales!A:A,A1,Sales!B:B,\">=100\")"]}
```

Cross-sheet references (`Sheet2!A1`), absolute refs, `OFFSET`/`INDIRECT`,
`XLOOKUP`, `SUMPRODUCT`, statistical and date functions are all supported.
Read back the **computed value** with `get` to verify each key formula:

```json
{"command":"get","file":"/abs/data.xlsx","path":"/Sheet1/D2"}
```

## Sheets, tables, named ranges, validation

```json
{"command":"add","file":"/abs/data.xlsx","parent":"/","type":"sheet","props":["name=Summary"]}
{"command":"add","file":"/abs/data.xlsx","parent":"/Sheet1","type":"table","props":["range=A1:E20","name=SalesTable","style=TableStyleMedium9"]}
{"command":"add","file":"/abs/data.xlsx","parent":"/","type":"namedrange","props":["name=TaxRate","refersTo=Summary!$B$1"]}
{"command":"add","file":"/abs/data.xlsx","parent":"/Sheet1","type":"validation","props":["range=C2:C100","type=list","formula1=\"Low,Medium,High\""]}
```

## Charts, conditional formatting, sparklines

```json
{"command":"add","file":"/abs/data.xlsx","parent":"/Sheet1","type":"chart",
 "props":["type=bar","data=Sheet1!A1:B10","title=Sales by Region","anchor=7,1,15,20"]}
{"command":"add","file":"/abs/data.xlsx","parent":"/Sheet1","type":"cf",
 "props":["range=B2:B100","type=colorscale"]}
{"command":"add","file":"/abs/data.xlsx","parent":"/Sheet1","type":"cf",
 "props":["range=C2:C100","type=cellIs","operator=greaterThan","value=90","fill=C6EFCE"]}
```

## Pivot tables

```json
{"command":"add","file":"/abs/data.xlsx","parent":"/Sheet1","type":"pivottable",
 "props":["source=Sheet1!A1:E100","rows=Region,Category","cols=Year",
          "values=Sales:sum,Qty:count","position=Summary!A3"]}
```

Aggregators: sum, count, average, max, min, stdDev, var… Date columns auto-group.
Full schema: `{"command":"help","format":"xlsx","type":"pivottable"}`.

## Sort and import

Sort: `{"command":"set","path":"/Sheet1","props":["sort=C desc","sortHeader=true"]}`.
CSV import is available via the CLI `import` command shape in `batch`.

## Verify

Use `batch` for large fills (one save cycle). Then `get` key formula cells to
confirm computed values, `{"command":"view","mode":"stats"}`, `validate`, and
`{"command":"view","mode":"issues"}` before delivering.
