# pyright: strict
"""The runner gathers all transition state from deterministic command doubles."""
from __future__ import annotations

import json
import sys
import subprocess
from pathlib import Path
from typing import Any

from atm_bd_types import PrRef, StackGateResult, Transition
from result import Ok

from helpers import HOOK, RecordingSubprocess, fake_stack_gate

ROOT = Path(__file__).parents[6]
sys.path.insert(0, str(ROOT / "plugins/atm-bd-orchestration/core/scripts"))
from hook_runner import collect_observed


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
