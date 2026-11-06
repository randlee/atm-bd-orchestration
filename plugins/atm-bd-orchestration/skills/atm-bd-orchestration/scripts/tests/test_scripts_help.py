"""Every self-contained script declares the dependencies needed to start."""
import ast
from pathlib import Path
import subprocess

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
SCRIPT_PATHS = sorted(path for path in SCRIPTS.iterdir()
                      if path.is_file() and "# /// script" in path.read_text(encoding="utf-8", errors="replace")[:500])


def has_main_entry(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
               and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
               and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq)
               and len(node.test.comparators) == 1 and isinstance(node.test.comparators[0], ast.Constant)
               and node.test.comparators[0].value == "__main__" for node in tree.body)


def test_script_population():
    python_files = set(SCRIPTS.glob("*.py"))
    main_entries = {path for path in python_files if has_main_entry(path)}
    selected = set(SCRIPT_PATHS)
    assert main_entries
    assert main_entries <= selected, f"Python entrypoints missing PEP 723 metadata: {main_entries - selected}"
    other_pep_scripts = {"phase_settings.py", "bead-groups", "bv-analyze", "fix-round-scope", "sanity-close-vars",
                         "sanity-merge", "sanity-run-history", "sanity-split", "sanity-stack-link"}
    assert selected == main_entries | {SCRIPTS / name for name in other_pep_scripts}
    excluded_libraries = {"bd_models.py", "bead_formulas.py", "command_timeout.py", "qa_reviewers.py",
                          "stack_top.py", "transitions.py"}
    excluded_shell_scripts = {"bead-queues"}
    assert {path.name for path in python_files - selected} == excluded_libraries
    shell_scripts = {path.name for path in SCRIPTS.iterdir()
                     if path.is_file() and path.read_bytes().startswith(b"#!/bin/sh\n")}
    assert shell_scripts == excluded_shell_scripts
    assert all(SCRIPTS / name not in selected for name in excluded_shell_scripts)


def test_cron_declares_its_script_dependencies():
    assert SCRIPTS / "bd_cache_cron.py" in SCRIPT_PATHS


@pytest.mark.parametrize("script", SCRIPT_PATHS, ids=lambda path: path.name)
def test_script_declared_dependencies_can_start(script):
    try:
        result = subprocess.run(["uv", "run", "--script", str(script), "--help"], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"SUBPROCESS.TIMEOUT: {script.name} --help exceeded {error.timeout}s", pytrace=False)
    output = result.stdout + result.stderr
    assert not any(marker in output for marker in ("ModuleNotFoundError", "ImportError", "Traceback")), output
