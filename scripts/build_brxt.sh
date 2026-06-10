#!/usr/bin/env bash
# Build dist/bioroffice.brxt from the extension/ directory.
# A .brxt is a ZIP with manifest.json, README.md, pyproject.toml, and src/ at
# the archive root. We also ship bin/ (the OfficeCLI engine) and skills/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT="$ROOT/extension"
DIST="$ROOT/dist"
OUT="$DIST/bioroffice.brxt"

for required in manifest.json README.md pyproject.toml src; do
  [ -e "$EXT/$required" ] || { echo "missing $EXT/$required" >&2; exit 1; }
done

python3 - "$EXT" "$OUT" <<'EOF'
import sys, zipfile, pathlib

ext, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", ".pytest_cache", "dist"}
EXCLUDE_FILES = {".DS_Store", "uv.lock"}

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(ext.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ext)
        if EXCLUDE_DIRS & set(rel.parts) or rel.name in EXCLUDE_FILES:
            continue
        zi = zipfile.ZipInfo.from_file(path, rel.as_posix())
        zi.compress_type = zipfile.ZIP_DEFLATED
        # Preserve the unix mode (incl. executable bit) for unzip tools that honor it.
        zi.external_attr = (path.stat().st_mode & 0xFFFF) << 16
        zf.writestr(zi, path.read_bytes())

names = zf.namelist() if False else None
print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
EOF

# Sanity-check required entries at archive root
python3 - "$OUT" <<'EOF'
import sys, zipfile
names = set(zipfile.ZipFile(sys.argv[1]).namelist())
required = ["manifest.json", "README.md", "pyproject.toml"]
missing = [r for r in required if r not in names]
if not any(n.startswith("src/") for n in names):
    missing.append("src/")
if missing:
    sys.exit(f"BRXT INVALID — missing: {missing}")
print("BRXT structure OK:", sorted(n for n in names if "/" not in n))
EOF
