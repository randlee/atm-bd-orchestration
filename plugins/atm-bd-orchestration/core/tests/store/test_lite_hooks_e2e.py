"""Contract hook flows against a real embedded beads database and cache."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest
from atm_bd_core.profile import TEMPLATES
from atm_bd_core.store import CacheStore, PhaseFilesCli
from atm_bd_core.store._cache_binding import cache_module as bd_cache_rs
from atm_bd_types import BeadPatch, ErrorId, Hook, HookRequest, Refusal, Status
from atm_bd_core import stack_of

from . import beads_db as beads_db_helpers
from .beads_db import bd, create_bead, init_db, require_test_bd_binary

ROOT = Path(__file__).resolve().parents[5]
SCRIPTS = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts"
SHA = "0123456789abcdef0123456789abcdef01234567"



def load_hook(name: str):
    path = SCRIPTS / f"atm-bd-task-{name}-hook.py"
    if name == "close":
        path = SCRIPTS / "atm-bd-task-hook.py"
    spec = importlib.util.spec_from_file_location(f"shipped_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.hook


def request(hook: str, actor: str, *, to=None, op=None, report="", task_id="tst-1"):
    body = {"schema_version": "1.0.0", "hook": hook, "team": "t", "phase": "bo",
            "caller": {"identity": actor, "team": "t", "host": None}, "custom": {},
            "request": {"home_dir": "/h", "current_dir": "/r", "caller_identity": actor, "caller_team": "t",
                        "to": {"agent": to} if to else None, "message_source": {"Inline": report},
                        "requires_ack": False, "task_id": task_id, "task_op": op, "dry_run": False}}
    result = HookRequest.parse(json.dumps(body))
    assert isinstance(result, HookRequest), result
    return result


def write_profile_config(root: Path) -> None:
    profile = root / "profile"
    templates = profile / "templates"
    templates.mkdir(parents=True)
    lines = ['name = "lite"', 'stages = ["dev"]', 'policy = "policy.toml"', "[hooks]", "[templates]"]
    for name in TEMPLATES:
        relative = f"templates/{name}.j2"
        (profile / relative).write_text("fixed template", encoding="utf-8")
        lines.append(f'{name} = "{relative}"')
    (profile / "policy.toml").write_text("[params]\n", encoding="utf-8")
    (profile / "profile.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    config = root / ".atm-bd"
    config.mkdir(exist_ok=True)
    (config / "phase-bo.toml").write_text(
        'profile="lite"\nprofile_path="profile/profile.toml"\nlead="lead"\n', encoding="utf-8")


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cache = ControlledCache()
    cache.add_bead("tst-1", "work", "open", ["phase-bo", "stage:dev"],
                   {"branch": "work", "stack_bead": "tst-stack"})
    cache.add_bead("tst-stack", "stack", "open", ["phase-bo", "stage:stack"],
                   {"layers": [{"branch": "work", "head": SHA, "pr": 7, "base": "main"}]})
    write_profile_config(tmp_path)
    monkeypatch.chdir(tmp_path)
    store = CacheStore(cache, "bo")
    yield tmp_path, store


@pytest.fixture
def real_db_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    binary = require_test_bd_binary()
    init_db(tmp_path)
    meta = {"branch": "work", "stack_bead": "tst-stack"}
    create_bead(tmp_path, "tst-1", "work", "phase-bo,stage:dev", meta)
    layers = {"layers": [{"branch": "work", "head": SHA, "pr": 7, "base": "main"}]}
    create_bead(tmp_path, "tst-stack", "stack", "phase-bo,stage:stack", layers)
    write_profile_config(tmp_path)
    monkeypatch.chdir(tmp_path)
    if os.path.isabs(binary):
        bindir = tmp_path / "bin"
        bindir.mkdir()
        (bindir / "bd").symlink_to(binary)
        monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    cache = bd_cache_rs.Cache(str(tmp_path), bd_binary=binary, scopes=["bo"])
    cache.sync("bo", 30)
    store = CacheStore(cache, "bo")
    assert isinstance(store, CacheStore), store
    yield tmp_path, store
    store.cache.close()


class ControlledCache:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.outcomes: list[tuple[str, list[dict]]] = []
        self.seq = 0
        self.state = "applied"
        self.escalated: list[dict] = []

    def add_bead(self, bead_id: str, title: str, status: str, labels: list[str], metadata: dict) -> None:
        self.rows[bead_id] = {"id": bead_id, "title": title, "status": status, "labels": labels,
                              "metadata": metadata, "dependencies": [], "assignee": None}

    def get(self, bead_id: str) -> dict:
        return {"row": {"bead": self.rows[bead_id], "blocked": []}}

    def refresh(self, ids, timeout):
        return [self.get(bead_id)["row"] for bead_id in ids]

    def list(self, _phase: str) -> dict:
        return {"rows": [{"bead": row} for row in self.rows.values()]}

    def ready(self, phase: str) -> dict:
        return {"ready": self.list(phase)["rows"]}

    def write(self, bead_id: str, operation: str, args: dict, *_rest) -> dict:
        self.seq += 1
        self.state, self.escalated = self.outcomes.pop(0) if self.outcomes else ("applied", [])
        if self.state == "applied":
            row = self.rows[bead_id]
            if operation == "close":
                row["status"] = "closed"
            row.update({key: value for key, value in args.items() if key in ("status", "assignee")})
        return {"seq": self.seq}

    def drain(self, *_args) -> dict:
        return {"escalated": self.escalated}

    def entry(self, _seq: int) -> dict:
        return {"state": self.state}

    def sync(self, *_args) -> None:
        pass

    def close(self) -> None:
        pass


class InstrumentedCache(ControlledCache):
    def __init__(self) -> None:
        super().__init__()
        self.get_calls: list[str] = []
        self.list_phases: list[str] = []
        self.ready_phases: list[str] = []

    def get(self, bead_id: str) -> dict:
        self.get_calls.append(bead_id)
        return super().get(bead_id)

    def list(self, phase: str) -> dict:
        self.list_phases.append(phase)
        return {"rows": [{"bead": row, "blocked": []} for row in self.rows.values()
                         if phase in row["labels"]]}

    def ready(self, phase: str) -> dict:
        self.ready_phases.append(phase)
        return {"ready": self.list(phase)["rows"]}


def test_cache_store_indexes_blocks_once_and_honors_requested_phase():
    cache = InstrumentedCache()
    cache.add_bead("phase-a-target", "target", "open", ["phase-a", "stage:dev"], {})
    cache.add_bead("phase-a-blocker", "blocker", "open", ["phase-a", "stage:fix"], {})
    cache.rows["phase-a-blocker"]["dependencies"] = [
        {"type": "blocks", "depends_on_id": "phase-a-target"},
    ]
    cache.add_bead("phase-b-other", "other", "open", ["phase-b", "stage:dev"], {})
    store = CacheStore(cache, "bo")

    listed = store.list("phase-a")
    assert [bead.id for bead in listed] == ["phase-a-target", "phase-a-blocker"]
    assert listed[0].blocks("phase-a-blocker")
    assert cache.list_phases == ["phase-a"]
    assert cache.get_calls == ["phase-a-target", "phase-a-blocker"]

    cache.get_calls.clear()
    cache.list_phases.clear()
    ready = store.ready("phase-b")
    assert [bead.id for bead in ready] == ["phase-b-other"]
    assert cache.ready_phases == ["phase-b"]
    assert cache.list_phases == ["phase-b", "phase-b"]
    assert cache.get_calls == ["phase-b-other"]


def test_refresh_with_unset_scope_id_returns_request_refusal(setup):
    _root, store = setup
    refusal = store.refresh([None])
    assert isinstance(refusal, Refusal)
    assert refusal.id == ErrorId.REQUEST_INVALID


def test_show_without_stack_id_returns_stack_refusal(setup):
    _root, store = setup
    refusal = store.show(None)
    assert isinstance(refusal, Refusal)
    assert refusal.id == ErrorId.STACK_NOT_RECORDED


def test_real_embedded_bd_wires_cache_store(real_db_setup):
    root, store = real_db_setup
    bead = store.show("tst-1")
    stack = store.show("tst-stack")
    assert bead.id == "tst-1" and bead.branch == "work"
    assert stack.id == "tst-stack" and stack_of(stack).layers[0].head == SHA
    assert json.loads(bd(root, "show", "tst-1", "--json"))[0]["id"] == "tst-1"


def test_stack_read_refreshes_external_ledger_change(real_db_setup):
    root, store = real_db_setup
    newer = "a" * 40
    layers = {"layers": [{"branch": "work", "head": newer, "pr": 8, "base": "main"}]}
    bd(root, "update", "tst-stack", "--metadata", json.dumps(layers))
    assert stack_of(store.show("tst-stack")).layers[0].head == newer


def test_three_hooks_assign_start_and_close_with_controlled_cache(setup):
    _, store = setup
    phases = PhaseFilesCli()
    assigned = load_hook("assign")(request("task.assign", "lead", to="dev"), store, phases)
    assert "pass-through" in assigned.to_json(None)
    assert store.show("tst-1").assignee == "dev"

    started = load_hook("start")(request("task.start", "dev"), store, phases)
    assert "pass-through" in started.to_json(None)
    assert store.show("tst-1").status == Status.IN_PROGRESS

    reply = load_hook("close")(
        request("task.close", "dev", op={"op": "close", "outcome": "completed", "reason": "done"},
                report="done"),
        store,
        phases,
    )
    assert "handled" in reply.to_json(None), reply.to_json(None)
    assert store.show("tst-1").status == Status.CLOSED


def test_real_bd_requires_the_explicit_test_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATM_TEST_BD", raising=False)
    with pytest.raises(RuntimeError, match="ATM_TEST_BD must name the pinned embedded bd test binary"):
        require_test_bd_binary()


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


def test_stale_snapshot_is_a_typed_race(real_db_setup):
    _, store = real_db_setup
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


def test_journaled_update_is_visible_before_drain(real_db_setup):
    _, store = real_db_setup
    snapshot = store.show("tst-1")
    assert store.update(BeadPatch.assign(snapshot, "dev"), "lead") is None
    assert store.cache.get("tst-1")["pending"] == 1
    assert store.show("tst-1").assignee == "dev"


def test_qa_target_and_ready_views(setup):
    _root, store = setup
    store.cache.add_bead("tst-qa", "qa", "open", ["phase-bo", "stage:qa"], {"checked_bead": "tst-1"})
    qa = store.show("tst-qa")
    assert store.target_layer(store.show(qa.checked_bead)).head == SHA
    assert stack_of(store.show("tst-stack")).layers[0].head == SHA
    assert {b.id for b in store.list("bo")} == {"tst-1", "tst-stack", "tst-qa"}
    assert "tst-1" in {b.id for b in store.ready("bo")}


def test_hook_update_journals_without_draining(setup, monkeypatch):
    _, store = setup
    snapshot = store.show("tst-1")

    class PendingCache:
        def write(self, *_args):
            return {"seq": 1}

        def drain(self, *_args):
            pytest.fail("hook must not drain")

        def entry(self, _seq):
            return {"state": "pending"}

        def close(self):
            pass

    monkeypatch.setattr(store, "cache", PendingCache())
    assert store.update(BeadPatch.start(snapshot), "dev") is None


def test_missing_cache_root_names_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CacheStore.for_phase("bo")
    assert isinstance(result, Refusal)
    assert getattr(result, "id", None) == ErrorId.CACHE_UNAVAILABLE
    assert "no .beads directory" in repr(result)
    assert str(tmp_path.resolve()) in repr(result)


def test_store_resolves_the_supplied_checked_bead_without_qa_fallback(setup):
    _, store = setup
    store.cache.add_bead("other", "work", "closed", ["phase-bo", "stage:dev"],
                         {"branch": "missing", "stack_bead": "tst-stack"})
    checked = store.show("tst-1")
    assert store.target_layer(checked).head == SHA
    result = store.target_layer(store.show("other"))
    assert isinstance(result, Refusal) and result.id == ErrorId.STACK_NOT_RECORDED



def test_qa_without_checked_bead_does_not_use_a_closed_blocker(setup):
    _, store = setup
    store.cache.rows["tst-1"]["status"] = "closed"
    store.cache.add_bead("tst-qa", "qa", "in_progress", ["phase-bo", "stage:qa"], {})
    store.cache.rows["tst-qa"]["assignee"] = "qa"
    store.cache.rows["tst-qa"]["dependencies"] = [{"type": "blocks", "depends_on_id": "tst-1"}]
    report = f'done\n```json\n{{"verdict":"PASS","sha":"{SHA}"}}\n```'
    req = request("task.close", "qa", op={"op": "close", "outcome": "completed"},
                  report=report, task_id="tst-qa")
    reply = load_hook("close")(req, store, PhaseFilesCli())
    assert "STACK_NOT_RECORDED" in reply.to_json(Hook.TASK_CLOSE)
    assert store.cache.seq == 0


def test_external_poured_finding_is_visible_with_its_dependency(real_db_setup):
    root, store = real_db_setup
    create_bead(root, "tst-finding", "finding", "phase-bo,stage:fix", {"sprint_bead": "tst-1", "blocking": True})
    bd(root, "dep", "add", "tst-1", "--blocked-by", "tst-finding")
    assert store.refresh(["tst-finding", "tst-1"]) is None
    finding = store.show("tst-finding")
    assert not isinstance(finding, Refusal), finding
    assert finding.blocks("tst-1")
