# pyright: strict
"""Shared deterministic fixtures for the pure lite hook planner."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

from atm_bd_types import CloseVars, Transition
from atm_bd_types import StackGateResult
from result import Ok, Result
from stack_gate_types import FakeStackGate

HOOK = Path(__file__).parents[1] / "atm-bd-task-hook.py"
SPEC = importlib.util.spec_from_file_location("lite_task_hook", HOOK)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
hook: Any = MODULE


class RecordingSubprocess:
    """A deterministic subprocess boundary that records argv and returns queued results."""

    def __init__(self, responses: list[subprocess.CompletedProcess[str]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(tuple(argv))
        if not self.responses:
            raise AssertionError(f"unexpected subprocess call: {argv}")
        return self.responses.pop(0)


def fake_stack_gate(result: Result[StackGateResult] | None = None) -> FakeStackGate:
    return FakeStackGate(result or Ok(StackGateResult.Stacked()))


def make_close_vars() -> CloseVars:
    return CloseVars()


def observed(**changes: object) -> Any:
    base: dict[str, object] = {"task_id": "atm-bo-5.group-dev", "bead_id": "atm-bo-5.group-dev", "lead": "fenix",
            "reason": "blocked by upstream", "findings_file": "findings.json", "pr_number": "123",
            "pr_base": "sprint/bo-4-stack-gate", "pr_head": "sprint/bo-5-lite-skill", "pr_sha": "a" * 40,
            "stack_top": "sprint/bo-4-stack-gate", "gate_stacked": True}
    for key, value in changes.items():
        base[key] = value
    return hook.Observed(**base)


def command_argv(result: Any) -> list[tuple[str, ...]]:
    return [command.argv for command in result.value]


def run_hook(transition: Transition, *, state: Any | None = None) -> Any:
    return hook.plan(transition, make_close_vars(), state or observed())
