# BiorOffice — Comprehensive Validation Checklists

Four checklists cover the full lifecycle: **build → install → load → use**.
Run them top to bottom when releasing a new version of the extension or
after bumping the pinned OfficeCLI engine.

---

## 1. Bundle build & static validation

- [ ] `extension/manifest.json` parses as JSON and contains all required
      fields: `name`, `display_name`, `description`, `version`,
      `entry_point`, `repository`, `env_vars` (array, may be empty)
- [ ] `manifest.json` `entry_point` (`bioroffice`) matches
      `[project.scripts]` in `extension/pyproject.toml`
- [ ] `manifest.json` `version` matches `pyproject.toml` and
      `src/bioroffice/__init__.py`
- [ ] Engine pin consistent: `RELEASE_TAG` and `SHA256SUMS` in
      `src/bioroffice/cli.py` match `extension/bin/SHA256SUMS`
- [ ] Bundled binary checksum verifies:
      `cd extension/bin && shasum -a 256 -c <(grep mac-arm64 SHA256SUMS)`
- [ ] Bundled binary runs: `OFFICECLI_SKIP_UPDATE=1 extension/bin/officecli-mac-arm64 --version`
- [ ] Each `skills/<slug>/SKILL.md` starts with `---` YAML frontmatter
      containing single-line `name:` and `description:`
- [ ] `scripts/build_brxt.sh` succeeds and prints `BRXT structure OK`
- [ ] The `.brxt` zip has `manifest.json`, `README.md`, `pyproject.toml` at
      the archive **root** and a `src/` directory (BioRouter rejects it otherwise)
- [ ] `.venv/`, `__pycache__/`, `uv.lock`, `.DS_Store` are **not** in the zip
- [ ] Bundle size is sane (~11–12 MB compressed)

## 2. Install simulation (before touching a real BioRouter)

- [ ] Extract the `.brxt` to a temp dir **without preserving file modes**
      (mimics BioRouter's AdmZip extraction): binary must arrive
      non-executable
- [ ] `uv sync` completes cleanly in the extracted dir (< 120 s — BioRouter's
      install timeout)
- [ ] Launch exactly as BioRouter does:
      `uv run --directory <temp-dir> bioroffice`
  - [ ] Launcher log (stderr) shows `restored executable bit on …` —
        the exec-bit self-heal works
  - [ ] MCP `initialize` handshake returns serverInfo `officecli` at the
        pinned version
  - [ ] `tools/list` returns the `officecli` tool
  - [ ] A `tools/call` `create` writes a real file
- [ ] Functional suite passes (24 checks):
      `python3 scripts/functional_test.py <temp-dir>`

## 3. Real BioRouter installation (GUI + state)

- [ ] Back up `~/.config/biorouter/config.yaml` first
- [ ] Launch the dev app with Playwright debugging
      (`ENABLE_PLAYWRIGHT=true`, CDP port; or `just dev-ui-playwright`)
- [ ] Extensions tab → **Add Extension** opens the .brxt modal
- [ ] Selecting `bioroffice.brxt` shows the manifest preview card
      (BiorOffice, 1.0.0) and **Skills included** listing all 4 skills
- [ ] Configure step shows the two **optional** env vars; **Install
      Extension** is enabled without entering anything
- [ ] Install completes: modal closes, toast "Extension installed and enabled",
      no error banner
- [ ] On disk: `~/.config/biorouter/extensions/bioroffice/` contains
      `manifest.json`, `bin/officecli-mac-arm64`, `.venv/`, and
      `skills/*/SKILL.md`
- [ ] `config.yaml` gains a `bioroffice` stdio entry:
      `cmd: uv`, `args: [run, --directory, …/extensions/bioroffice, bioroffice]`,
      `enabled: true`
- [ ] BiorOffice appears in the Extensions list, toggled on

## 4. Live usage in BioRouter (agent-level)

- [ ] **Skills discovered:** Skills tab lists `bioroffice-office-suite`,
      `bioroffice-word`, `bioroffice-excel`, `bioroffice-powerpoint`
      (skills load dynamically at session start from
      `extensions/bioroffice/skills/`)
- [ ] **New chat session** starts with the extension enabled and the
      `officecli` tool available to the agent
- [ ] **PowerPoint:** agent creates a .pptx with titled slides, text shapes,
      and a table; `view outline` confirms structure; file opens in
      PowerPoint/Keynote
- [ ] **Word:** agent creates a .docx with Title/Heading styles, bold+colored
      run formatting, a styled table, header/footer, and a hyperlink;
      `view annotated` confirms formatting; file opens in Word/Pages
- [ ] **Excel:** agent creates an .xlsx with cross-sheet `VLOOKUP`, nested
      `IF`, `SUMIFS`, `SUMPRODUCT`, number formats, conditional formatting,
      a named range, and a chart; `get` on formula cells returns **computed
      values** (engine evaluates formulas at save); file opens in Excel/Numbers
- [ ] **Dynamic skill loading:** agent calls `load_skill` (`pptx` / `word` /
      `excel` / `financial-model` / …) and receives non-trivial guidance text
- [ ] **Validation:** `validate` reports each generated file OpenXML-valid;
      `view issues` reports no blocking problems
- [ ] **Uninstall path:** removing the extension deletes
      `~/.config/biorouter/extensions/bioroffice/` including bundled skills

---

## Automated coverage

| Checklist | Automated by |
|---|---|
| 1 + 2 | `scripts/build_brxt.sh` (structure) + `scripts/functional_test.py` (24 checks: dynamic skills, PPTX, DOCX, XLSX with formula readback, OpenXML validation) |
| 3 + 4 | `e2e/bioroffice-install.spec.ts` (Playwright, 9 tests: GUI install, disk/config assertions, skills tab, live agent chat creating a .pptx) |

## Known constraints

- The bundle ships only the **macOS arm64** engine binary; other platforms
  auto-download the pinned release (one-time network access) with SHA-256
  verification.
- BioRouter's zip extraction does not preserve the executable bit — the
  launcher restores it on every start (also covers manual unzips).
- `OFFICECLI_SKIP_UPDATE=1` (manifest default) keeps the engine pinned;
  set it to `0` in extension settings to allow self-update.
- `view screenshot` requires a headless browser on the host (Playwright /
  Chrome / Firefox); `view html` has no such dependency.
