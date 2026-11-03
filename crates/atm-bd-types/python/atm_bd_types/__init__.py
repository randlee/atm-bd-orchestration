"""atm-bd-types plug-in surface: what a profile plug-in imports (stub: stubs/atm_bd_types.pyi).

Every class is the Rust binding in `atm_bd_types._native`; the protocols and aliases are defined here.
"""

import builtins
import typing

from atm_bd_types._native import (
    Ancestry,
    Assign,
    AssignTransition,
    AssignVars,
    Bead,
    BeadPatch,
    CheckState,
    CloseTransition,
    CollectError,
    ErrorId,
    FactKind,
    Finding,
    Hook,
    HookAction,
    HookReply,
    HookRequest,
    Layer,
    Notify,
    Params,
    PhaseFacts,
    PhaseFile,
    PrBase,
    Profile,
    QaFail,
    QaPass,
    Refusal,
    RemoteBranch,
    Report,
    Stack,
    StackFact,
    Stage,
    StartTransition,
    Status,
    TaskEvents,
    TaskFact,
    TaskState,
    Template,
    TopChecks,
)
from atm_bd_types._stores import CacheStore, PhaseFilesCli

Sha: typing.TypeAlias = str
Action: typing.TypeAlias = Assign | Report | Notify


class BeadStore(typing.Protocol):
    def show(self, bead_id: str) -> Bead | Refusal: ...
    def target_layer(self, qa_bead: Bead) -> Layer | Refusal: ...
    def update(self, patch: BeadPatch, actor: str) -> Refusal | None: ...


class PhaseFiles(typing.Protocol):
    def load(self, path: str, profile: str) -> PhaseFile | Refusal: ...


class Cron(typing.Protocol):
    def decide(self, facts: PhaseFacts, params: Params) -> builtins.list[Action]: ...


__all__ = [
    "Action",
    "Ancestry",
    "Assign",
    "AssignTransition",
    "AssignVars",
    "Bead",
    "BeadPatch",
    "BeadStore",
    "CacheStore",
    "CheckState",
    "CloseTransition",
    "CollectError",
    "Cron",
    "ErrorId",
    "FactKind",
    "Finding",
    "Hook",
    "HookAction",
    "HookReply",
    "HookRequest",
    "Layer",
    "Notify",
    "Params",
    "PhaseFacts",
    "PhaseFile",
    "PhaseFiles",
    "PhaseFilesCli",
    "PrBase",
    "Profile",
    "QaFail",
    "QaPass",
    "Refusal",
    "RemoteBranch",
    "Report",
    "Sha",
    "Stack",
    "StackFact",
    "Stage",
    "StartTransition",
    "Status",
    "TaskEvents",
    "TaskFact",
    "TaskState",
    "Template",
    "TopChecks",
]
