# pyright: strict
"""Stack gate boundary and deterministic test double."""
from __future__ import annotations

from typing import Protocol

from atm_bd_types import StackGateResult


class StackGate(Protocol):
    """Verify a provider PR base and pushed head against the stack top."""

    def check(self, pr_base_ref: str, head_branch: str, head_sha: str,
              stack_top_branch: str, remote: str = "origin") -> StackGateResult: ...


class FakeStackGate:
    """Return a controlled result and retain exact inputs for callers' tests."""

    def __init__(self, result: StackGateResult) -> None:
        self.result = result
        self.calls: list[tuple[str, str, str, str, str]] = []

    def check(self, pr_base_ref: str, head_branch: str, head_sha: str,
              stack_top_branch: str, remote: str = "origin") -> StackGateResult:
        self.calls.append((pr_base_ref, head_branch, head_sha, stack_top_branch, remote))
        return self.result
