"""Profile routing and monitor behavior with controlled tick inputs."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import atm_bd_core.tick as tick_module
import pytest
from atm_bd_types import ErrorId, HookReply, PhaseFacts, Refusal, Stage, Status, TaskEvents, TaskFact, TaskState
from atm_bd_types._core import Ports
from atm_bd_types._native import _bead

from atm_bd_console import cli, monitor
from atm_bd_console.result import ConfigInvalid
from atm_bd_console.state import StateStore


def _phase(root, text):
    directory = root / ".atm-bd"
    directory.mkdir(exist_ok=True)
    (directory / "phase-zz.toml").write_text(text, encoding="utf-8")


def _lite(root):
    skill = root / "skill"
    skill.mkdir()
    (skill / "profile.toml").write_text('name="lite"\nstages=["dev", "qa"]\npolicy="policy.toml"\n[hooks]\n[templates]\n', encoding="utf-8")
    (skill / "policy.toml").write_text('[params]\n', encoding="utf-8")
    (root / "templates").mkdir()
    lines = ['profile="lite"', 'profile_path="skill/profile.toml"', 'lead="lead"',
             'root="atm-phase-zz"', '[templates]']
    for name in ("refuse", "dev-close", "qa-pass", "qa-findings"):
        (root / "templates" / name).write_text("body", encoding="utf-8")
        lines.append(f'{name}="templates/{name}"')
    _phase(root, "\n".join(lines))


def test_route_selects_profile_or_existing_runner(tmp_path):
    _phase(tmp_path, 'lead="lead"\n')
    assert isinstance(monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor, monitor.TodayMonitor)
    _lite(tmp_path)
    assert isinstance(monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor, monitor.PolicyMonitor)


def test_missing_path_and_mismatched_profile_are_refused(tmp_path):
    _phase(tmp_path, 'profile="lite"\nlead="lead"\n')
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    refusal = selected._tick(dry_run=True)
    assert isinstance(refusal, Refusal) and refusal.id == ErrorId.PHASE_UNREADABLE
    assert "profile_path" in json.loads(HookReply.refused(refusal).to_json())["message"]
    _lite(tmp_path)
    path = tmp_path / ".atm-bd" / "phase-zz.toml"
    path.write_text(path.read_text().replace('profile="lite"', 'profile="other"'))
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    refusal = selected._tick(dry_run=True)
    assert isinstance(refusal, Refusal) and refusal.id == ErrorId.PROFILE_MISMATCH


def test_lite_tick_snapshot_and_dry_step(tmp_path, monkeypatch, capsys):
    _lite(tmp_path)
    calls = []
    class Runner:
        def run(self, argv, stdin):
            raise AssertionError(f"unexpected external command: {argv}")
    def collector(phase, phase_file, ports, now, state_dir):
        sprint = _bead("sprint1", Status.OPEN, Stage.OTHER)
        bead = _bead("b", Status.IN_PROGRESS, Stage.DEV, "agent", sprint="sprint1")
        task = TaskFact("b", "agent", TaskState.ACTIVE, "b")
        return PhaseFacts(phase, now, phase_file, [task], [TaskEvents("b", 2, 120)], [], [], [],
                          [sprint, bead], [], None, None, [], [])
    original = tick_module.tick
    def controlled(path, phase, primary, *, dry_run):
        calls.append(dry_run)
        return original(path, phase, primary, dry_run=dry_run, ports=Ports(Runner(), object()), now=123, collector=collector)
    monkeypatch.setattr(tick_module, "tick", controlled)
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    args = monitor.MonitorArgs("queues", phase="zz", json=True)
    assert selected.queues(args) == monitor.Exit.OK
    assert json.loads(capsys.readouterr().out) == {"phase": "zz", "rows": []}
    step = selected.step(selected._config(args), cli.INITIAL_STATE, False, cast(StateStore, object()))
    assert step[0].phase == "zz" and step[0].errors == ()
    assert step[0].agents[0].name == "agent" and step[0].agents[0].rows[0].task_id == "b"
    assert step[0].sprints[0].id == "sprint1"
    assert selected.snapshot(monitor.MonitorArgs("snapshot", phase="zz")) == monitor.Exit.OK
    assert list(tmp_path.rglob("snapshot.json"))
    assert calls == [True, True, True]


def test_policy_snapshot_preserves_non_profile_stage_kind(tmp_path):
    _lite(tmp_path)
    selected = monitor.route(tmp_path, monitor.MonitorArgs("snapshot", phase="zz"),
                             lambda _: 0, lambda *args: None)[0]
    assert isinstance(selected, monitor.PolicyMonitor)
    stage = SimpleNamespace(bead_id="work", stage=Stage.STACK, status=Status.OPEN, assignee="agent")
    sprint = SimpleNamespace(id="sprint1", title="Sprint", status=Status.OPEN, depends_on=[], steps=[stage])
    task = SimpleNamespace(task_id="work", assignee="agent", state=TaskState.ACTIVE, since=120)
    view = SimpleNamespace(generated_at=123, sprints=[sprint], rows=[], errors=[], tasks=[task],
                           root_id="atm-phase-zz", root_closed=False, lead="lead", top_ci=None)
    result = SimpleNamespace(view=view, facts=SimpleNamespace(beads=[]), decision=SimpleNamespace(actions=[]))

    snapshot = selected._snapshot(result, selected._config(monitor.MonitorArgs("snapshot", phase="zz")))

    assert snapshot.sprints[0].steps[0].kind == "stack"
    assert snapshot.agents[0].rows[0].kind == "stack"


def test_cli_has_one_monitor_route_and_no_specific_profile_names():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and node.func.attr == "route" and isinstance(node.func.value, ast.Name)
             and node.func.value.id == "monitor_source"]
    assert len(calls) == 1
    for path in (Path(cli.__file__), Path(monitor.__file__)):
        source_tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(isinstance(node, ast.Constant) and node.value in ("lite", "orchestration")
                       for node in ast.walk(source_tree))


def test_refusal_snapshot_preserves_id_and_wire_message(tmp_path):
    _phase(tmp_path, 'profile="lite"\nlead="lead"\n')
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    refusal = selected._tick(dry_run=True)
    assert isinstance(refusal, Refusal)
    expected = json.loads(HookReply.refused(refusal).to_json())["message"]
    snapshot = selected._snapshot(refusal, selected._config(monitor.MonitorArgs("snapshot", phase="zz")))
    error = snapshot.errors[0]
    assert isinstance(error, ConfigInvalid)
    assert error.key == refusal.id.name and error.value == expected


def test_cli_routes_profile_queues_once(tmp_path, monkeypatch, capsys):
    _lite(tmp_path)
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    calls = []
    def run(self, args):
        calls.append(args.phase)
        return monitor.Exit.OK
    monkeypatch.setattr(monitor.PolicyMonitor, "queues", run)
    assert cli.main(["queues", "--phase", "zz"]) == 0
    assert calls == ["zz"]
    assert capsys.readouterr().out == ""


def test_cron_dry_run_never_sends_and_live_tick_sends_only_decided_action(tmp_path, monkeypatch, capsys):
    from atm_bd_types._core import CommandResult

    _lite(tmp_path)
    manifest = tmp_path / "skill" / "profile.toml"
    manifest.write_text(manifest.read_text().replace('[hooks]', 'cron="cron.py"\n[hooks]'))
    (tmp_path / "skill" / "cron.py").write_text(
        'from atm_bd_types import Report\ndef decide(facts, params):\n return [Report("k", "q", None, "hello")]\n'
    )
    calls = []
    class Runner:
        def run(self, argv, stdin):
            calls.append((argv, stdin))
            return CommandResult(0, "", "")
    def collector(phase, phase_file, ports, now, state_dir):
        return PhaseFacts(phase, now, phase_file, [], [], [], [], [], [], [], None, None, [], [])
    original = tick_module.tick
    def controlled(path, phase, primary, *, dry_run):
        return original(path, phase, primary, dry_run=dry_run, ports=Ports(Runner(), object()), now=123, collector=collector)
    monkeypatch.setattr(tick_module, "tick", controlled)
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    assert selected.queues(monitor.MonitorArgs("queues", phase="zz", json=True)) == monitor.Exit.OK
    assert json.loads(capsys.readouterr().out)["rows"] == [{"queue": "q", "key": "k", "bead_id": None, "text": "hello"}]
    assert calls == []
    preview = selected.step(selected._config(monitor.MonitorArgs("console", phase="zz")), cli.INITIAL_STATE, False, cast(StateStore, object()))
    assert preview[0].sections[0].rows[0].reason == "hello" and calls == []
    assert selected.cron(monitor.MonitorArgs("cron", phase="zz", dry_run=True)) == monitor.Exit.OK
    assert calls == [] and json.loads(capsys.readouterr().out)["outcome"] == "DRY_RUN"
    assert not (tmp_path / ".atm-bd" / "state" / "phase-zz" / "executed.json").exists()
    assert selected.cron(monitor.MonitorArgs("cron", phase="zz", md_table=True)) == monitor.Exit.OK
    assert calls == [] and "| sprint |" in capsys.readouterr().out
    assert selected.cron(monitor.MonitorArgs("cron", phase="zz")) == monitor.Exit.OK
    assert calls == [(["atm", "send", "lead", "--stdin"], "[q] hello")]
    assert json.loads(capsys.readouterr().out)["outcome"] == "SENT"


def test_malformed_phase_fails_closed(tmp_path):
    _phase(tmp_path, 'profile = [broken')
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    refusal = selected._tick(dry_run=True)
    assert isinstance(refusal, Refusal) and refusal.id == ErrorId.PHASE_UNREADABLE


def test_policy_show_reads_its_configured_root_snapshot(tmp_path, monkeypatch, capsys):
    from datetime import UTC, datetime

    _lite(tmp_path)
    path = tmp_path / ".atm-bd" / "phase-zz.toml"
    path.write_text(path.read_text().replace('root="atm-phase-zz"', 'root="custom-root"'))
    class Runner:
        def run(self, argv, stdin):
            raise AssertionError(f"unexpected command {argv}")
    def collector(phase, phase_file, ports, now, state_dir):
        return PhaseFacts(phase, now, phase_file, [], [], [], [], [], [], [], None, None, [], [])
    original = tick_module.tick
    def controlled(path, phase, primary, *, dry_run):
        return original(path, phase, primary, dry_run=dry_run, ports=Ports(Runner(), object()), now=123, collector=collector)
    monkeypatch.setattr(tick_module, "tick", controlled)
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "now", lambda: datetime.fromtimestamp(124, UTC))
    assert cli.main(["snapshot", "--phase", "zz"]) == 0
    assert cli.main(["show", "--phase", "zz"]) == 0
    assert "zz" in capsys.readouterr().out


def test_queue_reports_incomplete_facts(tmp_path, monkeypatch, capsys):
    from atm_bd_types import CollectError, FactKind

    _lite(tmp_path)
    class Runner:
        def run(self, argv, stdin):
            raise AssertionError(f"unexpected command {argv}")
    def collector(phase, phase_file, ports, now, state_dir):
        error = CollectError(FactKind.BEADS, [], "offline", "restore cache")
        return PhaseFacts(phase, now, phase_file, [], [], [], [], [], None, None, None, None, [], [error])
    original = tick_module.tick
    def controlled(path, phase, primary, *, dry_run):
        return original(path, phase, primary, dry_run=dry_run, ports=Ports(Runner(), object()), now=123, collector=collector)
    monkeypatch.setattr(tick_module, "tick", controlled)
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    assert selected.queues(monitor.MonitorArgs("queues", phase="zz", json=True)) == monitor.Exit.UNAVAILABLE
    output = capsys.readouterr()
    assert "BEADS: offline; restore cache" in output.err
    assert json.loads(output.out)["rows"] == []


def test_failed_cron_action_returns_unavailable(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    _lite(tmp_path)
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    refusal = Refusal(ErrorId.BEAD_CLOSED, bead="b")
    action = SimpleNamespace(kind=SimpleNamespace(name="ASSIGN"), to="agent", bead_id="b", key="k")
    outcome = SimpleNamespace(kind=SimpleNamespace(name="FAILED"), failure=refusal)
    monkeypatch.setattr(selected, "_tick", lambda **kwargs: SimpleNamespace(
        view=SimpleNamespace(errors=[], actions=[action]), outcomes=[outcome]))
    assert selected.cron(monitor.MonitorArgs("cron", phase="zz")) == monitor.Exit.UNAVAILABLE
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "FAILED" and "BEAD_CLOSED" in output["error"]


def test_snapshot_holds_console_lock_and_persists_refusal(tmp_path, monkeypatch):
    from atm_bd_console.result import Err, LockHeld, Ok
    from atm_bd_console.state import acquire_lock, load_snapshot

    _lite(tmp_path)
    selected = monitor.route(tmp_path, monitor.MonitorArgs("queues", phase="zz"), lambda _: 0, lambda *args: None).monitor
    assert isinstance(selected, monitor.PolicyMonitor)
    refusal = Refusal(ErrorId.PHASE_UNREADABLE, path="phase", reason="broken")
    def controlled(**kwargs):
        locked = acquire_lock(tmp_path, "atm-phase-zz")
        assert isinstance(locked, Err) and isinstance(locked.error, LockHeld)
        return refusal
    monkeypatch.setattr(selected, "_tick", controlled)
    assert selected.snapshot(monitor.MonitorArgs("snapshot", phase="zz")) == monitor.Exit.CONFIG
    saved = load_snapshot(tmp_path, "atm-phase-zz")
    assert isinstance(saved, Ok) and isinstance(saved.value.errors[0], ConfigInvalid)
    assert saved.value.errors[0].key == refusal.id.name
    assert saved.value.errors[0].value == json.loads(HookReply.refused(refusal).to_json())["message"]


def test_policy_console_launches_with_monitor_step_and_config(tmp_path, monkeypatch):
    from atm_bd_console import app

    _lite(tmp_path)
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    seen = []
    monkeypatch.setattr(cli.atm_bd, "repo_config", lambda *_: cli.Ok(object()))
    monkeypatch.setattr(cli.shutil, "which", lambda _: "/fixture/bin")
    monkeypatch.setattr(cli, "_notification_startup_error", lambda _: None)
    def run(config, step, state, startup_error, **kwargs):
        seen.append((config, kwargs["runner_step"]))
        return 0
    monkeypatch.setattr(app, "run", run)
    assert cli.main(["console", "--phase", "zz"]) == 0
    config, callback = seen[0]
    assert config.phase == "zz" and Path(config.state_dir).name == "atm-phase-zz"
    assert isinstance(callback.__self__, monitor.PolicyMonitor)



@pytest.mark.parametrize("policy", [False, True], ids=["today", "policy"])
@pytest.mark.parametrize("failure", ["repo", "bd", "atm", "git", "notification"])
def test_console_startup_checks_apply_to_both_monitors(tmp_path, monkeypatch, policy, failure):
    from atm_bd_console import app
    from atm_bd_console.result import Err, NotFound, Ok

    if policy:
        _lite(tmp_path)
    config = monitor.PolicyMonitor(tmp_path, "zz", {})._config(monitor.MonitorArgs("console", phase="zz"))
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(cli.config_source, "load_config", lambda *_a, **_kw: Ok(config))
    error = NotFound("not_found", "test", "test fix")
    checks, launched = [], []
    def repo(root):
        checks.append(("repo", root))
        return Err(error) if failure == "repo" else Ok(object())
    def which(command):
        checks.append(("tool", command))
        return None if failure == command else "/fixture/bin"
    def notification(actual):
        checks.append(("notification", actual))
        return error if failure == "notification" else None
    monkeypatch.setattr(cli.atm_bd, "repo_config", repo)
    monkeypatch.setattr(cli.shutil, "which", which)
    monkeypatch.setattr(cli, "_notification_startup_error", notification)
    monkeypatch.setattr(app, "run", lambda actual, _step, _state, startup_error, **_kw: launched.append((actual, startup_error)) or 0)
    assert cli.main(["console", "--phase", "zz"]) == (0 if failure == "notification" else 3)
    assert checks[0] == ("repo", config.repo_root)
    if failure == "notification":
        assert checks[:4] == [("repo", config.repo_root), *(("tool", tool) for tool in ("bd", "atm", "git"))]
        assert checks[4][0] == "notification"
        assert launched == [(checks[4][1], error)]
    else:
        assert not launched


def test_policy_console_rejects_bad_configuration_before_launch(tmp_path, monkeypatch, capsys):
    from atm_bd_console import app

    _phase(tmp_path, 'profile="lite"\nlead="lead"\n')
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(app, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("launched")))
    assert cli.main(["console", "--phase", "zz"]) == 3
    assert "PHASE_UNREADABLE" in capsys.readouterr().out
    _lite(tmp_path)
    path = tmp_path / ".atm-bd" / "phase-zz.toml"
    path.write_text(path.read_text().replace('profile="lite"', 'profile="other"'))
    assert cli.main(["console", "--phase", "zz"]) == 3
    assert "PROFILE_MISMATCH" in capsys.readouterr().out


def test_cli_accepts_a_third_monitor_without_concrete_dispatch(monkeypatch, tmp_path):
    calls = []
    class OtherMonitor:
        def queues(self, args):
            calls.append(("queues", args.phase))
            return monitor.Exit.OK
        def snapshot(self, args):
            calls.append(("snapshot", args.phase))
            return monitor.Exit.OK
        def cron(self, args):
            calls.append(("cron", args.phase))
            return monitor.Exit.OK
        def step(self, config, state, force_github, store, cache=None):
            raise AssertionError("step is not needed for this check")
    other = OtherMonitor()
    def select(root, args, command, step):
        return monitor.Route(other, None, "custom-root", other.step, lambda _startup_error: calls.append(("console", args.phase)) or 0)
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(monitor, "route", select)
    for command in ("queues", "snapshot", "cron", "console"):
        assert cli.main([command, "--phase", "zz"]) == 0
    assert calls == [("queues", "zz"), ("snapshot", "zz"), ("cron", "zz"), ("console", "zz")]
    from atm_bd_console.result import Err, NotFound
    reads = []
    def load(root, root_id):
        reads.append(root_id)
        return Err(NotFound("not_found", root_id, "missing"))
    monkeypatch.setattr(cli, "load_snapshot", load)
    assert cli.main(["show", "--phase", "zz"]) == 2
    assert reads == ["custom-root"]
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert "PolicyMonitor" not in source and "TodayMonitor" not in source


def test_today_config_is_loaded_once_by_route_for_each_mode(tmp_path, monkeypatch):
    from atm_bd_console.result import Err, NotFound

    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)
    calls = []
    error = NotFound("not_found", "phase", "fix")
    def load(root, phase, **options):
        calls.append((root, phase, options))
        return Err(error)
    monkeypatch.setattr(cli.config_source, "load_config", load)
    for mode in ("console", "snapshot", "cron"):
        calls.clear()
        assert cli.main([mode, "--phase", "zz"]) == 3
        assert len(calls) == 1
        root, phase, options = calls[0]
        assert (root, phase) == (tmp_path, "zz")
        assert options["interval_s"] == (cli.config_source.CRON_CADENCE_S if mode == "cron" else None)
        assert options["dry_run"] == (mode == "snapshot")
    calls.clear()
    assert cli.main(["cron", "--phase", "zz", "--interval", "42", "--md-table"]) == 3
    assert len(calls) == 1 and calls[0][2]["interval_s"] == 42 and calls[0][2]["dry_run"]
    tree = ast.parse(Path(cli.__file__).read_text(encoding="utf-8"))
    assert not any(isinstance(node, ast.Attribute) and node.attr == "load_config" for node in ast.walk(tree))
    assert not any(isinstance(node, ast.FunctionDef) and node.name == "_cadence" for node in ast.walk(tree))
