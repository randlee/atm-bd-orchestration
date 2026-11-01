# pyright: strict
"""Keep every Python source and Python entry point in pyright's input set."""
from __future__ import annotations

import json
from pathlib import Path


def test_python_inputs_are_all_included() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "pyrightconfig.json").read_text())
    included = [root / item for item in config["include"]]
    missing: list[str] = []
    for directory in ("plugins", "apps/atm-bd-console", "release_scripts", ".github/scripts"):
        for path in (root / directory).rglob("*"):
            if not path.is_file() or any(part in {".venv", "__pycache__", ".pytest_cache", "node_modules"} for part in path.parts):
                continue
            with path.open("rb") as source:
                first = source.readline()
            if path.suffix != ".py" and not (first.startswith(b"#!") and (b"python" in first or b"uv run --script" in first)):
                continue
            if not any(path == item or (item.is_dir() and path.is_relative_to(item) and path.suffix == ".py")
                       for item in included):
                missing.append(str(path.relative_to(root)))
    assert not missing, f"Python files missing from pyright include: {missing}"
