#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.20.0"]
# ///
# pyright: strict
"""Pure command planner for lite task-close transitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeAlias, TypeVar

from atm_bd_types import CloseVars, Error, ErrorKind, Transition

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Err:
    error: Error


Result: TypeAlias = Ok[T] | Err


@dataclass(frozen=True)
class Observed:
    """State snapshot used for idempotency decisions; gathering it is runner work."""

    task_id: str
    bead_id: str
    lead: str
    reason: str = ""
    findings_file: str = ""
    pr_number: str = ""
    pr_base: str = ""
    pr_head: str = ""
    pr_sha: str = ""
    stack_top: str = ""
    gate_stacked: bool = False
    bead_closed: bool = False
    layer_linked: bool = False
    qa_assigned: bool = False
    task_closed: bool = False
    qa_closed: bool = False
    findings_poured: bool = False
    notified: bool = False
    refused: bool = False


Predicate: TypeAlias = Callable[[Observed], bool]


@dataclass(frozen=True)
class Command:
    argv: tuple[str, ...]
    idempotent_when: Predicate


def _error(message: str, fix: str) -> Err:
    return Err(Error(ErrorKind.CONFIG_INVALID, message, fix))


def _commands(*items: tuple[tuple[str, ...], Predicate]) -> Ok[list[Command]]:
    return Ok([Command(argv, satisfied) for argv, satisfied in items])


def plan(transition: Transition, vars: CloseVars, observed: Observed) -> Result[list[Command]]:
    """Return only the ordered external commands still required for a transition."""
    match transition:
        # Dev close
        case Transition.DEV_CLOSE:
            if not observed.gate_stacked:
                return _error("pull request is not stacked on the current stack top", "Repair the PR base and pushed stack ancestry, then rerun the same hook command.")
            return _commands(
                (("bd", "close", observed.bead_id), lambda state: state.bead_closed),
                (("atm-bd", "stack", "link", observed.bead_id), lambda state: state.layer_linked),
                (("atm", "task", "assign", observed.lead, "--task-id", f"{observed.bead_id}.group-qa", "--template", "skills/atm-bd-lite/templates/qa-template.xml.j2"), lambda state: state.qa_assigned),
                (("atm", "task", "close", observed.task_id, "completed"), lambda state: state.task_closed),
            )

        # Fix close
        case Transition.FIX_CLOSE:
            if not observed.gate_stacked:
                return _error("pull request is not stacked on the current stack top", "Repair the PR base and pushed stack ancestry, then rerun the same hook command.")
            return _commands(
                (("bd", "close", observed.bead_id), lambda state: state.bead_closed),
                (("atm-bd", "stack", "link", observed.bead_id), lambda state: state.layer_linked),
                (("atm", "task", "assign", observed.lead, "--task-id", f"{observed.bead_id}.group-qa", "--template", "skills/atm-bd-lite/templates/qa-template.xml.j2"), lambda state: state.qa_assigned),
                (("atm", "task", "close", observed.task_id, "completed"), lambda state: state.task_closed),
            )

        # QA pass
        case Transition.QA_PASS:
            return _commands(
                (("bd", "close", observed.bead_id), lambda state: state.qa_closed),
                (("atm", "send", observed.lead, "QA PASS", "--task-id", observed.bead_id), lambda state: state.notified),
                (("atm", "task", "close", observed.task_id, "completed"), lambda state: state.task_closed),
            )

        # QA fail
        case Transition.QA_FAIL:
            return _commands(
                (("atm-bd", "pour", "--source", observed.findings_file, "--formula", "finding-group.formula.toml.j2"), lambda state: state.findings_poured),
                (("atm", "send", observed.lead, "QA FAIL", "--task-id", observed.bead_id), lambda state: state.notified),
                (("atm", "task", "close", observed.task_id, "completed"), lambda state: state.task_closed),
            )

        # Refused
        case Transition.REFUSED:
            return _commands(
                (("bd", "update", observed.bead_id, "--status", "open", "--append-notes", observed.reason), lambda state: state.refused),
                (("atm", "send", observed.lead, "task refused", "--task-id", observed.bead_id), lambda state: state.notified),
                (("atm", "task", "close", observed.task_id, "refused", observed.reason), lambda state: state.task_closed),
            )
