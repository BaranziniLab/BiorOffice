"""
BiorOffice — Microsoft Office automation MCP server for BioRouter.

This launcher locates the OfficeCLI engine binary (bundled with the
extension, or downloaded on first use for platforms whose binary is not
bundled), ensures it is executable, and then hands the process over to
``officecli mcp`` — OfficeCLI's native MCP stdio server. BioRouter then
speaks MCP directly to the engine with no protocol translation layer.
"""

import hashlib
import os
import platform
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

# Pinned engine release. Bump RELEASE_TAG and SHA256SUMS together.
RELEASE_TAG = "v1.0.108"
DOWNLOAD_BASE = f"https://github.com/iOfficeAI/OfficeCLI/releases/download/{RELEASE_TAG}"

SHA256SUMS = {
    "officecli-linux-arm64": "904f335db3bbd0b24a74d87a44bc6adefa911c943d445ffb72989c3d7c66bd68",
    "officecli-linux-x64": "a6b020f8ef97f3eb4245d2a3bac3d4cf1fea8305c1031d4b67d53780f0317215",
    "officecli-mac-arm64": "7a58472396a1a44b1a5bdd4b46d302cb798ce1b15f412f9e76c37b5e146587a8",
    "officecli-mac-x64": "778173ea29d2533c3b92cfb2f5c3184deba9928e3fd870d8cb9e44901f1e599a",
    "officecli-win-arm64.exe": "4c583e396c108e4d0b2700e4266cd73f012797040121c9876194ae6a40e218fb",
    "officecli-win-x64.exe": "643485a71367c1e0389f4c7e6781976e2ab80c84a0d43491d3b9c3fddb727f62",
}


def _log(msg: str) -> None:
    # stdout carries the MCP protocol; diagnostics must go to stderr.
    print(f"[bioroffice] {msg}", file=sys.stderr, flush=True)


def binary_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
    if system == "darwin":
        return f"officecli-mac-{arch}"
    if system == "linux":
        return f"officecli-linux-{arch}"
    if system == "windows":
        return f"officecli-win-{arch}.exe"
    raise RuntimeError(f"Unsupported platform: {system}/{machine}")


def candidate_dirs() -> list:
    """Places the bundled bin/ directory may live, in priority order."""
    dirs = []
    # Editable install: src/bioroffice/cli.py -> extension root is parents[2]
    here = Path(__file__).resolve()
    for parent in (here.parents[2], here.parents[1]):
        dirs.append(parent / "bin")
    # `uv run --directory <ext-dir>` runs from the extension directory
    dirs.append(Path.cwd() / "bin")
    # Canonical BioRouter install location
    dirs.append(
        Path.home() / ".config" / "biorouter" / "extensions" / "bioroffice" / "bin"
    )
    # Deduplicate, preserving order
    seen, out = set(), []
    for d in dirs:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def ensure_executable(path: Path) -> None:
    if os.name != "nt" and not os.access(path, os.X_OK):
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        _log(f"restored executable bit on {path}")


def verify_checksum(path: Path, name: str) -> bool:
    expected = SHA256SUMS.get(name)
    if not expected:
        return True
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest == expected


def download_binary(name: str) -> Path:
    """Download the pinned engine binary for this platform (self-heal path
    for platforms whose binary is not bundled in the .brxt)."""
    for base in candidate_dirs():
        try:
            base.mkdir(parents=True, exist_ok=True)
            target = base / name
            url = f"{DOWNLOAD_BASE}/{name}"
            _log(f"downloading {url} -> {target}")
            tmp = target.with_suffix(target.suffix + ".part")
            urllib.request.urlretrieve(url, tmp)
            if not verify_checksum(tmp, name):
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"checksum mismatch for downloaded {name}")
            tmp.replace(target)
            ensure_executable(target)
            return target
        except OSError as exc:
            _log(f"cannot use {base}: {exc}")
            continue
    raise RuntimeError(f"could not download {name} into any writable location")


def resolve_binary() -> Path:
    override = os.environ.get("BIOROFFICE_OFFICECLI_PATH", "").strip()
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            ensure_executable(path)
            _log(f"using override binary {path}")
            return path
        _log(f"BIOROFFICE_OFFICECLI_PATH={override} does not exist; ignoring")

    name = binary_name()
    for base in candidate_dirs():
        path = base / name
        if path.is_file():
            if not verify_checksum(path, name):
                _log(f"checksum mismatch for {path}; ignoring")
                continue
            ensure_executable(path)
            _log(f"using bundled binary {path}")
            return path

    _log(f"no bundled {name} found; fetching pinned release {RELEASE_TAG}")
    return download_binary(name)


def main() -> None:
    # Keep the pinned engine deterministic unless the user opts out.
    os.environ.setdefault("OFFICECLI_SKIP_UPDATE", "1")
    binary = resolve_binary()
    _log(f"starting OfficeCLI MCP stdio server ({binary})")
    argv = [str(binary), "mcp"]
    if os.name == "nt":
        # exec semantics are unreliable for console stdio on Windows
        sys.exit(subprocess.call(argv))
    os.execv(str(binary), argv)


if __name__ == "__main__":
    main()
