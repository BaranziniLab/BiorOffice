# BiorOffice

**Microsoft Office automation as a BioRouter extension.** BiorOffice packages
the open-source [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) engine
(Apache-2.0, by iOfficeAI) into a self-contained `.brxt` bundle that installs
directly into [BioRouter](https://github.com/BaranziniLab/BioRouter). Once
installed, the BioRouter agent can create, read, analyze, and edit Word
(.docx), Excel (.xlsx), and PowerPoint (.pptx) documents — **no Microsoft
Office installation required**.

## Repository layout

| Path | Contents |
|---|---|
| [`extension/`](extension/) | The .brxt source: `manifest.json`, `pyproject.toml`, Python launcher (`src/bioroffice/`), bundled OfficeCLI binary (`bin/`), and 4 bundled skills (`skills/`) |
| [`officecli/`](officecli/) | Vendored OfficeCLI source code (upstream `iOfficeAI/OfficeCLI@main`, Apache-2.0) |
| [`dist/bioroffice.brxt`](dist/) | The built, installable extension bundle |
| [`scripts/build_brxt.sh`](scripts/build_brxt.sh) | Builds `dist/bioroffice.brxt` from `extension/` |
| [`scripts/functional_test.py`](scripts/functional_test.py) | End-to-end MCP test: PPTX deck, rich DOCX, formula-heavy XLSX |
| [`e2e/bioroffice-install.spec.ts`](e2e/) | Playwright spec that installs the .brxt through the real BioRouter GUI and has the live agent create a document |
| [`CHECKLIST.md`](CHECKLIST.md) | Comprehensive install / validation / usage checklists |

## How it works

```
BioRouter agent ──MCP (stdio)──► uv run --directory ~/.config/biorouter/extensions/bioroffice bioroffice
                                   │  (Python launcher: pick platform binary, restore exec bit,
                                   │   verify SHA-256, auto-download if missing)
                                   └─ exec → officecli mcp   (native MCP server, 1 tool: `officecli`)
```

- **One MCP tool, full surface** — `officecli` covers create / view / get /
  query / set / add / remove / move / swap / validate / batch / raw / help /
  load_skill across all three formats, including formula evaluation (150+
  Excel functions), charts, pivot tables, and an agent-friendly HTML/PNG
  rendering engine.
- **Bundled BioRouter skills** (auto-discovered at session start):
  `bioroffice-office-suite`, `bioroffice-word`, `bioroffice-excel`,
  `bioroffice-powerpoint`.
- **Dynamic specialized skills** the agent loads on demand via `load_skill`:
  `word`, `academic-paper`, `pptx`, `pitch-deck`, `morph-ppt`, `morph-ppt-3d`,
  `excel`, `financial-model`, `data-dashboard`.
- **Self-contained & pinned** — OfficeCLI v1.0.108 (macOS arm64) ships inside
  the bundle with SHA-256 verification; other platforms auto-download the same
  pinned release on first launch.

## Install into BioRouter

GUI: **Extensions → Add Extension → Browse file → `dist/bioroffice.brxt` → Install Extension**

CLI:

```bash
biorouter extension install dist/bioroffice.brxt
```

## Build & test

```bash
scripts/build_brxt.sh                                   # → dist/bioroffice.brxt
python3 scripts/functional_test.py <installed-ext-dir>  # 24-check MCP test suite
```

See [CHECKLIST.md](CHECKLIST.md) for the full validation procedure.

## License

Extension code: Apache-2.0. Vendored OfficeCLI source and binaries:
Apache-2.0, © iOfficeAI contributors.
