# pyright: strict
"""Generated Rust error stubs let pyright detect a missing detail variant."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_missing_detail_variant_fails_pyright(tmp_path: Path) -> None:
    pyright = shutil.which("pyright")
    assert pyright is not None
    (tmp_path / "pyrightconfig.json").write_text(json.dumps({"typeCheckingMode": "strict", "reportMatchNotExhaustive": "error"}))
    path = tmp_path / "check.py"
    variants = ("CommandFailed", "Timeout", "Rejected", "Unreachable", "ParseFailed", "NotFound", "ConfigInvalid", "LockHeld", "IoFailed")

    def check(selected: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        cases = "".join(f"        case ErrorDetail.{name}(): pass\n" for name in selected)
        path.write_text("from atm_bd_types import Error, ErrorDetail\n\ndef check(error: Error) -> None:\n    match error.detail:\n" + cases + "        case None: pass\n")
        return subprocess.run([pyright, "--project", str(tmp_path), "--pythonpath", sys.executable],
                              capture_output=True, text=True, timeout=60, check=False)

    complete = check(variants)
    assert complete.returncode == 0, complete.stdout + complete.stderr
    incomplete = check(variants[:-1])
    assert incomplete.returncode != 0
    assert "reportMatchNotExhaustive" in incomplete.stdout and "IoFailed" in incomplete.stdout
