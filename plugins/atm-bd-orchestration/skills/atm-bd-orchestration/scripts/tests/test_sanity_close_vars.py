from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOADER = importlib.machinery.SourceFileLoader("sanity_close_vars", str(ROOT / "scripts/sanity-close-vars"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
CLOSE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(CLOSE)
READ_TASK_EVENTS = CLOSE.task_events
EVENT_SETTINGS = CLOSE.event_settings


@pytest.fixture(autouse=True)
def task_events(monkeypatch):
    monkeypatch.setattr(CLOSE, "task_events", lambda task, **kwargs: [{"event": "assigned"}])
    monkeypatch.setattr(CLOSE, "event_settings", lambda manifest: ("test-team", "test-bot@tool", 30))


@pytest.fixture
def inputs():
    context = json.loads((ROOT / "examples/task-close-vars-sanity.json").read_text())
    context.update(budget="full")
    manifest = {"run_id": "run", "sha": context["commit"], "sanity_bead": context["sanity_bead"],
                "dev_bead": context["checked_bead"], "branch": context["branch"],
                "worktree_path": context["worktree_path"], "deliverables_total": 2,
                "close_context": context, "checked_bead_data": {"title": "Checked title", "labels": ["stage:fix"]},
                "assignments": [{"number": 1}, {"number": 2}]}
    selected = {"run_id": "run", "reviewer": "sanity-selected", "commit": context["commit"],
                "task_id": context["sanity_bead"], "checked_bead": context["checked_bead"],
                "sprint": context["sprint"], "completed_at": "2026-10-20T00:00:00Z",
                "verdict": "PASS", "findings_count": 0, "findings": [], "findings_md": "D1: done\nD2: done"}
    return manifest, selected


def test_pass_builds_full_close_input_without_waiting_for_stack(inputs):
    manifest, selected = inputs
    result = CLOSE.build(manifest, selected)
    assert result["stacked"] is None
    assert result["verdict"] == "PASS" and result["deliverables_complete"] == 2
    assert result["undone"] == []
    assert result["commit"] == manifest["sha"]
    assert result["carry_forward"] == manifest["dev_bead"]
    assert result["run_id"] == "run" and result["reviewer"] == "sanity-selected"
    assert "stacked" in manifest["close_context"]


def test_reopened_assignment_counts_from_task_events_not_old_context(inputs):
    manifest, selected = inputs
    manifest["close_context"]["round"] = 1
    events = [{"event": "assigned"}, {"event": "completed"}, {"event": "reopened"}]
    assert CLOSE.build(manifest, selected, events=events)["round"] == 2


def test_event_reader_requests_complete_history(monkeypatch):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return type("Result", (), {"stdout": '{"events": [{"event": "assigned"}]}'})()
    monkeypatch.setattr(CLOSE.shutil, "which", lambda _: "/usr/bin/atm")
    assert READ_TASK_EVENTS("task", team="phase-team", identity="bot@tool", timeout=47, runner=run) == [{"event": "assigned"}]
    assert calls == [["atm", "task", "events", "task", "--all", "--json"]]


def test_event_reader_overrides_hostile_caller_identity_and_team(monkeypatch):
    seen = {}
    monkeypatch.setenv("ATM_TEAM", "foreign-team")
    monkeypatch.setenv("ATM_IDENTITY", "foreign-identity")
    monkeypatch.setattr(CLOSE.shutil, "which", lambda _: "/usr/bin/atm")
    def run(command, **kwargs):
        seen.update(kwargs)
        return type("Result", (), {"stdout": '{"events": []}'})()

    assert READ_TASK_EVENTS("task", team="phase-team", identity="configured@tool", timeout=81, runner=run) == []
    assert seen["env"]["ATM_TEAM"] == "phase-team"
    assert seen["env"]["ATM_IDENTITY"] == "configured@tool"
    assert seen["timeout"] == 81


def test_missing_atm_has_typed_cause_and_fix(monkeypatch):
    monkeypatch.setattr(CLOSE.shutil, "which", lambda _: None)
    with pytest.raises(CLOSE.SanityCloseVarsError) as caught:
        READ_TASK_EVENTS("task", team="team", identity="bot", timeout=30)
    assert caught.value.code == "SANITY_CLOSE_VARS.ATM_MISSING"
    assert "install atm" in caught.value.fix


def test_task_not_found_has_typed_cause_and_fix(monkeypatch):
    monkeypatch.setattr(CLOSE.shutil, "which", lambda _: "/usr/bin/atm")
    def run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr="task not found: sanity")
    with pytest.raises(CLOSE.SanityCloseVarsError) as caught:
        READ_TASK_EVENTS("sanity", team="team", identity="bot", timeout=30, runner=run)
    assert caught.value.code == "SANITY_CLOSE_VARS.TASK_NOT_FOUND"
    assert "verify that sanity task" in caught.value.fix


def test_timeout_has_typed_cause_and_fix(monkeypatch):
    monkeypatch.setattr(CLOSE.shutil, "which", lambda _: "/usr/bin/atm")
    def run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    with pytest.raises(CLOSE.SanityCloseVarsError) as caught:
        READ_TASK_EVENTS("sanity", team="team", identity="bot", timeout=73, runner=run)
    assert caught.value.code == "SANITY_CLOSE_VARS.TIMEOUT"
    assert "ATM service" in caught.value.fix


def test_unset_team_has_typed_cause_and_configuration_fix(tmp_path):
    (tmp_path / ".atm-bd").mkdir()
    (tmp_path / ".atm-bd/phase-x.toml").write_text('lead = "phase-lead"\n')
    manifest = {"close_context": {"primary_checkout": str(tmp_path), "phase": "x"}}
    with pytest.raises(CLOSE.SanityCloseVarsError) as caught:
        EVENT_SETTINGS(manifest)
    assert caught.value.code == "SANITY_CLOSE_VARS.TEAM_UNSET"
    assert "set the phase team" in caught.value.fix


def test_event_settings_use_repository_phase_team_identity_and_timeout(tmp_path, monkeypatch):
    (tmp_path / ".atm-bd").mkdir()
    (tmp_path / ".atm-bd/phase-x.toml").write_text('lead = "phase-lead"\nteam = "phase-team"\n')
    config = tmp_path / ".claude/project/atm-bd-orchestration.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("tool_identity: configured-bot@tool\ngate_timeout_s: 83\n")
    monkeypatch.delenv("ATM_BD_GATE_TIMEOUT_S", raising=False)
    assert EVENT_SETTINGS({"close_context": {"primary_checkout": str(tmp_path), "phase": "x"}}) == (
        "phase-team", "configured-bot@tool", 83
    )


def test_fail_retains_verbatim_deliverable_reason_and_stack_result(inputs):
    manifest, selected = inputs
    selected.update(verdict="FAIL", findings_count=1,
                    findings=[{"deliverable": 2, "issue": "missing required implementation"}])
    stack = {"result": "lock_timeout", "holder": "other"}
    result = CLOSE.build(manifest, selected, stack)
    assert result["stacked"] is stack
    assert result["undone"] == [{"number": 2, "reason": "missing required implementation"}]
    assert result["deliverables_complete"] == 1


def test_role_fix_finding_carries_forward(inputs):
    manifest, selected = inputs
    manifest["checked_bead_data"] = {"title": "finding", "labels": ["stage:finding"], "metadata": {"role": "fix"}}
    assert CLOSE.build(manifest, selected)["carry_forward"] == manifest["dev_bead"]


@pytest.mark.parametrize("field", ["run_id", "commit", "task_id", "checked_bead"])
def test_pinned_identity_mismatch_is_rejected(inputs, field):
    manifest, selected = inputs
    selected[field] = "wrong"
    with pytest.raises(ValueError, match=field):
        CLOSE.build(manifest, selected)


def test_lint_only_failure_marks_numbered_deliverables_undone(inputs):
    manifest, selected = inputs
    selected.update(verdict="FAIL", findings_count=1, lint_md="lint exited 1")
    result = CLOSE.build(manifest, selected)
    assert result["undone"] == [{"number": 1, "reason": "lint exited 1"}, {"number": 2, "reason": "lint exited 1"}]


def test_minimal_documented_dev_dispatch_needs_no_hand_built_fields(inputs):
    manifest, selected = inputs
    # The dev close hook adds the QA bead's reviewer list to close_context (atm-task-close.py sanity_dispatch, #821).
    manifest["close_context"] = {**json.loads((ROOT / "examples/task-close-vars-dev.json").read_text()), "reviewers_round1": ["req-qa"]}
    result = CLOSE.build(manifest, selected)
    assert result["evidence"] == "" and result["outcome"] == "fixed"
    assert result["round"] == 1 and result["findings_blocking"] == 0


@pytest.mark.parametrize(("outcome", "omit_stack"), [("fixed", False), ("not_reproducible", True)])
def test_optional_stack_input_does_not_block_close_vars(inputs, tmp_path, outcome, omit_stack):
    manifest, selected = inputs
    manifest["close_context"]["pr_number"] = ""
    manifest["close_context"]["outcome"] = outcome
    if omit_stack:
        manifest["close_context"].pop("stack_bead", None)
    values = CLOSE.build(manifest, selected)
    stack_file = tmp_path / "stack-input.json"
    stack_file.write_text("stale")

    assert not CLOSE.write_stack_input(stack_file, values, manifest)
    assert not stack_file.exists()


def test_stack_input_carries_assignment_budget_and_worktree_and_only_passes(inputs, tmp_path):
    manifest, selected = inputs
    manifest["close_context"].update(budget="lean")
    values = CLOSE.build(manifest, selected)
    stack_file = tmp_path / "stack-input.json"

    assert CLOSE.write_stack_input(stack_file, values, manifest)
    payload = json.loads(stack_file.read_text())
    assert payload["budget"] == "lean" and "timeout_s" not in payload
    assert payload["worktree_path"] == manifest["worktree_path"]

    selected["verdict"] = "FAIL"
    values = CLOSE.build(manifest, selected)
    assert not CLOSE.write_stack_input(stack_file, values, manifest)
    assert not stack_file.exists()


def test_stack_input_requires_assignment_budget(inputs, tmp_path):
    manifest, selected = inputs
    manifest["close_context"].update(budget="full")
    values = CLOSE.build(manifest, selected)
    stack_file = tmp_path / "stack-input.json"

    assert CLOSE.write_stack_input(stack_file, values, manifest)
    manifest["close_context"].pop("budget")
    with pytest.raises(ValueError, match="budget"):
        CLOSE.write_stack_input(stack_file, values, manifest)


@pytest.mark.parametrize("reviewers", ["", [], "req-qa", ["req-qa", ""]])
def test_an_untyped_reviewer_list_is_refused_at_emission_not_at_the_qa_template(inputs, reviewers):
    """#821: a legacy close_context carried reviewers_round1 as ""; qa-template.xml.j2 iterates a list."""
    manifest, selected = inputs
    manifest["close_context"]["reviewers_round1"] = reviewers
    with pytest.raises(ValueError, match="reviewers_round1 must be a non-empty list of reviewer names"):
        CLOSE.build(manifest, selected)


def test_a_close_context_without_reviewers_is_refused_not_defaulted(inputs):
    manifest, selected = inputs
    del manifest["close_context"]["reviewers_round1"]
    with pytest.raises(ValueError, match="lacks reviewers_round1"):
        CLOSE.build(manifest, selected)
