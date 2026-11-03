"""atm-bd-types plug-in runtime surface (stub: stubs/atm_bd_types.pyi).

Every class is the Rust binding in `atm_bd_types._native`, except the runtime protocols and aliases
needed by Python callers. Their static signatures are owned by `src/python/stub.rs`; `test_stubs.py`
checks that this runtime surface matches the generated stub.
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
    Merged,
    Notify,
    Params,
    PatchKind,
    PhaseFacts,
    PhaseFile,
    PrBase,
    Profile,
    QaFail,
    QaPass,
    Refusal,
    RemoteBranch,
    Report,
    ReviewTarget,
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
    def refresh(self, bead_ids: builtins.list[str]) -> Refusal | None: ...
    def show(self, bead_id: str | None) -> Bead | Refusal: ...
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
    "Merged",
    "Notify",
    "Params",
    "PatchKind",
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
    "ReviewTarget",
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
