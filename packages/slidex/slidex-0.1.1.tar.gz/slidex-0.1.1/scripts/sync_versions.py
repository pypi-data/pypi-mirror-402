from __future__ import annotations

import re
from pathlib import Path

import tomllib


def cargo_version(path: Path) -> str:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data["package"]["version"]


def sync_pyproject(pyproject: Path, version: str) -> bool:
    lines = pyproject.read_text(encoding="utf-8").splitlines(keepends=True)
    in_project = False
    changed = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue
        if in_project and stripped.startswith("version"):
            match = re.match(r"^(\s*version\s*=\s*)\"[^\"]*\"(\s*)$", line.rstrip())
            if match:
                prefix, suffix = match.groups()
                newline = "\n" if line.endswith("\n") else ""
                lines[idx] = f"{prefix}\"{version}\"{suffix}{newline}"
                changed = True
            break

    if changed:
        pyproject.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    version = cargo_version(repo_root / "Cargo.toml")
    pyproject = repo_root / "pyproject.toml"
    sync_pyproject(pyproject, version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
