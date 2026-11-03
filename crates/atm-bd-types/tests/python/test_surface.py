"""The bindings delegate to the Rust: transitions, requests, verdicts, guarded writes, records and the wheel tag."""

from __future__ import annotations

import importlib.metadata
import json

import pytest
from atm_bd_types import (
    Assign,
    AssignTransition,
    AssignVars,
    BeadPatch,
    CacheStore,
    CloseTransition,
    ErrorId,
    FactKind,
    Hook,
    HookAction,
    HookReply,
    HookRequest,
    Merged,
    Notify,
    Params,
    PatchKind,
    PhaseFacts,
    PhaseFilesCli,
    Profile,
    QaFail,
    QaPass,
    Refusal,
    RemoteBranch,
    Report,
    Stage,
    StartTransition,
    Status,
    Template,
)
from atm_bd_types._core import ActionOutcome, Decision, OutcomeKind, ViewRow, encode_evidence
from atm_bd_types._native import _bead, _layer, _phase_file
from conftest import SHA, pass_report, request_json

S = Status
TEMPLATES = [(f"/r/t/{n}.md.j2", "/r/t", b"ok") for n in ("refuse", "dev-close", "qa-pass", "qa-findings", "land-close")]


def parse(hook: str, report: str = "", op: dict[str, str] | None = None, to: str | None = None) -> HookRequest:
    req = HookRequest.parse(request_json(hook, report, op, to))
    assert isinstance(req, HookRequest), req
    return req


@pytest.mark.parametrize(("status", "assignee", "expected"), [
    (S.OPEN, "dev", AssignTransition.ASSIGN_SAME), (S.IN_PROGRESS, None, AssignTransition.ASSIGN),
    (S.CLOSED, "dev", AssignTransition.ASSIGN_CLOSED), (S.DEFERRED, None, AssignTransition.ASSIGN_NOT_READY),
])
def test_assign_select(status: Status, assignee: str | None, expected: AssignTransition) -> None:
    assert AssignTransition.select(status, assignee, "dev") == expected


@pytest.mark.parametrize(("status", "expected"), [
    (S.OPEN, StartTransition.START), (S.IN_PROGRESS, StartTransition.START_AGAIN),
    (S.CLOSED, StartTransition.START_CLOSED), (S.BLOCKED, StartTransition.START_NOT_READY),
])
def test_start_select(status: Status, expected: StartTransition) -> None:
    assert StartTransition.select(status) == expected


def test_close_select_by_outcome_stage_and_verdict() -> None:
    qa, dev = _bead("q", S.IN_PROGRESS, Stage.QA), _bead("d", S.IN_PROGRESS, Stage.DEV)
    completed = {"op": "close", "outcome": "completed"}
    assert CloseTransition.select(parse("task.close", "", {"op": "close", "outcome": "refused"}), qa) \
        == CloseTransition.GIVE_BACK
    assert CloseTransition.select(parse("task.close", "done", completed), dev) == CloseTransition.WORK_CLOSE
    assert CloseTransition.select(parse("task.close", pass_report(), completed), qa) == CloseTransition.QA_PASS
    no_verdict = CloseTransition.select(parse("task.close", "no block", completed), qa)
    assert isinstance(no_verdict, Refusal) and no_verdict.id == ErrorId.QA_VERDICT
    assert "cause=no fenced verdict block" in repr(no_verdict)


def test_request_fields_and_bad_stdin() -> None:
    req = parse("task.assign", "hi", to="dev")
    assert (req.phase, req.phase_config_path, req.caller, req.task_id, req.assignee) == (
        "bo", ".atm-bd/phase-bo.toml", "qa", "bo-3", "dev")
    assert req.is_phase_task() and req.close_report == "hi" and req.close_reason == "hi"
    bad = HookRequest.parse("{")
    assert isinstance(bad, Refusal) and bad.id == ErrorId.REQUEST_INVALID
    assert "cause=" in repr(bad)


def test_verdicts() -> None:
    report = f'```json\n{{"verdict": "FINDINGS", "sha": "{SHA}", "findings": [{{"id": "f1", "blocking": true}}]}}\n```'
    req = parse("task.close", report, {"op": "close", "outcome": "completed"})
    fail = req.qa_findings()
    assert isinstance(fail, QaFail) and fail.sha == SHA
    assert [(f.id, f.blocking) for f in fail.findings] == [("f1", True)]
    closed = BeadPatch.close(_bead("b", S.OPEN, Stage.QA), fail)
    assert closed.evidence == fail
    assert encode_evidence(fail) == json.dumps({"kind": "qa_fail", "sha": SHA,
                                              "findings": [{"id": "f1", "blocking": True}]},
                                             sort_keys=True, separators=(",", ":"))
    wrong = req.qa_pass()
    assert isinstance(wrong, Refusal) and wrong.id == ErrorId.QA_VERDICT


def test_merged_sha_keeps_string_python_surface_and_validates_constructor() -> None:
    merged = Merged(sha=SHA)
    assert merged.sha == SHA
    with pytest.raises(ValueError, match="not a 40-hex commit id"):
        Merged(sha="bad")


def test_bead_patch_guards_the_snapshot() -> None:
    bead = _bead("b", S.OPEN, Stage.DEV, "dev")
    assert "Assign { guard: Guard { bead_id: BeadId(\"b\"), status: Open, assignee: Some(\"dev\") }, agent: \"qa\" }" \
        == repr(BeadPatch.assign(bead, "qa"))
    assert BeadPatch.start(bead) == BeadPatch.start(bead) != BeadPatch.reopen(bead)
    verdict = parse("task.close", pass_report(), {"op": "close", "outcome": "completed"}).qa_pass()
    assert isinstance(verdict, QaPass)
    assert "QaPass" in repr(BeadPatch.close(bead, verdict))
    with pytest.raises(TypeError):
        BeadPatch.close(bead, "not evidence")  # type: ignore[arg-type]



@pytest.mark.parametrize(("status", "text"), [
    (Status.OPEN, "open"), (Status.IN_PROGRESS, "in_progress"), (Status.BLOCKED, "blocked"),
    (Status.DEFERRED, "deferred"), (Status.CLOSED, "closed"),
])
def test_status_roundtrip(status: Status, text: str) -> None:
    assert status.as_str() == text and Status.parse(text) == status
    assert Status.parse("unknown") is None


@pytest.mark.parametrize(("stage", "text"), [
    (Stage.DEV, "dev"), (Stage.FIX, "fix"), (Stage.QA, "qa"), (Stage.LAND, "land"),
    (Stage.STACK, "stack"), (Stage.OTHER, "other"),
])
def test_stage_roundtrip(stage: Stage, text: str) -> None:
    assert stage.as_str() == text and Stage.parse(text) == stage
    assert Stage.parse("unknown") == Stage.OTHER


def test_patch_exposes_typed_snapshot_operation_and_evidence() -> None:
    bead = _bead("b", S.IN_PROGRESS, Stage.DEV, "dev")
    assigned = BeadPatch.assign(bead, "qa")
    assert (assigned.kind, assigned.bead_id, assigned.expected_status, assigned.expected_assignee, assigned.agent) == (
        PatchKind.ASSIGN, "b", S.IN_PROGRESS, "dev", "qa")
    assert assigned.evidence is None
    assert BeadPatch.start(bead).kind == PatchKind.START
    assert BeadPatch.reopen(bead).kind == PatchKind.REOPEN
    verdict = parse("task.close", pass_report(), {"op": "close", "outcome": "completed"}).qa_pass()
    assert isinstance(verdict, QaPass)
    closed = BeadPatch.close(bead, verdict)
    assert closed.kind == PatchKind.CLOSE and closed.evidence == verdict and closed.agent is None
    assert encode_evidence(verdict) == f'{{"kind":"qa_pass","sha":"{SHA}"}}'

def test_bead_unset_scope_is_none_and_ids_are_nonempty() -> None:
    bead = _bead("b", S.OPEN, Stage.DEV)
    assert (bead.branch, bead.stack_bead, bead.sprint, bead.phase, bead.checked_bead) == (
        None, None, None, None, None)
    assert bead.layer_for(None) is None
    layer = _layer("", SHA, 7, None)
    assert layer.branch is None and layer.base is None
    with pytest.raises(TypeError, match="empty bead id"):
        _bead("", S.OPEN, Stage.DEV)


def test_refused_message_uses_the_parsed_hooks_fix_table() -> None:
    parse("task.assign")
    assert HookReply.refused(Refusal(ErrorId.ASSIGN_NOT_LEAD, lead="fenix")).to_json() == (
        '{"result":"refused","message":"ASSIGN_NOT_LEAD: Only the lead (fenix) assigns. Ask the lead."}')


def test_give_back_reason_and_unknown_template() -> None:
    parse("task.close", "", {"op": "close", "outcome": "refused", "reason": "blocked"})
    phase = _phase_file("lite", "lead", TEMPLATES, [("root", "atm-phase-bo")])
    assert phase.key("root") == "atm-phase-bo" and phase.key("nope") is None
    reply = HookReply.handled([HookAction.close(phase.template(Template.REFUSE), "blocked")]).to_json()
    assert '"var_file_values":{"reason":"blocked"}' in reply and '"outcome":"refused"' in reply
    unknown = HookReply.handled([HookAction.close("/elsewhere.j2", "blocked")]).to_json()
    assert unknown == (
        '{"result":"refused","message":"REQUEST_INVALID: Not yours to fix: field=template. The lead has it."}')


def test_stores_refuse_without_framework(monkeypatch: pytest.MonkeyPatch) -> None:
    from atm_bd_types import _stores

    def missing(_name: str):
        raise ModuleNotFoundError("no framework", name="atm_bd_core")

    monkeypatch.setattr(_stores, "import_module", missing)
    store = CacheStore.for_phase("bo")
    assert isinstance(store, Refusal) and store.id == ErrorId.CACHE_UNAVAILABLE
    assert "atm_bd_core package is missing" in repr(store) and "`uv add atm-bd-core`" in repr(store)
    phase = PhaseFilesCli().load(".atm-bd/phase-bo.toml", "lite")
    assert isinstance(phase, Refusal) and phase.id == ErrorId.PHASE_UNREADABLE
    assert "atm_bd_core package is missing" in repr(phase) and "`uv add atm-bd-core`" in repr(phase)


def test_params_delegate() -> None:
    params = Params([("qa_agent", "qa"), ("max", 3)])
    assert (params.text("qa_agent"), params.int("max"), params.int("qa_agent"), params.text("none")) == (
        "qa", 3, None, None)
    with pytest.raises(TypeError):
        Params([("bad", 1.5)])  # type: ignore[list-item]


def test_records_construct_positionally_and_by_name() -> None:
    vars_ = AssignVars("q", "bo", "lite")
    assert Assign("k", "qa", "q", "t.j2", vars_) == Assign(key="k", to="qa", bead_id="q", template="t.j2", vars=vars_)
    assert Report("k", "config", None, "text").bead_id is None and Notify("lead", ["k"]).keys == ["k"]
    facts = PhaseFacts("bo", 0, _phase_file("lite", "lead", TEMPLATES, []))
    assert facts.ready is None and facts.errors == [] and facts.phase_file.profile == "lite"
    with pytest.raises(TypeError, match='missing field "now"'):
        PhaseFacts("bo")  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="unexpected field"):
        AssignVars("q", "bo", "lite", extra=1)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="40-hex"):
        RemoteBranch("main", "not-a-sha")
    profile = Profile("lite", ["dev", "qa"], {Hook.TASK_CLOSE: "s.py"}, {Template.REFUSE: "r.j2"}, "policy.toml")
    assert profile.cron is None and profile.hooks == {Hook.TASK_CLOSE: "s.py"}
    assert FactKind.TOP_CHECKS.name == "TOP_CHECKS"


def test_actions_round_trip_through_the_rust_action() -> None:
    actions = [Assign("k", "qa", "q", "t.j2", AssignVars("q", "bo", "lite")), Report("r", "config", None, "x"),
               Notify("lead", ["r"])]
    decision = Decision(actions, [ViewRow("config", "r", None, "x", None)])
    assert decision.actions == actions
    failed = ActionOutcome(actions[2], OutcomeKind.FAILED, Refusal(ErrorId.BEAD_RACED, bead="q"))
    assert failed.failure is not None and failed.failure.id == ErrorId.BEAD_RACED and failed.action == actions[2]


def test_wheel_is_abi3() -> None:
    wheel = importlib.metadata.distribution("atm-bd-types").read_text("WHEEL") or ""
    assert "-abi3-" in wheel, wheel


def test_framework_stack_of_reads_ledger() -> None:
    from atm_bd_types._core import stack_of
    from atm_bd_types._native import _bead, _layer, _stack

    layer = _layer("branch", "0123456789abcdef0123456789abcdef01234567", 2, "base")
    bead = _bead("bo.stack", Status.OPEN, Stage.STACK, stack=_stack([layer]))
    assert stack_of(bead).layers[0].branch == "branch"
    assert stack_of(_bead("bo-1", Status.OPEN, Stage.DEV)) is None
