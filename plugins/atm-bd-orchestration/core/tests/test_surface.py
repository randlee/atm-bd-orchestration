"""The framework runtime exports match its Rust-generated public stub."""

import importlib.util
import json
from pathlib import Path

import atm_bd_core
import pytest
from atm_bd_core import ActionOutcome, Decision, OutcomeKind, ViewRow, encode_evidence, stack_of
from atm_bd_types import Assign, AssignVars, CacheStore, ErrorId, HookRequest, Merged, Notify, PhaseFilesCli, QaFail, QaPass, Refusal, Report, Stage, Status
from atm_bd_types._native import _stub


def test_framework_surface_matches_generated_stub() -> None:
    path = Path(__file__).resolve().parents[4] / "crates/atm-bd-types/gen_stubs.py"
    spec = importlib.util.spec_from_file_location("atm_bd_stub_generator", path)
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    assert generator.surface_mismatches(_stub("atm_bd_core"), atm_bd_core) == []


def test_old_framework_shim_is_not_importable() -> None:
    assert importlib.util.find_spec("atm_bd_types._core") is None


def test_encode_evidence_uses_canonical_json() -> None:
    sha = "0123456789abcdef0123456789abcdef01234567"
    assert encode_evidence(Merged(sha=sha)) == f'{{"kind":"merged","sha":"{sha}"}}'



def test_encode_qa_evidence_uses_canonical_json() -> None:
    sha = "0123456789abcdef0123456789abcdef01234567"
    def verdict(report: dict[str, object]) -> HookRequest:
        request = {
            "schema_version": "1.0.0", "hook": "task.close", "team": "t", "phase": "bo",
            "caller": {"identity": "qa", "team": "t", "host": None}, "custom": {},
            "request": {"home_dir": "/h", "current_dir": "/r", "caller_identity": "qa", "caller_team": "t",
                        "to": None, "message_source": {"Inline": "```json\n" + json.dumps(report) + "\n```"},
                        "requires_ack": False, "task_id": "bo-3",
                        "task_op": {"op": "close", "outcome": "completed"}, "dry_run": False},
        }
        parsed = HookRequest.parse(json.dumps(request))
        assert isinstance(parsed, HookRequest)
        return parsed

    passed = verdict({"verdict": "PASS", "sha": sha}).qa_pass()
    assert isinstance(passed, QaPass)
    assert encode_evidence(passed) == f'{{"kind":"qa_pass","sha":"{sha}"}}'
    failed = verdict({"verdict": "FINDINGS", "sha": sha,
                      "findings": [{"id": "f1", "blocking": True}]}).qa_findings()
    assert isinstance(failed, QaFail)
    assert encode_evidence(failed) == json.dumps(
        {"kind": "qa_fail", "sha": sha, "findings": [{"id": "f1", "blocking": True}]},
        sort_keys=True, separators=(",", ":"))


def test_actions_round_trip_through_the_rust_action() -> None:
    actions = [Assign("k", "qa", "q", "t.j2", AssignVars("q", "bo", "lite")), Report("r", "config", None, "x"),
               Notify("lead", ["r"])]
    decision = Decision(actions, [ViewRow("config", "r", None, "x", None)])
    assert decision.actions == actions
    failed = ActionOutcome(actions[2], OutcomeKind.FAILED, Refusal(ErrorId.BEAD_RACED, bead="q"))
    assert failed.failure is not None and failed.failure.id == ErrorId.BEAD_RACED and failed.action == actions[2]


def test_framework_stack_of_reads_ledger() -> None:
    from atm_bd_types._native import _bead, _layer, _stack

    layer = _layer("branch", "0123456789abcdef0123456789abcdef01234567", 2, "base")
    bead = _bead("bo.stack", Status.OPEN, Stage.STACK, stack=_stack([layer]))
    assert stack_of(bead).layers[0].branch == "branch"
    assert stack_of(_bead("bo-1", Status.OPEN, Stage.DEV)) is None


def test_framework_package_imports() -> None:
    assert atm_bd_core.__name__ == "atm_bd_core"


def test_lazy_store_delegates_to_framework(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    import types

    class Store:
        @staticmethod
        def for_phase(phase: str):
            assert phase == "bo"
            return Store()

        def show(self, bead_id: str | None):
            return bead_id

    class Phases:
        def load(self, path: str, profile: str):
            return (path, profile)

    fake = types.ModuleType("atm_bd_core.store")
    fake.CacheStore = Store  # type: ignore[attr-defined]
    fake.PhaseFilesCli = Phases  # type: ignore[attr-defined]
    import atm_bd_core
    monkeypatch.setitem(sys.modules, "atm_bd_core.store", fake)
    monkeypatch.setattr(atm_bd_core, "store", fake, raising=False)
    assert CacheStore.for_phase("bo").show("bo-1") == "bo-1"
    assert PhaseFilesCli().load("phase.toml", "lite") == ("phase.toml", "lite")


