"""Every self-contained script declares the dependencies needed to start."""
from pathlib import Path
import subprocess

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
SCRIPT_PATHS = sorted(path for path in SCRIPTS.iterdir()
                      if path.is_file() and "# /// script" in path.read_text(encoding="utf-8", errors="replace")[:500])


@pytest.mark.parametrize("script", SCRIPT_PATHS, ids=lambda path: path.name)
def test_script_declared_dependencies_can_start(script):
    try:
        result = subprocess.run(["uv", "run", "--script", str(script), "--help"], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"SUBPROCESS.TIMEOUT: {script.name} --help exceeded {error.timeout}s", pytrace=False)
    output = result.stdout + result.stderr
    assert not any(marker in output for marker in ("ModuleNotFoundError", "ImportError", "Traceback")), output
