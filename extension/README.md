# BiorOffice

**Microsoft Office automation for BioRouter.** Create, read, analyze, and edit
Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) documents — with no
Microsoft Office installation.

BiorOffice packages the open-source [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)
engine (Apache-2.0) as a self-contained BioRouter extension (`.brxt`). The
extension's entry point locates the bundled engine binary, restores its
executable bit, and execs into `officecli mcp` — OfficeCLI's native MCP stdio
server — so BioRouter talks to the engine directly.

## What you get

- **One MCP tool — `officecli`** — covering create / view / get / query / set /
  add / remove / move / swap / validate / batch / raw / help / load_skill
  across all three formats.
- **Four bundled BioRouter skills**, auto-discovered when a session starts:
  - `bioroffice-office-suite` — core grammar, paths, help system
  - `bioroffice-word` — rich-formatted documents
  - `bioroffice-excel` — formulas, pivots, charts, conditional formatting
  - `bioroffice-powerpoint` — slides, shapes, charts, transitions
- **Dynamic specialized skills** loaded on demand by the agent via
  `load_skill` (word, academic-paper, pptx, pitch-deck, morph-ppt,
  morph-ppt-3d, excel, financial-model, data-dashboard).
- **Pinned engine** (v1.0.108) with SHA-256 verification; auto-download
  self-heal for platforms whose binary is not bundled.

## Install

In BioRouter: **Settings → Extensions → Install from .brxt** and pick
`bioroffice.brxt`, or from the CLI:

```bash
biorouter extension install bioroffice.brxt
```

BioRouter unzips the bundle to `~/.config/biorouter/extensions/bioroffice/`,
runs `uv sync`, and registers the stdio extension
(`uv run --directory <dir> bioroffice`).

## Environment variables (optional)

| Variable | Default | Purpose |
|---|---|---|
| `BIOROFFICE_OFFICECLI_PATH` | (empty) | Use a specific officecli binary instead of the bundled one |
| `OFFICECLI_SKIP_UPDATE` | `1` | Keep the engine pinned; set `0` to allow self-update |

## Requirements

- BioRouter with `uv` available on PATH (already required for .brxt extensions)
- Python ≥ 3.10 (resolved by `uv sync`)
- macOS arm64 binary is bundled; other platforms auto-download the pinned
  release on first launch (needs network once)

## License

Extension code: Apache-2.0. Bundled OfficeCLI binary: Apache-2.0,
© iOfficeAI contributors.
