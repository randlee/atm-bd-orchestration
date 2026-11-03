"""Exercise the stack fact against the shared embedded beads fixture."""

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

from atm_bd_core.collect import collect
from atm_bd_core.collect.beads import beads, stack
from atm_bd_core.store import CacheStore
from atm_bd_core.store._cache_binding import cache_module as bd_cache_rs
from atm_bd_types._core import stack_of
from atm_bd_types._native import _phase_file


def test_stack_from_embedded_cache(tmp_path, monkeypatch):
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
        templates = [(f"/r/{i}", "/r", b"ok") for i in range(4)]
        phase_file = _phase_file("lite", "lead", templates, [("integration_branch", "main")])
        fact, error = stack(entries, phase_file, stack_of)
        assert fact is not None and error is None
        assert fact.stack.layers[0].head == head
        assert fact.trunk == "main"

        class Runner:
            def run(self, argv, stdin):
                if argv[:3] == ["atm", "task", "list"]:
                    output = "[]"
                elif argv[:2] == ["git", "ls-remote"]:
                    output = f"{head}\trefs/heads/work\n"
                elif argv[:3] == ["git", "remote", "get-url"]:
                    output = "https://github.com/example/repo.git"
                elif argv[:2] == ["git", "merge-base"]:
                    output = ""
                elif "headRefOid" in argv:
                    output = head
                elif "baseRefName" in argv:
                    output = "main"
                elif "statusCheckRollup" in argv:
                    output = '["SUCCESS"]'
                else:
                    raise AssertionError(f"unexpected command {argv!r}")
                return SimpleNamespace(code=0, stdout=output, stderr="")

        facts = collect("bo", phase_file, SimpleNamespace(runner=Runner(), cache=store), 123, tmp_path)
        assert facts.errors == []
        assert facts.stack is not None and facts.stack.stack.layers[0].head == head
        assert facts.top_checks is not None and facts.top_checks.head == head
        assert facts.pr_bases is not None and facts.pr_bases[0].base == "main"
    finally:
        cache.close()
