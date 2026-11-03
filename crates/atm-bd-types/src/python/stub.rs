//! Assembles the two `.pyi` surfaces in contract order from the stub text each binding generates or carries.
//!
//! The protocols and aliases below are defined by the wheel's Python package (`atm_bd_types/__init__.py`,
//! `atm_bd_types/_core.py`); their text lives here so one place renders each whole stub.
use super::enums::*;
use super::hook::*;
use super::records::*;

const PLUGIN_HEADER: &str = r#"# atm-bd-types 0.3.0 plug-in surface: what a profile plug-in imports. The names the lite hooks use, read-only facts,
# Params, the Actions the cron decide returns (Cron), and the Profile manifest. Framework names: atm_bd_core.pyi.
import builtins
import enum
import typing

Sha: typing.TypeAlias = str
r"""40-hex commit id (Rust `Sha`)."""
"#;

const BEAD_STORE: &str = r#"class BeadStore(typing.Protocol):
    def show(self, bead_id: str) -> Bead | Refusal: ...
    def target_layer(self, qa_bead: Bead) -> Layer | Refusal:
        r"""The ledger layer of the QA bead's closed dev/fix blocker, or of its checked_bead."""
    def update(self, patch: BeadPatch, actor: str) -> Refusal | None: ...
"#;

const PHASE_FILES: &str = "class PhaseFiles(typing.Protocol):
    def load(self, path: str, profile: str) -> PhaseFile | Refusal: ...
";

const RECORD_DECORATOR: &str = r#"# ---- Cron: PhaseFacts -> decide -> Action. Times: unix seconds.

_T = typing.TypeVar("_T")

@typing.dataclass_transform(frozen_default=True)
def _record(cls: type[_T]) -> type[_T]:
    r"""Stub-only: a frozen Rust record whose constructor takes every field in order."""
"#;

const ACTION: &str = "Action: typing.TypeAlias = Assign | Report | Notify\n";

const CRON: &str = r#"class Cron(typing.Protocol):
    r"""The profile's cron script (a module): pure, no I/O, imports only atm_bd_types. Called once per tick with every fact."""
    def decide(self, facts: PhaseFacts, params: Params) -> list[Action]: ...
"#;

const FRAMEWORK_HEADER: &str = r#"# atm-bd-types 0.3.0 framework surface: the same for every profile. Policy loading, decision record, view,
# executor outcomes, ports. The framework executes the Actions a plug-in decides; plug-ins never import this.
import builtins
import enum
import typing

from atm_bd_types import (Action, Bead, BeadPatch, BeadStore, CheckState, CollectError, Params, PhaseFacts, Refusal, Stack, Stage, Status,
                          TaskState)

_T = typing.TypeVar("_T")

@typing.dataclass_transform(frozen_default=True)
def _record(cls: type[_T]) -> type[_T]:
    r"""Stub-only: a frozen Rust record whose constructor takes every field in order."""
"#;

const COMMAND_RUNNER: &str = r#"class CommandRunner(typing.Protocol):
    r"""The only process port: collectors read through it, the executor writes through it."""
    def run(self, argv: list[str], stdin: str | None) -> CommandResult: ...
"#;

const BEADS_CACHE: &str = r#"class BeadsCache(BeadStore, typing.Protocol):
    r"""show() from BeadStore plus the phase's listed and ready beads."""
    def list(self, phase: str) -> builtins.list[Bead] | Refusal: ...
    def ready(self, phase: str) -> builtins.list[Bead] | Refusal: ...
"#;

/// `atm_bd_types.pyi`, the plug-in surface.
pub(crate) fn plugin() -> String {
    [
        PLUGIN_HEADER.to_owned(),
        PyStatus::stub(),
        PyStage::stub(),
        PyAssignTransition::stub(),
        PyStartTransition::stub(),
        PyCloseTransition::stub(),
        PyTemplate::stub(),
        PyErrorId::stub(),
        REFUSAL_STUB.to_owned(),
        LAYER_STUB.to_owned(),
        STACK_STUB.to_owned(),
        FINDING_STUB.to_owned(),
        QA_PASS_STUB.to_owned(),
        QA_FAIL_STUB.to_owned(),
        BEAD_STUB.to_owned(),
        PHASE_FILE_STUB.to_owned(),
        BEAD_PATCH_STUB.to_owned(),
        HOOK_REQUEST_STUB.to_owned(),
        HOOK_ACTION_STUB.to_owned(),
        HOOK_REPLY_STUB.to_owned(),
        BEAD_STORE.to_owned(),
        PHASE_FILES.to_owned(),
        PHASE_FILES_CLI_STUB.to_owned(),
        CACHE_STORE_STUB.to_owned(),
        RECORD_DECORATOR.to_owned(),
        PyHook::stub(),
        PyFactKind::stub(),
        PyTaskState::stub(),
        PyCheckState::stub(),
        PyTaskFact::stub(),
        PyTaskEvents::stub(),
        PyRemoteBranch::stub(),
        PyAncestry::stub(),
        PyStackFact::stub(),
        PyTopChecks::stub(),
        PyPrBase::stub(),
        PyCollectError::stub(),
        PyPhaseFacts::stub(),
        PyAssignVars::stub(),
        PyAssign::stub(),
        PyReport::stub(),
        PyNotify::stub(),
        ACTION.to_owned(),
        PARAMS_STUB.to_owned(),
        CRON.to_owned(),
        PyProfile::stub(),
    ]
    .join("\n")
}

/// `atm_bd_core.pyi`, the framework surface.
pub(crate) fn framework() -> String {
    [
        FRAMEWORK_HEADER.to_owned(),
        PyActionKind::stub(),
        PyOutcomeKind::stub(),
        PyPolicy::stub(),
        PyViewRow::stub(),
        PyDecision::stub(),
        PyViewStep::stub(),
        PyViewSprint::stub(),
        PyViewTask::stub(),
        PyViewAction::stub(),
        PyPhaseView::stub(),
        PyActionOutcome::stub(),
        PyTickResult::stub(),
        PyCommandResult::stub(),
        COMMAND_RUNNER.to_owned(),
        BEADS_CACHE.to_owned(),
        PyPorts::stub(),
        "def patch_json(patch: BeadPatch) -> str: ...\n".to_owned(),
        "def stack_of(bead: Bead) -> Stack | None: ...\n".to_owned(),
    ]
    .join("\n")
}
