"""Contract hook flows against a real embedded beads database and cache."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess

from atm_bd_core.store._cache_binding import cache_module as bd_cache_rs
import pytest
from atm_bd_core.store import CacheStore, PhaseFilesCli
from atm_bd_types import BeadPatch, ErrorId, HookRequest, Refusal, Status
from atm_bd_types._core import stack_of

from . import beads_db as beads_db_helpers
from .beads_db import bd, create_bead, init_db

ROOT = Path(__file__).resolve().parents[5]
SCRIPTS = ROOT / "crates/atm-bd-types/tests/fixtures/scripts"
SHA = "0123456789abcdef0123456789abcdef01234567"



def load_hook(name: str):
    path = SCRIPTS / f"atm-bd-task-{name}-hook.py"
    if name == "close":
        path = SCRIPTS / "atm-bd-task-hook.py"
    spec = importlib.util.spec_from_file_location(f"fixture_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.hook


def request(hook: str, actor: str, *, to=None, op=None, report=""):
    body = {"schema_version": "1.0.0", "hook": hook, "team": "t", "phase": "bo",
            "caller": {"identity": actor, "team": "t", "host": None}, "custom": {},
            "request": {"home_dir": "/h", "current_dir": "/r", "caller_identity": actor, "caller_team": "t",
                        "to": {"agent": to} if to else None, "message_source": {"Inline": report},
                        "requires_ack": False, "task_id": "tst-1", "task_op": op, "dry_run": False}}
    result = HookRequest.parse(json.dumps(body))
    assert isinstance(result, HookRequest), result
    return result


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    init_db(tmp_path)
    meta = json.dumps({"branch": "work", "stack_bead": "tst-stack"})
    create_bead(tmp_path, "tst-1", "work", "phase-bo,stage:dev", json.loads(meta))
    layers = json.dumps({"layers": [{"branch": "work", "head": SHA, "pr": 7, "base": "main"}]})
    create_bead(tmp_path, "tst-stack", "stack", "phase-bo,stage:stack", json.loads(layers))
    config = tmp_path / ".atm-bd"
    config.mkdir()
    (config / "phase-bo.toml").write_text('profile="lite"\nlead="lead"\n[templates]\n' +
        ''.join(f'{name}="{name}.j2"\n' for name in ("refuse", "dev-close", "qa-pass", "qa-findings")))
    for name in ("refuse", "dev-close", "qa-pass", "qa-findings"):
        (tmp_path / f"{name}.j2").write_text("fixed template")
    monkeypatch.chdir(tmp_path)
    binary = os.environ.get("ATM_TEST_BD", "bd")
    cache = bd_cache_rs.Cache(str(tmp_path), bd_binary=binary, scopes=["bo"])
    cache.sync("bo", 30)
    cache.close()
    if os.path.isabs(binary):
        bindir = tmp_path / "bin"
        bindir.mkdir()
        (bindir / "bd").symlink_to(binary)
        monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    store = CacheStore.for_phase("bo")
    assert isinstance(store, CacheStore), store
    yield tmp_path, store
    store.cache.close()


def test_three_hooks_assign_start_and_close_on_real_db(setup):
    root, store = setup
    phases = PhaseFilesCli()
    assert 'pass-through' in load_hook("assign")(request("task.assign", "lead", to="dev"), store, phases).to_json()
    assert store.show("tst-1").assignee == "dev"
    assert 'pass-through' in load_hook("start")(request("task.start", "dev"), store, phases).to_json()
    assert store.show("tst-1").status == Status.IN_PROGRESS
    reply = load_hook("close")(request("task.close", "dev", op={"op": "close", "outcome": "completed", "reason": "done"}, report="done"), store, phases)
    assert 'handled' in reply.to_json(), reply.to_json()
    assert store.show("tst-1").status == Status.CLOSED
    assert json.loads(bd(root, "show", "tst-1", "--json"))[0]["status"] == "closed"


def test_bd_helper_bounds_the_process_and_reports_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    command = ["fake-bd", "show", "tst-1", "--json"]
    observed: dict[str, object] = {}

    def timeout_run(args: list[str], **kwargs: object) -> None:
        observed["args"] = args
        observed.update(kwargs)
        raise subprocess.TimeoutExpired(args, timeout=beads_db_helpers.BD_TIMEOUT_SECONDS)

    monkeypatch.setenv("ATM_TEST_BD", "fake-bd")
    monkeypatch.setattr(beads_db_helpers.subprocess, "run", timeout_run)
    with pytest.raises(RuntimeError, match="fake-bd.*show.*tst-1.*--json"):
        bd(tmp_path, "show", "tst-1", "--json")

    assert observed["args"] == command
    assert observed["stdin"] == subprocess.DEVNULL
    assert observed["timeout"] == beads_db_helpers.BD_TIMEOUT_SECONDS


def test_stale_snapshot_is_a_typed_race(setup):
    _, store = setup
    snapshot = store.show("tst-1")
    assert store.update(BeadPatch.assign(snapshot, "dev"), "lead") is None
    error = store.update(BeadPatch.start(snapshot), "dev")
    assert isinstance(error, Refusal) and error.id == ErrorId.BEAD_RACED


def test_phase_failures_are_typed(setup):
    _, _store = setup
    phases = PhaseFilesCli()
    assert phases.load(".atm-bd/phase-bo.toml", "other").id == ErrorId.PROFILE_MISMATCH
    assert phases.load(".atm-bd/missing.toml", "lite").id == ErrorId.PHASE_UNREADABLE
    Path(".atm-bd/no-profile.toml").write_text('lead="lead"\n')
    error = phases.load(".atm-bd/no-profile.toml", "lite")
    assert error.id == ErrorId.PROFILE_MISMATCH
    assert 'add profile = "lite" to .atm-bd/no-profile.toml' in repr(error)


def test_backend_race_is_not_reported_as_success(setup):
    root, store = setup
    snapshot = store.show("tst-1")
    bd(root, "update", "tst-1", "--assignee", "other", "--actor", "lead")
    error = store.update(BeadPatch.start(snapshot), "dev")
    assert isinstance(error, Refusal) and error.id == ErrorId.BEAD_RACED


def test_qa_target_and_ready_views(setup):
    root, store = setup
    bd(root, "create", "qa", "--id", "tst-qa", "--labels", "phase-bo,stage:qa", "--metadata",
       json.dumps({"checked_bead": "tst-1"}))
    store.cache.sync("bo", 30)
    qa = store.show("tst-qa")
    assert store.target_layer(qa).head == SHA
    assert stack_of(store.show("tst-stack")).layers[0].head == SHA
    assert {b.id for b in store.list("bo")} == {"tst-1", "tst-stack", "tst-qa"}
    assert "tst-1" in {b.id for b in store.ready("bo")}


def test_pending_journal_warning_names_late_write(setup, monkeypatch):
    _, store = setup
    snapshot = store.show("tst-1")

    class PendingCache:
        def write(self, *_args):
            return {"seq": 1}

        def drain(self, *_args):
            return {"escalated": []}

        def entry(self, _seq):
            return {"state": "pending"}

        def close(self):
            pass

    monkeypatch.setattr(store, "cache", PendingCache())
    result = store.update(BeadPatch.start(snapshot), "dev")
    assert isinstance(result, Refusal) and result.id == ErrorId.CACHE_UNAVAILABLE
    assert "write journaled; may still apply; re-check bead tst-1 before retrying" in repr(result)


def test_missing_cache_root_names_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CacheStore.for_phase("bo")
    assert isinstance(result, Refusal)
    assert getattr(result, "id", None) == ErrorId.CACHE_UNAVAILABLE
    assert "no .beads directory" in repr(result)
    assert str(tmp_path.resolve()) in repr(result)


def test_qa_without_checked_bead_names_the_qa_bead(setup):
    root, store = setup
    create_bead(root, "tst-qa", "qa", "phase-bo,stage:qa", {})
    store.cache.sync("bo", 30)
    result = store.target_layer(store.show("tst-qa"))
    assert isinstance(result, Refusal) and result.id == ErrorId.CACHE_UNAVAILABLE
    assert "QA bead tst-qa has no checked bead or closed blocker" in repr(result)
