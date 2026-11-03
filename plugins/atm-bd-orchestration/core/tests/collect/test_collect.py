from types import SimpleNamespace

from atm_bd_core.collect import collect
from atm_bd_types import FactKind
from atm_bd_types._native import _phase_file


def test_failed_reads_remain_unknown(tmp_path, recorded_runner):
    templates = [(f"/r/{n}", "/r", b"ok") for n in range(4)]
    phase_file = _phase_file("lite", "lead", templates, [("integration_branch", "main")])

    class Cache:
        def list(self, phase):
            raise OSError("offline")

        def ready(self, phase):
            raise OSError("offline")

    runner = recorded_runner({"code": 1, "stderr": "unavailable"}, {"code": 1, "stderr": "unavailable"})
    facts = collect("bo", phase_file, SimpleNamespace(runner=runner, cache=Cache()), 123, tmp_path)
    assert runner.calls == [(["atm", "task", "list", "--all", "--json"], None),
                            (["git", "ls-remote", "--heads", "origin"], None)]
    assert facts.now == 123
    assert facts.beads is None and facts.ready is None and facts.tasks is None
    assert facts.reported_keys == []
    assert {FactKind.BEADS, FactKind.READY, FactKind.TASKS, FactKind.STACK} <= {error.kind for error in facts.errors}


def test_task_bead_mapping_uses_only_matching_task_ids(tmp_path, recorded_runner):
    import json

    from atm_bd_types import Stage, Status
    from atm_bd_types._native import _bead

    class Cache:
        def list(self, phase):
            return [_bead("bo-1", Status.OPEN, Stage.DEV)]
        def ready(self, phase):
            return []

    runner = recorded_runner(
        {"stdout": json.dumps([
            {"task_id": "bo-1", "assignee": "dev", "state": "active", "bead_id": "unrelated"},
            {"task_id": "outside", "assignee": "qa", "state": "assigned", "bead_id": "bo-1"},
        ])},
        {"stdout": '{"events": []}'},
        {"stdout": ""},
    )
    templates = [(f"/r/{n}", "/r", b"ok") for n in range(4)]
    phase_file = _phase_file("lite", "lead", templates, [("integration_branch", "main")])
    facts = collect("bo", phase_file, SimpleNamespace(runner=runner, cache=Cache()), 123, tmp_path)
    assert [(task.task_id, task.bead_id) for task in facts.tasks] == [("bo-1", "bo-1")]
    assert [event.task_id for event in facts.task_events] == ["bo-1"]
    assert runner.calls[1] == (["atm", "task", "events", "bo-1", "--all", "--json"], None)


def test_missing_stack_accessor_fails_module_load(monkeypatch):
    import builtins
    from pathlib import Path

    import atm_bd_core.collect as collect_module

    import pytest

    real_import = builtins.__import__
    def missing_accessor(name, *args, **kwargs):
        if name == "atm_bd_types._core":
            raise ImportError("missing stack accessor")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", missing_accessor)
    with pytest.raises(ImportError, match="missing stack accessor"):
        source = Path(collect_module.__file__).read_text(encoding="utf-8")
        exec(compile(source, collect_module.__file__, "exec"), {"__package__": "atm_bd_core.collect"})
