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
