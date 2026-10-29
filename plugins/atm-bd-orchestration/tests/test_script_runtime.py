"""Every executable script runs under `uv run --script` with the one inline-metadata header (#629).

The header, not the `python3` on PATH, decides the interpreter and dependencies of a script run; a script
that lacks it, a non-executable script, or a document that still prefixes a script with `python3` would put
the run back on PATH order.
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import tomllib
from pathlib import Path

import install

PKG = Path(__file__).resolve().parents[1]
SCRIPTS = sorted(p for p in PKG.glob("skills/*/scripts/*") if p.is_file() and p.read_bytes().startswith(b"#!")
                 and not p.read_bytes().startswith(b"#!/bin/sh"))  # `bead-queues` is a sh wrapper over `atm-bd queues`
EXECUTABLES = [*SCRIPTS, PKG / "install.py"]
DOCUMENTS = sorted(p for p in PKG.rglob("*") if p.suffix in {".md", ".j2", ".yaml", ".json"}
                   and p.is_file() and "CHANGELOG" not in p.name and ".pytest_cache" not in p.parts)


def test_the_header_is_pep_723_metadata_pinning_the_manifest_sc_compose_range():
    lines = install.SCRIPT_HEADER.splitlines()
    assert lines[0] == "#!/usr/bin/env -S uv run --script"
    assert lines[1] == "# /// script" and lines[-1] == "# ///"
    metadata = tomllib.loads("\n".join(line[2:] for line in lines[2:-1]))
    assert metadata["requires-python"] == ">=3.11,<3.12"
    floor, ceiling = install.sc_compose_range()
    assert f"sc-compose>={floor},<{ceiling}" in metadata["dependencies"]
    assert {dep.split(">")[0].split("=")[0] for dep in metadata["dependencies"]} == {"pydantic", "pyyaml", "sc-compose"}


def test_every_executable_script_starts_with_the_header_and_is_executable():
    assert len(SCRIPTS) >= 32
    for path in EXECUTABLES:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(install.SCRIPT_HEADER), f"{path.relative_to(PKG)} does not start with SCRIPT_HEADER"
        assert text.count("#!") == 1 or text.index("#!", 1) > len(install.SCRIPT_HEADER), path
        assert path.stat().st_mode & stat.S_IXUSR, f"{path.relative_to(PKG)} is not executable"


def test_library_modules_carry_no_shebang():
    for path in PKG.glob("skills/*/scripts/*.py"):
        if path not in SCRIPTS:
            assert not path.read_text(encoding="utf-8").startswith("#!"), path


def test_no_document_runs_a_script_through_python3():
    pattern = re.compile(r"python3\s+\S*(scripts/|install\.py|\{\{ repair_script \}\})")
    hits = [f"{p.relative_to(PKG)}:{n}" for p in DOCUMENTS
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1) if pattern.search(line)]
    assert hits == []


def test_a_script_runs_on_python_3_11_whatever_python3_is_on_path(tmp_path):
    """The real runtime: `uv run --script` resolves 3.11 and the wheel with a 3.14 `python3` first on PATH."""
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "python3").write_text("#!/bin/sh\necho 'Python 3.14.7'\n")
    (fake / "python3").chmod(0o755)
    probe = tmp_path / "probe.py"
    probe.write_text(install.SCRIPT_HEADER + "import sys, sc_compose, pydantic, yaml\nprint(sys.version_info[:2])\n")
    probe.chmod(0o755)
    env = {**os.environ, "PATH": f"{fake}{os.pathsep}{os.environ['PATH']}"}
    run = subprocess.run([str(probe)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "(3, 11)"
    assert sys.version_info[:2] == (3, 11)  # the suite's own interpreter, so the comparison is not vacuous
