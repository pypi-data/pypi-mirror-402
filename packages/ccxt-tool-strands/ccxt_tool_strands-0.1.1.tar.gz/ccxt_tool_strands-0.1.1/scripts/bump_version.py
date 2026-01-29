from __future__ import annotations

import re
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def bump_patch(version: str) -> str:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version.strip())
    if not m:
        raise SystemExit(f"Unsupported version format: {version!r}")
    major, minor, patch = map(int, m.groups())
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r"^version\s*=\s*\"([^\"]+)\"\s*$", text, re.M)
    if not m:
        raise SystemExit("Could not find version in pyproject.toml")

    old = m.group(1)
    new = bump_patch(old)

    text2 = re.sub(
        r"^version\s*=\s*\"([^\"]+)\"\s*$",
        f'version = "{new}"',
        text,
        flags=re.M,
        count=1,
    )

    PYPROJECT.write_text(text2, encoding="utf-8")
    print(new)


if __name__ == "__main__":
    main()
