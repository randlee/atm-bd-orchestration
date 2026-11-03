"""Controlled tests for profile-driven registration and the cron wire."""
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from atm_bd_core import cron_entry
from atm_bd_core.install import __main__ as installer
from atm_bd_core.install import sync
from atm_bd_core.profile import LoadedProfile, load_profile
from atm_bd_types import ErrorId, Profile, Refusal, Status

ROOT = Path(__file__).resolve().parents[5]
PROFILE = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/profile.toml"


def list_response(argv, calls, tmp_path):
    """Produce the bare-array shape returned by ATM's hook/cron list commands."""
    target = tmp_path / ".atm-bd/install/sample"
    phase = "sample"
    if argv[:3] == ["atm", "hook", "list"]:
        rows = [{"team": "test-team", "phase": phase, "hook": hook,
                 "module_path": str(target / f"{hook}.py"), "cwd": str(tmp_path),
                 "timeout_ms": 2500, "custom": {}, "active": True,
                 "registered_by": "lead", "registered_at": "2026-10-19T00:00:00Z", "disabled_at": None}
                for hook in ("task.assign", "task.start", "task.close")]
        return SimpleNamespace(stdout=json.dumps(rows))
    if argv[:3] == ["atm", "cron", "list"]:
        row = {"id": 1, "generation": 1, "team": "test-team", "phase": phase, "name": "profile",
               "cron_expr": "0 * * * * *", "module_path": str(target / "cron.py"), "cwd": str(tmp_path),
               "args": [str(target / "profile/profile.toml"), str(tmp_path)], "timeout_ms": 30000,
               "jitter_s": 0, "custom": {}, "stop": {"kind": "hook"}, "active": True,
               "created_by": "lead", "created_at": "2026-10-19T00:00:00Z",
               "last_run_at": None, "last_outcome": None, "ended_at": None}
        return SimpleNamespace(stdout=json.dumps([row]))
    return SimpleNamespace(stdout="")


def test_registers_each_declared_hook_and_cron_with_runtime_launchers(tmp_path, monkeypatch):
    calls = []
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    (phase_dir / "phase-sample.toml").write_text('profile = "lite"\n[templates]\n', encoding="utf-8")
    unrelated = '[atm]\ndefault_team = "other"\n\n[startup.unrelated]\nall = ["leave me alone"]\n'
    (tmp_path / ".atm.toml").write_text(unrelated, encoding="utf-8")
    def run(argv, **kwargs):
        calls.append(argv)
        return list_response(argv, calls, tmp_path)

    monkeypatch.setattr(installer.subprocess, "run", run)
    installer.install(PROFILE, tmp_path, "sample", ROOT, "0 * * * * *", "owner/repo")
    startup = (tmp_path / ".atm.toml").read_text(encoding="utf-8")
    assert startup.startswith(unrelated)
    installer.set_startup(tmp_path, load_profile(PROFILE))
    assert (tmp_path / ".atm.toml").read_text(encoding="utf-8") == startup
    entries = tomllib.loads(startup)["startup"]
    assert entries["unrelated"] == {"all": ["leave me alone"]}
    params = tomllib.loads((PROFILE.parent / "policy.toml").read_text(encoding="utf-8"))["params"]
    for agent, role in ((params["dev_agent"], "dev"), (params["qa_agent"], "qa"), (params["lead"], "lead")):
        [line] = entries[agent]["all"]
        assert line == (f"Your role is {role} in the lite profile. Work only from the assigned template; "
                        "do not load the full orchestration skill. Use atm task start and atm task close as the only "
                        "task transitions. Never write your own task bead. Run no cache commands; hooks refresh their reads.")
    config = tomllib.loads((phase_dir / "phase-sample.toml").read_text(encoding="utf-8"))
    assert config["repo"] == "owner/repo"
    path = Path(config["profile_path"])
    assert path.is_absolute() and path.is_file() and path == path.resolve()
    assert "templates" not in config
    registrations = [args for args in calls if args[:3] == ["atm", "hook", "register"]]
    sync_index = next(i for i, args in enumerate(calls) if args[1:3] == ["-m", "atm_bd_core.install.sync"])
    assert sync_index < calls.index(registrations[0])
    assert [args[3] for args in registrations] == ["task.assign", "task.start", "task.close"]
    for args in registrations:
        entry = Path(args[args.index("--module") + 1])
        assert installer.timeout(entry, "TIMEOUT_MS") == 2500
        assert "os.execv" in entry.read_text(encoding="utf-8")
    [cron] = [args for args in calls if args[:3] == ["atm", "cron", "start"]]
    assert "--until-hook" in cron and cron.count("--arg") == 2
    entry = Path(cron[cron.index("--module") + 1])
    assert installer.timeout(entry, "CRON_TIMEOUT_MS") == 30000


def test_failed_cache_initialization_does_not_register_hooks(tmp_path, monkeypatch):
    calls = []
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    (phase_dir / "phase-sample.toml").write_text('profile = "lite"\n', encoding="utf-8")

    def run(argv, **kwargs):
        calls.append(argv)
        if argv[1:3] == ["-m", "atm_bd_core.install.sync"]:
            raise subprocess.CalledProcessError(1, argv)

    monkeypatch.setattr(installer.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        installer.install(PROFILE, tmp_path, "sample", ROOT, "0 * * * * *", "owner/repo")
    assert not any(args[0] == "atm" for args in calls)


def test_cache_sync_must_be_current_and_closes_on_failure(monkeypatch):
    closed = []
    cache = SimpleNamespace(sync=lambda phase, timeout: {"model_current": False}, close=lambda: closed.append(True))
    monkeypatch.setattr(sync.cache_module, "Cache", lambda *args, **kwargs: cache)
    monkeypatch.setattr(sync.shutil, "which", lambda name: "/bin/bd")
    monkeypatch.setattr(sys, "argv", ["sync", "/repo", "phase"])
    with pytest.raises(SystemExit, match="sync incomplete"):
        sync.main()
    assert closed == [True]


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
        installer.install(PROFILE, tmp_path, "../other", ROOT, "0 * * * * *", "owner/repo")


def test_missing_repo_flag_refuses(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["installer", "profile.toml", "/repo", "bo", "--checkout", "/checkout"])
    with pytest.raises(SystemExit):
        installer.main()
    assert "--repo" in capsys.readouterr().err


def test_cron_tick_passes_profile_phase_and_primary(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(cron_entry, "tick", lambda *args: seen.append(args) or object())
    envelope = {"hook": "cron.tick", "phase": "bo", "request": {"created_by": "lead", "args": ["/profile", str(tmp_path)]}}
    assert cron_entry.handle(envelope) == {"result": "pass-through"}
    assert seen == [(Path("/profile"), "bo", tmp_path)]
    monkeypatch.setattr(cron_entry, "tick", lambda *args: Refusal(ErrorId.PROFILE_MISMATCH, error="bad"))
    assert cron_entry.handle(envelope)["result"] == "refused"


def test_cron_stop_only_when_root_bead_is_closed(monkeypatch, tmp_path):
    """ADR-069 D4 pins the atm-bd schedule stop condition to phase-root closure."""
    monkeypatch.setattr(cron_entry, "load_profile", lambda path: SimpleNamespace(profile=SimpleNamespace(name="x")))
    monkeypatch.setattr(cron_entry, "PhaseFilesCli", lambda: SimpleNamespace(
        load=lambda *args: SimpleNamespace(key=lambda name: "root")))
    monkeypatch.setattr(cron_entry.CacheStore, "for_phase", lambda phase: SimpleNamespace(
        show=lambda root: SimpleNamespace(status=Status.CLOSED)))
    request = {"hook": "cron.stop", "phase": "bo", "request": {"created_by": "lead", "args": ["/profile", str(tmp_path)]}}
    assert cron_entry.handle(request) == {"stop": True, "reason": "phase closed"}
    monkeypatch.setattr(cron_entry.CacheStore, "for_phase", lambda phase: SimpleNamespace(
        show=lambda root: SimpleNamespace(status=Status.OPEN)))
    assert cron_entry.handle(request) == {"stop": False}


def test_reinstall_reuses_venv_and_identical_active_hooks_and_cron(tmp_path, monkeypatch):
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    (phase_dir / "phase-sample.toml").write_text('profile = "lite"\n', encoding="utf-8")
    python = phase_dir / "install/sample/venv/bin/python"
    python.parent.mkdir(parents=True)
    python.touch()
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        if argv[:3] in (["atm", "hook", "register"], ["atm", "cron", "start"]):
            raise subprocess.CalledProcessError(3, argv)
        return list_response(argv, calls, tmp_path)

    monkeypatch.setattr(installer.subprocess, "run", run)
    installer.install(PROFILE, tmp_path, "sample", ROOT, "0 * * * * *", "owner/repo")
    assert not any(args[:2] == ["uv", "venv"] for args in calls)
    assert any(args[:3] == ["atm", "cron", "list"] for args in calls)


def test_cache_requirement_uses_core_project_source(tmp_path):
    revision = "a" * 40
    (tmp_path / "pyproject.toml").write_text(
        f'[tool.uv.sources]\nbd-cache-rs = {{ git = "https://example.test/cache", rev = "{revision}", '
        'subdirectory = "python/cache" }\n', encoding="utf-8")
    assert installer.cache_requirement(tmp_path) == (
        f"bd-cache-rs @ git+https://example.test/cache@{revision}#subdirectory=python/cache")


def test_startup_uses_arbitrary_declared_policy_parameters(tmp_path):
    policy = tmp_path / "policy.toml"
    policy.write_text('[params]\nworker_name = "worker"\nworker_message = "instructions"\n', encoding="utf-8")
    loaded = LoadedProfile(Profile("test", ["stage"], {}, {}, "policy.toml",
                                   startup={"worker_name": "worker_message"}), tmp_path)
    installer.set_startup(tmp_path, loaded)
    assert tomllib.loads((tmp_path / ".atm.toml").read_text(encoding="utf-8"))["startup"] == {
        "worker": {"all": ["instructions"]}}


def test_phase_paths_remove_template_tables_and_preserve_unrelated_tables(tmp_path):
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    path = phase_dir / "phase-sample.toml"
    path.write_text('[templates]\nold = "obsolete"\n  [templates.sub]\nkeep = "yes"\n'
                    '[unrelated]\nvalue = 7\n', encoding="utf-8")
    installer.set_phase_paths(tmp_path, "sample", PROFILE)
    result = tomllib.loads(path.read_text(encoding="utf-8"))
    assert "templates" not in result
    assert result["profile_path"] == str(PROFILE.resolve())
    assert result["unrelated"] == {"value": 7}


def test_rewrite_rejects_invalid_input_and_output_without_modifying_original(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('valid = "before"\n', encoding="utf-8")
    with pytest.raises(tomllib.TOMLDecodeError):
        installer._rewrite(path, lambda source: "invalid = [")
    assert path.read_text(encoding="utf-8") == 'valid = "before"\n'
    assert not path.with_suffix(".toml.tmp").exists()
    path.write_text("invalid = [", encoding="utf-8")
    with pytest.raises(tomllib.TOMLDecodeError):
        installer._rewrite(path, lambda source: pytest.fail("invalid input must not be transformed"))
    assert path.read_text(encoding="utf-8") == "invalid = ["


def test_startup_preserves_indented_nested_table(tmp_path):
    policy = tmp_path / "policy.toml"
    policy.write_text('[params]\nname = "worker"\nmessage = "new"\n', encoding="utf-8")
    path = tmp_path / ".atm.toml"
    path.write_text('[startup.worker]\nall = ["old"]\n  [startup.worker.extra]\nkeep = true\n',
                    encoding="utf-8")
    loaded = LoadedProfile(Profile("test", ["stage"], {}, {}, "policy.toml",
                                   startup={"name": "message"}), tmp_path)
    installer.set_startup(tmp_path, loaded)
    assert tomllib.loads(path.read_text(encoding="utf-8"))["startup"]["worker"] == {
        "all": ["new"], "extra": {"keep": True}}


def test_empty_final_templates_header_is_removed(tmp_path):
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    path = phase_dir / "phase-sample.toml"
    path.write_text("[templates]", encoding="utf-8")
    installer.set_phase_paths(tmp_path, "sample", PROFILE)
    assert "templates" not in tomllib.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name, source, expected", [
    ("TIMEOUT_MS", "TIMEOUT_MS = 1234\n", 1234),
    ("CRON_TIMEOUT_MS", "CRON_TIMEOUT_MS = 30000\n", 30000),
])
def test_timeout_reads_literal_without_executing_module(tmp_path, name, source, expected):
    module = tmp_path / "hook.py"
    module.write_text(source + "raise RuntimeError('must not execute')\n", encoding="utf-8")
    assert installer.timeout(module, name) == expected


@pytest.mark.parametrize("source", ["", "TIMEOUT_MS = 0\n", "TIMEOUT_MS = -1\n",
                                    "TIMEOUT_MS = True\n", "TIMEOUT_MS: int = 50\n",
                                    "TIMEOUT_MS = int('50')\n"])
def test_timeout_rejects_missing_or_invalid_declarations(tmp_path, source):
    module = tmp_path / "hook.py"
    module.write_text(source, encoding="utf-8")
    with pytest.raises(ValueError):
        installer.timeout(module, "TIMEOUT_MS")


@pytest.mark.parametrize("kind,mutation", [
    ("hook", "missing"), ("hook", "inactive"), ("hook", "wrong_module"), ("hook", "wrong_phase"),
    ("cron", "missing"), ("cron", "inactive"), ("cron", "wrong_module"), ("cron", "wrong_phase"),
    ("cron", "wrong_args"), ("cron", "wrong_stop"),
])
def test_registration_check_refuses_missing_or_wrong_rows(tmp_path, monkeypatch, kind, mutation):
    hooks = {name: tmp_path / f".atm-bd/install/sample/{name}.py"
             for name in ("task.assign", "task.start", "task.close")}
    target = tmp_path / ".atm-bd/install/sample"
    entry = target / "cron.py"
    cron_args = [str(target / "profile/profile.toml"), str(tmp_path)]

    def run(argv, **kwargs):
        response = list_response(argv, [], tmp_path)
        if argv[1] == kind:
            rows = json.loads(response.stdout)
            if mutation == "missing":
                rows.pop()
            else:
                row = rows[-1]
                if mutation == "inactive":
                    row["active"] = False
                elif mutation == "wrong_module":
                    row["module_path"] = "/other.py"
                elif mutation == "wrong_phase":
                    row["phase"] = "other"
                elif mutation == "wrong_args":
                    row["args"] = []
                else:
                    row["stop"] = {"kind": "manual"}
            return SimpleNamespace(stdout=json.dumps(rows))
        return response

    monkeypatch.setattr(installer.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="active"):
        installer.verify_registrations("sample", tmp_path, hooks, entry, "0 * * * * *", cron_args)


def test_registration_list_rejects_non_array(tmp_path, monkeypatch):
    monkeypatch.setattr(installer.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout='{"rows": []}'))
    with pytest.raises(ValueError, match="JSON array"):
        installer.list_registrations("hook", "sample")


def test_install_fails_when_registered_hook_is_absent(tmp_path, monkeypatch):
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    (phase_dir / "phase-sample.toml").write_text('profile = "lite"\n', encoding="utf-8")
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        response = list_response(argv, calls, tmp_path)
        if argv[:3] == ["atm", "hook", "list"]:
            rows = json.loads(response.stdout)
            rows.pop()
            return SimpleNamespace(stdout=json.dumps(rows))
        return response

    monkeypatch.setattr(installer.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="active hook task.close"):
        installer.install(PROFILE, tmp_path, "sample", ROOT, "0 * * * * *", "owner/repo")
    assert any(argv[:3] == ["atm", "cron", "start"] for argv in calls)
    assert any(argv[:3] == ["atm", "hook", "list"] for argv in calls)
    assert any(argv[:3] == ["atm", "cron", "list"] for argv in calls)


@pytest.mark.parametrize("mismatch", ["missing", "inactive", "phase", "hook", "module_path", "cwd", "timeout_ms", "custom"])
def test_reinstall_does_not_mask_nonmatching_hook_registration(tmp_path, monkeypatch, mismatch):
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    (phase_dir / "phase-sample.toml").write_text('profile = "lite"\n', encoding="utf-8")
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        if argv[:3] == ["atm", "hook", "register"]:
            raise subprocess.CalledProcessError(3, argv)
        response = list_response(argv, calls, tmp_path)
        if argv[:3] == ["atm", "hook", "list"]:
            rows = json.loads(response.stdout)
            if mismatch == "missing":
                rows.pop(0)
            elif mismatch == "inactive":
                rows[0]["active"] = False
            else:
                rows[0][mismatch] = (1 if mismatch == "timeout_ms" else {"unexpected": True} if mismatch == "custom" else "other")
            return SimpleNamespace(stdout=json.dumps(rows))
        return response

    monkeypatch.setattr(installer.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        installer.install(PROFILE, tmp_path, "sample", ROOT, "0 * * * * *", "owner/repo")
    assert not any(argv[:3] == ["atm", "cron", "start"] for argv in calls)
