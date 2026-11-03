"""atm-bd framework surface (stub: stubs/atm_bd_core.pyi), published by the `atm_bd_core` package.

Every class is the Rust binding in `atm_bd_types._native`; the two ports are protocols defined here.
"""

import builtins
import typing

from atm_bd_types import Bead, BeadStore, Refusal
from atm_bd_types._native import (
    ActionKind,
    ActionOutcome,
    CommandResult,
    Decision,
    OutcomeKind,
    PhaseView,
    Policy,
    Ports,
    TickResult,
    ViewAction,
    ViewRow,
    ViewSprint,
    ViewStep,
    ViewTask,
    patch_json,
    stack_of,
)


class CommandRunner(typing.Protocol):
    def run(self, argv: builtins.list[str], stdin: str | None) -> CommandResult: ...


class BeadsCache(BeadStore, typing.Protocol):
    def list(self, phase: str) -> builtins.list[Bead] | Refusal: ...
    def ready(self, phase: str) -> builtins.list[Bead] | Refusal: ...


__all__ = [
    "ActionKind",
    "ActionOutcome",
    "BeadsCache",
    "CommandResult",
    "CommandRunner",
    "Decision",
    "OutcomeKind",
    "PhaseView",
    "Policy",
    "Ports",
    "TickResult",
    "ViewAction",
    "ViewRow",
    "ViewSprint",
    "ViewStep",
    "ViewTask",
    "patch_json",
    "stack_of",
]
