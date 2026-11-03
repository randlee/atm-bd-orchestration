"""Exercise the stack fact against the shared embedded beads fixture."""

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

from atm_bd_core.collect import collect
from atm_bd_core.collect.beads import beads, stack
from atm_bd_core.store import CacheStore
from atm_bd_core.store._cache_binding import cache_module as bd_cache_rs
from atm_bd_core import stack_of
from atm_bd_types._native import _phase_file


def test_stack_from_embedded_cache(tmp_path, monkeypatch, recorded_runner):
    helper_path = Path(__file__).resolve().parents[1] / "store" / "beads_db.py"
    spec = importlib.util.spec_from_file_location("beads_db", helper_path)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.init_db(tmp_path)
    head = "a" * 40
    helper.create_bead(tmp_path, "tst-stack", "stack", "phase-bo,stage:stack", {
        "layers": [{"branch": "work", "head": head, "pr": 7, "base": "main"}],
    })
    monkeypatch.chdir(tmp_path)
    cache = bd_cache_rs.Cache(str(tmp_path), bd_binary=os.environ.get("ATM_TEST_BD", "bd"), scopes=["bo"])
    try:
        cache.sync("bo", 30)
        store = CacheStore(cache, "bo")
        entries, error = beads(store, "bo")
        assert entries is not None and error is None
        templates = [(f"/r/{i}", "/r", b"ok") for i in range(5)]
        phase_file = _phase_file("lite", "lead", templates, [("integration_branch", "main")])
        fact, error = stack(entries, phase_file, stack_of)
        assert fact is not None and error is None
        assert fact.stack.layers[0].head == head
        assert fact.trunk == "main"

        runner = recorded_runner(
            {"stdout": "[]"},
            {"stdout": f"{head}\trefs/heads/work\n"},
            {"stdout": ""},
            {"stdout": "https://github.com/example/repo.git"},
            {"stdout": "main"},
            {"stdout": head},
            {"stdout": '["SUCCESS"]'},
            {"stdout": head},
        )
        facts = collect("bo", phase_file, SimpleNamespace(runner=runner, cache=store), 123, tmp_path)
        assert runner.calls == [
            (["atm", "task", "list", "--all", "--json"], None),
            (["git", "ls-remote", "--heads", "origin"], None),
            (["git", "merge-base", "--is-ancestor", "origin/main", "origin/work"], None),
            (["git", "remote", "get-url", "origin"], None),
            (["gh", "pr", "view", "7", "--json", "baseRefName", "--jq", ".baseRefName"], None),
            (["gh", "pr", "view", "7", "--json", "headRefOid", "--jq", ".headRefOid"], None),
            (["gh", "pr", "view", "7", "--json", "statusCheckRollup", "--jq", "[.statusCheckRollup[] | .conclusion // .state // .status]"], None),
            (["gh", "pr", "view", "7", "--json", "headRefOid", "--jq", ".headRefOid"], None),
        ]
        assert facts.errors == []
        assert facts.stack is not None and facts.stack.stack.layers[0].head == head
        assert facts.top_checks is not None and facts.top_checks.head == head
        assert facts.pr_bases is not None and facts.pr_bases[0].base == "main"
    finally:
        cache.close()
