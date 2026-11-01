# pyright: strict
"""The runner gathers all transition state from deterministic command doubles."""
from __future__ import annotations

import json
import sys
import subprocess
from pathlib import Path
from typing import Any

import pytest

from atm_bd_types import Error, ErrorKind, PrRef, Profile, StackGateResult, Transition
from result import Err, Ok, Result

from helpers import HOOK, RecordingSubprocess, fake_stack_gate

ROOT = Path(__file__).parents[6]
sys.path.insert(0, str(ROOT / "plugins/atm-bd-orchestration/core/scripts"))
import phase_profile
from hook_runner import close_vars_from_mapping, collect_observed, run_transition


def _completed(argv: list[str], output: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, 0, json.dumps(output), "")


def test_collector_reads_bead_stack_task_pr_and_gate() -> None:
    sha = "a" * 40
    process = RecordingSubprocess([
        _completed(["bd", "show"], [{"id": "atm-phase-lt.dev-1", "status": "open", "metadata": {}}]),
        _completed(["bd", "show"], [{"id": "atm-phase-lt.stack", "status": "open",
                                      "metadata": {"trunk": "sprint/main", "layers": []}}]),
        subprocess.CompletedProcess(["git", "rev-parse"], 0, sha, ""),
        _completed(["atm", "task", "events"], {"events": [
            {"to_state": "complete"},
            {"to_state": "assigned", "actor": {"member": "fenix"}},
            {"to_state": "active"},
        ]}),
        _completed(["atm", "task", "list"], []),
    ])
    gate = fake_stack_gate(Ok(StackGateResult.Stacked()))

    def lookup(branch: str, repo: Path, *, expected_head: str, runner: Any = None) -> Any:
        assert branch == "feature/lite"
        assert expected_head == sha
        assert repo.name == "repo"
        return Ok(PrRef("42", "https://example.invalid/pr/42", "sprint/main", sha))

    values: dict[str, object] = {
        "task_id": "atm-phase-lt.dev-1", "checked_bead": "atm-phase-lt.dev-1",
        "stack_bead": "atm-phase-lt.stack", "branch": "feature/lite", "commit": sha,
        "pr_target": "sprint/main", "qa_bead": "atm-phase-lt.qa-1",
    }
    result = collect_observed(values, {}, Transition.DEV_CLOSE, Path("/tmp/repo"), HOOK,
                              runner=process, pr_finder=lookup, gate_factory=lambda _root: gate)
    assert isinstance(result, Ok)
    observed: Any = result.value
    assert observed.bead_id == "atm-phase-lt.dev-1"
    assert observed.stack_top == "sprint/main"
    assert observed.gate_stacked is True
    assert observed.bead_closed is False
    assert observed.qa_assigned is False
    assert observed.task_closed is False
    assert observed.lead == "fenix"
    assert gate.calls == [("sprint/main", "feature/lite", sha, "sprint/main", "origin")]
    assert [call[:2] for call in process.calls] == [
        ("bd", "show"), ("bd", "show"), ("git", "rev-parse"),
        ("atm", "task"), ("atm", "task"),
    ]


@pytest.mark.parametrize("values", [
    {"sanity_bead": 17},
    {"max_sanity_rounds": "five"},
    {"max_sanity_rounds": True},
    {"max_sanity_rounds": -1},
    {"max_sanity_rounds": 0x1_0000_0000},
])
def test_close_vars_reject_invalid_values_with_a_typed_error(values: dict[str, object]) -> None:
    result = close_vars_from_mapping(values)
    assert isinstance(result, Err)
    assert result.error.kind is ErrorKind.CONFIG_INVALID


def test_close_vars_builds_the_shared_type_from_supplied_values() -> None:
    result = close_vars_from_mapping({"sanity_bead": "atm-phase-lt.sanity", "max_sanity_rounds": 3})
    assert isinstance(result, Ok)
    assert result.value.sanity_bead == "atm-phase-lt.sanity"
    assert result.value.max_sanity_rounds == 3


def test_runner_stops_after_failed_stack_gate_before_bd_or_atm_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "a" * 40
    process = RecordingSubprocess([
        _completed(["bd", "show"], [{"id": "atm-phase-lt.dev-1", "status": "open", "metadata": {}}]),
        _completed(["bd", "show"], [{"id": "atm-phase-lt.stack", "status": "open",
                                      "metadata": {"trunk": "sprint/main", "layers": []}}]),
        subprocess.CompletedProcess(["git", "rev-parse"], 0, sha, ""),
    ])
    gate_failure = Err(Error(ErrorKind.COMMAND_FAILED, "gate failed", "repair stack ancestry"))
    gate = fake_stack_gate(gate_failure)

    def lookup(_branch: str, _repo: Path, *, expected_head: str, runner: Any = None) -> Any:
        assert expected_head == sha
        return Ok(PrRef("42", "https://example.invalid/pr/42", "sprint/main", sha))

    def gate_factory(_root: Path) -> Any:
        process.calls.append(("GATE",))
        return gate

    def allow_lite_profile(_phase: Path, _expected: Profile) -> Result[Profile]:
        return Ok(Profile.LITE)

    monkeypatch.setattr(phase_profile, "require_profile", allow_lite_profile)
    values: dict[str, object] = {
        "task_id": "atm-phase-lt.dev-1", "checked_bead": "atm-phase-lt.dev-1",
        "stack_bead": "atm-phase-lt.stack", "branch": "feature/lite", "commit": sha,
        "pr_target": "sprint/main", "qa_bead": "atm-phase-lt.qa-1",
    }
    outcome = run_transition(Path("phase.toml"), Transition.DEV_CLOSE, values, {}, Path("/tmp/repo"), HOOK,
                             runner=process, pr_finder=lookup, gate_factory=gate_factory)
    assert isinstance(outcome, Err)
    assert outcome.error.kind is ErrorKind.COMMAND_FAILED
    assert gate.calls == [("sprint/main", "feature/lite", sha, "sprint/main", "origin")]
    assert process.calls == [("bd", "show", "atm-phase-lt.dev-1", "--json"),
                             ("bd", "show", "atm-phase-lt.stack", "--json"),
                             ("git", "rev-parse", "--verify", "refs/remotes/origin/sprint/main"),
                             ("GATE",)]
    gate_index = process.calls.index(("GATE",))
    assert not any(call[0] in ("bd", "atm") for call in process.calls[gate_index + 1:])
