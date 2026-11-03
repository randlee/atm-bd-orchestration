"""pyright strict, 0 errors, on the contract's three lite hooks and its cron script against the generated stub."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
from conftest import CRATE

CONFIG = CRATE / "tests" / "pyright" / "pyrightconfig.json"
SCRIPTS = CRATE / "tests" / "fixtures" / "scripts"


def _run_pyright():
    try:
        result = subprocess.run([sys.executable, "-m", "pyright", "--outputjson", "-p", str(CONFIG)],
                                capture_output=True, text=True, check=False, timeout=120)
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"pyright timed out; stdout: {exc.stdout!r}; stderr: {exc.stderr!r}", pytrace=False)
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"pyright returned invalid JSON: {exc}; stdout: {result.stdout!r}; stderr: {result.stderr!r}",
                    pytrace=False)
    return result, report


def test_lite_scripts_type_check_strict_against_generated_stub() -> None:
    result, report = _run_pyright()
    errors = [f"{d['file']}:{d['range']['start']['line'] + 1}: {d['message']}"
              for d in report["generalDiagnostics"] if d["severity"] == "error"]
    assert errors == [], "\n".join(errors) + result.stderr
    assert report["summary"]["filesAnalyzed"] == len(list(SCRIPTS.glob("*.py"))) == 4
    assert result.returncode == 0, result.stderr


def test_pyright_timeout_reports_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 120
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output=b"partial stdout", stderr=b"partial stderr")

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(pytest.fail.Exception, match="partial stdout.*partial stderr"):
        _run_pyright()


def test_pyright_invalid_json_reports_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    def malformed(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="not JSON", stderr="diagnostic stderr")

    monkeypatch.setattr(subprocess, "run", malformed)
    with pytest.raises(pytest.fail.Exception, match="not JSON.*diagnostic stderr"):
        _run_pyright()
