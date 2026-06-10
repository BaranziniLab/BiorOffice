#!/usr/bin/env python3
"""
BiorOffice functional test.

Drives the extension over MCP stdio exactly as BioRouter does
(`uv run --directory <ext-dir> bioroffice`) and verifies the three core
capabilities:

  1. PowerPoint — multi-slide deck with title, styled text shapes, a table
  2. Word      — rich formatting: headings, styled runs, table, header,
                 footer, hyperlink, find-format
  3. Excel     — complex formulas (IF chains, VLOOKUP, SUMIFS, cross-sheet),
                 number formats, conditional formatting, a chart, named range

Every document is verified by reading content back (computed formula values,
outlines) and running OpenXML validation. Exits non-zero on any failure.

Usage:  python3 scripts/functional_test.py <extension-dir> [output-dir]
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

EXT_DIR = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / ".config/biorouter/extensions/bioroffice")
OUT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix="bioroffice-test-"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

FAILURES = []


class MCP:
    def __init__(self, ext_dir):
        self.p = subprocess.Popen(
            ["uv", "run", "--directory", ext_dir, "bioroffice"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        self._id = 0
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "bioroffice-functional-test", "version": "1.0"},
        })
        self._notify("notifications/initialized")

    def _send(self, obj):
        self.p.stdin.write((json.dumps(obj) + "\n").encode())
        self.p.stdin.flush()

    def _notify(self, method):
        self._send({"jsonrpc": "2.0", "method": method})

    def _rpc(self, method, params):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("MCP server closed the pipe")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                return msg

    def call(self, **arguments):
        msg = self._rpc("tools/call", {"name": "officecli", "arguments": arguments})
        if "error" in msg:
            raise RuntimeError(f"RPC error: {msg['error']}")
        result = msg["result"]
        text = "".join(c.get("text", "") for c in result.get("content", []))
        if result.get("isError"):
            raise RuntimeError(f"tool error for {arguments}: {text}")
        return text

    def close(self):
        self.p.terminate()


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(f"{label}: {detail}")


def test_powerpoint(mcp):
    print("\n=== PowerPoint ===")
    f = str(OUT_DIR / "quarterly-review.pptx")
    mcp.call(command="create", file=f)
    mcp.call(command="add", file=f, parent="/", type="slide",
             props=["title=Q4 2026 Business Review", "background=1A1A2E"])
    mcp.call(command="add", file=f, parent="/slide[1]", type="shape",
             props=["text=Prepared by BiorOffice", "x=2cm", "y=10cm", "w=20cm", "h=2cm",
                    "size=18", "color=AAAAEE", "align=center"])
    mcp.call(command="add", file=f, parent="/", type="slide",
             props=["title=Revenue Highlights", "background=1A1A2E"])
    mcp.call(command="add", file=f, parent="/slide[2]", type="shape",
             props=["text=Revenue grew 25% year-over-year\\nGross margin improved to 62%",
                    "x=2cm", "y=4cm", "w=21cm", "h=5cm", "size=22", "color=FFFFFF"])
    mcp.call(command="add", file=f, parent="/slide[2]", type="table",
             props=["rows=3", "cols=3", "x=2cm", "y=10cm", "w=20cm"])
    mcp.call(command="add", file=f, parent="/", type="slide", props=["title=Outlook"])
    mcp.call(command="add", file=f, parent="/slide[3]", type="notes",
             props=["text=Close with the 2027 expansion plan."])

    outline = mcp.call(command="view", file=f, mode="outline")
    check("3 slides present", "Slide 3" in outline, outline[:200])
    check("title on slide 1", "Q4 2026 Business Review" in outline, outline[:200])
    slide_text = mcp.call(command="view", file=f, mode="text")
    check("content text on slide 2", "Revenue grew 25%" in slide_text, slide_text[:300])
    shapes = mcp.call(command="get", file=f, path="/slide[2]", depth=1)
    check("table added to slide 2", "table" in shapes.lower(), shapes[:300])
    validation = mcp.call(command="validate", file=f)
    check("pptx OpenXML valid", "invalid" not in validation.lower(), validation[:200])
    check("pptx file exists on disk", Path(f).stat().st_size > 5000)


def test_word(mcp):
    print("\n=== Word ===")
    f = str(OUT_DIR / "annual-report.docx")
    mcp.call(command="create", file=f)
    mcp.call(command="add", file=f, parent="/body", type="paragraph",
             props=["text=Annual Report 2026", "style=Title"])
    mcp.call(command="add", file=f, parent="/body", type="paragraph",
             props=["text=Executive Summary", "style=Heading1"])
    mcp.call(command="add", file=f, parent="/body", type="paragraph",
             props=["text=Revenue increased by 25% year-over-year, driven by strong product adoption."])
    # Rich run formatting: bold + color the matched text
    mcp.call(command="set", file=f, path="/body/p[3]",
             props=["find=25%", "bold=true", "color=C00000"])
    mcp.call(command="add", file=f, parent="/body", type="paragraph",
             props=["text=Financial Results", "style=Heading1"])
    mcp.call(command="add", file=f, parent="/body", type="table",
             props=["rows=3", "cols=3", "style=TableGrid"])
    mcp.call(command="set", file=f, path="/body/tbl[1]/tr[1]/tc[1]",
             props=["text=Metric", "bold=true"])
    mcp.call(command="set", file=f, path="/body/tbl[1]/tr[1]/tc[2]",
             props=["text=2025", "bold=true"])
    mcp.call(command="set", file=f, path="/body/tbl[1]/tr[2]/tc[1]", props=["text=Revenue ($M)"])
    mcp.call(command="set", file=f, path="/body/tbl[1]/tr[2]/tc[2]", props=["text=128.4"])
    mcp.call(command="add", file=f, parent="/", type="header", props=["text=BiorOffice Inc. — Confidential"])
    mcp.call(command="add", file=f, parent="/", type="footer", props=["text=Annual Report 2026"])
    mcp.call(command="add", file=f, parent="/body", type="paragraph",
             props=["text=For more information visit "])
    mcp.call(command="add", file=f, parent="/body/p[5]", type="hyperlink",
             props=["text=our investor site", "url=https://example.com/investors"])

    text = mcp.call(command="view", file=f, mode="text")
    check("title text present", "Annual Report 2026" in text, text[:200])
    check("body paragraph present", "25% year-over-year" in text, text[:300])
    cell = mcp.call(command="get", file=f, path="/body/tbl[1]/tr[2]/tc[1]")
    check("table cell content present", "Revenue ($M)" in cell, cell[:300])
    annotated = mcp.call(command="view", file=f, mode="annotated")
    check("heading style applied", "Heading1" in annotated, annotated[:400])
    check("bold find-format applied", "bold" in annotated.lower(), annotated[:400])
    validation = mcp.call(command="validate", file=f)
    check("docx OpenXML valid", "invalid" not in validation.lower(), validation[:200])
    check("docx file exists on disk", Path(f).stat().st_size > 3000)


def test_excel(mcp):
    print("\n=== Excel ===")
    f = str(OUT_DIR / "sales-model.xlsx")
    mcp.call(command="create", file=f)
    # Lookup sheet
    mcp.call(command="add", file=f, parent="/", type="sheet", props=["name=Rates"])
    mcp.call(command="set", file=f, path="/Rates/A1", props=["value=Region"])
    mcp.call(command="set", file=f, path="/Rates/B1", props=["value=Commission"])
    for i, (region, rate) in enumerate([("North", 0.08), ("South", 0.10), ("East", 0.07), ("West", 0.12)], start=2):
        mcp.call(command="set", file=f, path=f"/Rates/A{i}", props=[f"value={region}"])
        mcp.call(command="set", file=f, path=f"/Rates/B{i}", props=[f"value={rate}"])
    # Data sheet via batch (one save cycle)
    header = [
        {"command": "set", "path": "/Sheet1/A1", "props": {"value": "Region", "bold": "true", "fill": "1A1A2E", "color": "FFFFFF"}},
        {"command": "set", "path": "/Sheet1/B1", "props": {"value": "Units", "bold": "true", "fill": "1A1A2E", "color": "FFFFFF"}},
        {"command": "set", "path": "/Sheet1/C1", "props": {"value": "UnitPrice", "bold": "true", "fill": "1A1A2E", "color": "FFFFFF"}},
        {"command": "set", "path": "/Sheet1/D1", "props": {"value": "Revenue", "bold": "true", "fill": "1A1A2E", "color": "FFFFFF"}},
        {"command": "set", "path": "/Sheet1/E1", "props": {"value": "Commission", "bold": "true", "fill": "1A1A2E", "color": "FFFFFF"}},
        {"command": "set", "path": "/Sheet1/F1", "props": {"value": "Tier", "bold": "true", "fill": "1A1A2E", "color": "FFFFFF"}},
    ]
    rows = [("North", 120, 49.5), ("South", 80, 75.0), ("East", 200, 19.99), ("West", 45, 320.0), ("North", 60, 49.5)]
    data = []
    for r, (region, units, price) in enumerate(rows, start=2):
        data += [
            {"command": "set", "path": f"/Sheet1/A{r}", "props": {"value": region}},
            {"command": "set", "path": f"/Sheet1/B{r}", "props": {"value": str(units)}},
            {"command": "set", "path": f"/Sheet1/C{r}", "props": {"value": str(price), "format": "#,##0.00"}},
            # Revenue = Units * UnitPrice
            {"command": "set", "path": f"/Sheet1/D{r}", "props": {"formula": f"=B{r}*C{r}", "format": "$#,##0.00"}},
            # Commission via cross-sheet VLOOKUP
            {"command": "set", "path": f"/Sheet1/E{r}", "props": {"formula": f"=ROUND(D{r}*VLOOKUP(A{r},Rates!$A$2:$B$5,2,FALSE),2)", "format": "$#,##0.00"}},
            # Tier via nested IF
            {"command": "set", "path": f"/Sheet1/F{r}", "props": {"formula": f"=IF(D{r}>=10000,\"Gold\",IF(D{r}>=5000,\"Silver\",\"Bronze\"))"}},
        ]
    summary = [
        {"command": "set", "path": "/Sheet1/H1", "props": {"value": "TotalRevenue", "bold": "true"}},
        {"command": "set", "path": "/Sheet1/H2", "props": {"formula": "=SUM(D2:D6)", "format": "$#,##0.00"}},
        {"command": "set", "path": "/Sheet1/I1", "props": {"value": "NorthRevenue", "bold": "true"}},
        {"command": "set", "path": "/Sheet1/I2", "props": {"formula": "=SUMIFS(D2:D6,A2:A6,\"North\")", "format": "$#,##0.00"}},
        {"command": "set", "path": "/Sheet1/J1", "props": {"value": "AvgBigDeals", "bold": "true"}},
        {"command": "set", "path": "/Sheet1/J2", "props": {"formula": "=AVERAGEIF(D2:D6,\">5000\")"}},
        {"command": "set", "path": "/Sheet1/K1", "props": {"value": "WeightedPrice", "bold": "true"}},
        {"command": "set", "path": "/Sheet1/K2", "props": {"formula": "=SUMPRODUCT(B2:B6,C2:C6)/SUM(B2:B6)", "format": "0.00"}},
    ]
    mcp.call(command="batch", file=f, commands=json.dumps(header + data + summary))
    # Named range, conditional formatting, chart
    mcp.call(command="add", file=f, parent="/", type="namedrange",
             props=["name=TotalRevenue", "refersTo=Sheet1!$H$2"])
    mcp.call(command="add", file=f, parent="/Sheet1", type="cf",
             props=["range=D2:D6", "type=colorscale"])
    mcp.call(command="add", file=f, parent="/Sheet1", type="chart",
             props=["type=bar", "dataRange=Sheet1!A1:B6", "title=Units by Region", "anchor=H4:P20"])

    # Verify computed formula values
    def cell_value(path):
        return mcp.call(command="get", file=f, path=path)

    d2 = cell_value("/Sheet1/D2")            # 120*49.5 = 5940
    check("Revenue formula computed (D2=5940)", "5940" in d2, d2)
    e2 = cell_value("/Sheet1/E2")            # 5940*0.08 = 475.2
    check("VLOOKUP commission computed (E2=475.2)", "475.2" in e2, e2)
    f2 = cell_value("/Sheet1/F2")            # 5940 -> Silver
    check("nested IF tier computed (F2=Silver)", "Silver" in f2, f2)
    h2 = cell_value("/Sheet1/H2")            # total 5940+6000+3998+14400+2970 = 33308
    check("SUM total computed (H2=33308)", "33308" in h2, h2)
    i2 = cell_value("/Sheet1/I2")            # north 5940+2970 = 8910
    check("SUMIFS computed (I2=8910)", "8910" in i2, i2)
    chart = mcp.call(command="get", file=f, path="/Sheet1", depth=1)
    check("chart present on Sheet1", "chart" in chart.lower(), chart[:300])
    validation = mcp.call(command="validate", file=f)
    check("xlsx OpenXML valid", "invalid" not in validation.lower(), validation[:200])
    check("xlsx file exists on disk", Path(f).stat().st_size > 5000)


def test_dynamic_skills(mcp):
    print("\n=== Dynamic skill loading (load_skill) ===")
    for name, marker in [("pptx", "pptx"), ("word", "word"), ("excel", "excel")]:
        body = mcp.call(command="load_skill", name=name)
        check(f"load_skill {name} returns guidance", len(body) > 500, f"{len(body)} chars")


def main():
    print(f"Extension dir: {EXT_DIR}")
    print(f"Output dir:    {OUT_DIR}")
    mcp = MCP(EXT_DIR)
    try:
        test_dynamic_skills(mcp)
        test_powerpoint(mcp)
        test_word(mcp)
        test_excel(mcp)
    finally:
        mcp.close()
    print("\n" + "=" * 50)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILURE(S)")
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)
    print("RESULT: ALL CHECKS PASSED")
    print(f"Artifacts: {OUT_DIR}")


if __name__ == "__main__":
    main()
