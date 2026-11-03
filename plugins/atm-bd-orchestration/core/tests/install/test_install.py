"""Controlled tests for profile-driven registration and the cron wire."""
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from atm_bd_core import cron_entry
from atm_bd_core.install import __main__ as installer
from atm_bd_types import ErrorId, Refusal, Status

ROOT = Path(__file__).resolve().parents[5]
PROFILE = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/profile.toml"


def test_registers_each_declared_hook_and_cron_with_runtime_launchers(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(installer.subprocess, "run", lambda argv, **kwargs: calls.append(argv))
    installer.install(PROFILE, tmp_path, "sample", ROOT, "0 * * * * *")
    registrations = [args for args in calls if args[:3] == ["atm", "hook", "register"]]
    assert [args[3] for args in registrations] == ["task.assign", "task.start", "task.close"]
    for args in registrations:
        entry = Path(args[args.index("--module") + 1])
        assert installer.timeout(entry, "TIMEOUT_MS") == 2500
        assert "os.execv" in entry.read_text(encoding="utf-8")
    [cron] = [args for args in calls if args[:3] == ["atm", "cron", "start"]]
    assert "--until-hook" in cron and cron.count("--arg") == 2
    entry = Path(cron[cron.index("--module") + 1])
    assert installer.timeout(entry, "CRON_TIMEOUT_MS") == 30000


def test_launcher_forwards_stdin_stdout_and_exit(tmp_path):
    child = tmp_path / "child.py"
    child.write_text('import sys\nprint(sys.stdin.read(), end="")\nsys.exit(7)\n', encoding="utf-8")
    entry = tmp_path / "entry.py"
    installer.launcher(entry, Path(sys.executable), child, 2500)
    result = subprocess.run([sys.executable, str(entry)], input="payload", text=True, capture_output=True, check=False)
    assert result.stdout == "payload" and result.returncode == 7


def test_invalid_phase_is_rejected_before_side_effects(tmp_path, monkeypatch):
    monkeypatch.setattr(installer.subprocess, "run", lambda *args, **kwargs: pytest.fail("unexpected command"))
    with pytest.raises(ValueError, match="path component"):
        installer.install(PROFILE, tmp_path, "../other", ROOT, "0 * * * * *")


def test_cron_tick_passes_profile_phase_and_primary(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(cron_entry, "tick", lambda *args: seen.append(args) or object())
    envelope = {"hook": "cron.tick", "phase": "bo", "request": {"args": ["/profile", str(tmp_path)]}}
    assert cron_entry.handle(envelope) == {"result": "pass-through"}
    assert seen == [(Path("/profile"), "bo", tmp_path)]
    monkeypatch.setattr(cron_entry, "tick", lambda *args: Refusal(ErrorId.PROFILE_MISMATCH, error="bad"))
    assert cron_entry.handle(envelope)["result"] == "refused"


def test_cron_stop_only_when_root_bead_is_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(cron_entry, "load_profile", lambda path: SimpleNamespace(profile=SimpleNamespace(name="x")))
    monkeypatch.setattr(cron_entry, "PhaseFilesCli", lambda: SimpleNamespace(
        load=lambda *args: SimpleNamespace(key=lambda name: "root")))
    monkeypatch.setattr(cron_entry.CacheStore, "for_phase", lambda phase: SimpleNamespace(
        show=lambda root: SimpleNamespace(status=Status.CLOSED)))
    request = {"hook": "cron.stop", "phase": "bo", "request": {"args": ["/profile", str(tmp_path)]}}
    assert cron_entry.handle(request) == {"stop": True, "reason": "phase closed"}
    monkeypatch.setattr(cron_entry.CacheStore, "for_phase", lambda phase: SimpleNamespace(
        show=lambda root: SimpleNamespace(status=Status.OPEN)))
    assert cron_entry.handle(request) == {"stop": False}
