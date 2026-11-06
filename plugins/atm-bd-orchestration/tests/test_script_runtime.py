"""Every executable script runs under `uv run --script` with the one inline-metadata header (#629).

The header, not the `python3` on PATH, decides the interpreter and dependencies of a script run; a script
that lacks it, a non-executable script, or a document that still prefixes a script with `python3` would put
the run back on PATH order.
"""
from __future__ import annotations

import os
import re
import runpy
import stat
import subprocess
import tomllib
from pathlib import Path

import install
import pytest
import yaml

PKG = Path(__file__).resolve().parents[1]
def _profile_script(path: Path) -> bool:
    return (path.parent.parent / "profile.toml").is_file()


SCRIPTS = sorted(p for p in PKG.glob("skills/*/scripts/*") if p.is_file() and p.read_bytes().startswith(b"#!")
                 and not p.read_bytes().startswith(b"#!/bin/sh") and not _profile_script(p))  # profile hooks retain their approved source headers
EXECUTABLES = [*SCRIPTS, PKG / "install.py"]
DOCUMENTS = sorted(p for p in PKG.rglob("*") if p.suffix in {".md", ".j2", ".yaml", ".json"}
                   and p.is_file() and "CHANGELOG" not in p.name and ".pytest_cache" not in p.parts)
PROBE_TIMEOUT_SECONDS = 30


def _captured_text(output: str | bytes | None) -> str:
    if output is None:
        return ""
    return output.decode(errors="replace") if isinstance(output, bytes) else output


def _run_uv_probe(command: list[str], *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, env=env, cwd=cwd,
                              timeout=PROBE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"command {command!r} timed out after {PROBE_TIMEOUT_SECONDS}s\n"
            f"partial stdout:\n{_captured_text(exc.stdout)}\n"
            f"partial stderr:\n{_captured_text(exc.stderr)}"
        ) from exc


def test_profile_exemptions_follow_manifests_and_suite_names(tmp_path):
    for name in ("alpha", "beta"):
        skill = tmp_path / "skills" / f"custom-{name}"
        (skill / "scripts").mkdir(parents=True)
        (skill / "profile.toml").write_text(f'name = "{name}"\n', encoding="utf-8")
        (tmp_path / "tests" / name).mkdir(parents=True)
        assert _profile_script(skill / "scripts" / "hook.py")
    ordinary = tmp_path / "skills" / "ordinary" / "scripts" / "script.py"
    ordinary.parent.mkdir(parents=True)
    assert not _profile_script(ordinary)
    suites = runpy.run_path(str(PKG / "conftest.py"))["_profile_suites"](tmp_path)
    assert set(suites) == {"tests/alpha", "tests/beta"}


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
    manifest = yaml.safe_load((PKG / "manifest.yaml").read_text())
    shipped = {PKG / path for path in manifest["artifacts"]["skills"] if "/scripts/" in path}
    assert SCRIPTS and set(SCRIPTS) <= shipped
    for path in EXECUTABLES:
        text = path.read_text(encoding="utf-8")
        assert text.startswith(install.SCRIPT_HEADER), f"{path.relative_to(PKG)} does not start with SCRIPT_HEADER"
        assert text.count("#!") == 1 or text.index("#!", 1) > len(install.SCRIPT_HEADER), path
        assert path.stat().st_mode & stat.S_IXUSR, f"{path.relative_to(PKG)} is not executable"


def test_library_modules_carry_no_shebang():
    for path in PKG.glob("skills/*/scripts/*.py"):
        if path not in SCRIPTS and not _profile_script(path):
            assert not path.read_text(encoding="utf-8").startswith("#!"), path


def test_no_document_runs_a_script_through_python3():
    pattern = re.compile(r"python3\s+\S*(scripts/|install\.py|\{\{ repair_script \}\})")
    hits = [f"{p.relative_to(PKG)}:{n}" for p in DOCUMENTS
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1) if pattern.search(line)]
    assert hits == []


def _run_python311_probe(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the actual script probe using the controlled environment rooted in tmp_path."""
    fake = tmp_path / "bin"
    fake.mkdir(parents=True)
    (fake / "python3").write_text("#!/bin/sh\necho 'Python 3.14.7'\n")
    (fake / "python3").chmod(0o755)
    probe = tmp_path / "probe.py"
    probe.write_text(install.SCRIPT_HEADER + "import sys, sc_compose, pydantic, yaml\nprint(sys.version_info[:2])\n")
    probe.chmod(0o755)
    env = {**os.environ, "PATH": f"{fake}{os.pathsep}{os.environ['PATH']}"}
    command = ["uv", "run", "--offline", "--python", "3.11", "--script", str(probe)]
    return _run_uv_probe(command, env=env, cwd=tmp_path)


def _assert_python311_probe_passes(run: subprocess.CompletedProcess[str]) -> None:
    assert run.returncode == 0, (
        f"stdout:\n{run.stdout}\nstderr:\n{run.stderr}\n"
        "If the Python 3.11 script environment is missing, run `just warm-py311` before the offline test."
    )
    assert run.stdout.strip() == "(3, 11)"


def test_a_script_runs_on_python_3_11_whatever_python3_is_on_path(tmp_path: Path) -> None:
    """The real runtime: `uv run --python 3.11` works with a 3.14 `python3` first on PATH."""
    _assert_python311_probe_passes(_run_python311_probe(tmp_path))


def test_empty_uv_cache_failure_names_warm_recipe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "empty-uv-cache"
    cache.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))

    run = _run_python311_probe(tmp_path / "cold-cache")
    with pytest.raises(AssertionError) as raised:
        _assert_python311_probe_passes(run)

    message = str(raised.value)
    assert "pydantic was not found in the cache" in message
    assert "run `just warm-py311`" in message


def test_uv_probe_timeout_reports_partial_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def expire(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert kwargs["timeout"] == PROBE_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(command, PROBE_TIMEOUT_SECONDS, output=b"partial stdout", stderr=b"partial stderr")

    monkeypatch.setattr(subprocess, "run", expire)
    command = ["uv", "run", "--offline", "--python", "3.11", "--script", "probe.py"]
    with pytest.raises(AssertionError) as raised:
        _run_uv_probe(command, env={}, cwd=tmp_path)

    message = str(raised.value)
    assert "uv" in message
    assert "partial stdout" in message
    assert "partial stderr" in message
