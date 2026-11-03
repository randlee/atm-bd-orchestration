"""pyright strict, 0 errors, on the contract's three lite hooks and its cron script against the generated stub."""

from __future__ import annotations

import json
import subprocess
import sys

from conftest import CRATE

CONFIG = CRATE / "tests" / "pyright" / "pyrightconfig.json"
SCRIPTS = CRATE / "tests" / "fixtures" / "scripts"


def test_lite_scripts_type_check_strict_against_generated_stub() -> None:
    result = subprocess.run([sys.executable, "-m", "pyright", "--outputjson", "-p", str(CONFIG)],
                            capture_output=True, text=True, check=False)
    report = json.loads(result.stdout)
    errors = [f"{d['file']}:{d['range']['start']['line'] + 1}: {d['message']}"
              for d in report["generalDiagnostics"] if d["severity"] == "error"]
    assert errors == [], "\n".join(errors) + result.stderr
    assert report["summary"]["filesAnalyzed"] == len(list(SCRIPTS.glob("*.py"))) == 4
    assert result.returncode == 0, result.stderr
