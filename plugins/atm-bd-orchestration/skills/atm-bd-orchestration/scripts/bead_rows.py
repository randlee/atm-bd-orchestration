# pyright: strict
"""Bead row types, typed pour problems, metadata repairs and the repository-pinned `bd` wrapper `bead-groups` uses.

`row_type_issues` and `schema_records` report typed row errors with a repair selected from the field and value
kind; `Bd` pins every `bd` subprocess to one repository's beads database.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from pydantic import TypeAdapter, ValidationError

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "atm-beads" / "scripts"))
from bead_formulas import Bd as BaseBd, BdError  # noqa: E402
from operation_models import JsonObject, matches_typeddict  # noqa: E402


class TargetError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.target_id: str | None = None


def beads_environment(repo: Path) -> dict[str, str]:
    """Pin subprocesses to this repository, ignoring the caller's beads database."""
    return {**os.environ, "BEADS_DIR": str(repo / ".beads")}


class Bd(BaseBd):
    def __init__(self, repo: Path):
        super().__init__()
        self.repo = repo

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        argv = [self.executable, *args]
        try:
            proc = subprocess.run(argv, cwd=self.repo, env=beads_environment(self.repo), text=True, capture_output=True)
        except OSError as exc:
            raise TargetError("BEAD_GROUPS_IO", f"{' '.join(argv)} could not run: {exc}; install bd and retry") from exc
        self.log.append((argv, proc.returncode))
        if check and proc.returncode:
            raise BdError(argv, proc.returncode, proc.stdout, proc.stderr)
        return proc


class Metadata(TypedDict, total=False):
    phase: str
    sprint: str
    stack: str
    layer: int | None
    difficulty: str
    branch: str
    worktree: str
    pr_target: str
    requirements: list[str]
    adrs: list[str]
    owned_paths: list[str]
    quick_fix: bool
    predecessors: list[str]
    trunk: str
    stack_number: int | None
    layers: list[StackLayerRecord]


class StackLayerRecord(TypedDict):
    branch: str
    pr: int
    head: str
    base: str
    linked: bool


class BeadRow(TypedDict):
    id: NotRequired[str]
    title: NotRequired[str]
    status: NotRequired[str]
    priority: NotRequired[int | str | bool | None]
    issue_type: NotRequired[str]
    labels: NotRequired[list[str]]
    parent: NotRequired[str | None]
    metadata: NotRequired[Metadata]


class ProblemKind(StrEnum):
    MISSING = "missing"
    SCHEMA_INVALID = "schema_invalid"
    PREDECESSOR_FAILED = "predecessor_failed"
    PREVIEW_FAILED = "preview_failed"
    ALREADY_POURED = "already_poured"


class PourProblem(TypedDict):
    kind: ProblemKind
    message: str


class RowIssueKind(StrEnum):
    OPTIONAL_METADATA = "optional_metadata"
    REQUIRED_METADATA = "required_metadata"
    ROW_FIELD = "row_field"


class RowIssue(TypedDict):
    bead: str
    key: str
    kind: RowIssueKind
    message: str


def row_type_issues(row: JsonObject) -> list[RowIssue]:
    """Report typed row errors with a repair selected from the field and value kind."""
    bead = str(row.get("id", "?"))
    issues: list[RowIssue] = []
    metadata = row.get("metadata")
    for field, value in row.items():
        if field == "metadata" and isinstance(value, dict):
            for name, item in value.items():
                if not matches_typeddict({name: item}, Metadata):
                    required = {"branch", "worktree", "pr_target", "difficulty"}
                    labels = row.get("labels")
                    if isinstance(labels, list) and "stage:sprint" in labels:
                        required.update({"layer", "requirements", "adrs"})
                    if isinstance(labels, list) and "stage:stack" in labels:
                        required.update({"trunk", "stack_number", "layers"})
                    repair = repair_metadata(bead, name, item, metadata, optional=name not in required)
                    issues.append({"bead": bead, "key": name,
                                   "kind": RowIssueKind.REQUIRED_METADATA if name in required else RowIssueKind.OPTIONAL_METADATA,
                                   "message": f"{bead}: metadata.{name}: invalid value {item!r}; Fix: {repair}"})
        elif not matches_typeddict({field: value}, BeadRow):
            commands = {"status": f"bd update {bead} --status <status>",
                        "labels": f"bd label add {bead} <label>",
                        "parent": f"bd update {bead} --parent <parent-id>"}
            repair = commands.get(field, f"bd update {bead} --metadata @<file>")
            issues.append({"bead": bead, "key": field, "kind": RowIssueKind.ROW_FIELD,
                           "message": f"{bead}: {field}: invalid value {value!r}; Fix: {repair}"})
    return issues


def repair_metadata(bead: str, key: str, value: object, metadata: object, *, optional: bool) -> str:
    if optional:
        return f"bd update {bead} --unset-metadata {key}"
    strings = {"branch": "<branch>", "pr_target": "<branch>", "trunk": "<branch>", "worktree": "<path>",
               "phase": "<phase>", "sprint": "<sprint>", "stack": "<stack>", "difficulty": "<difficulty>",
               "commit": "<commit-sha>", "checked_bead": "<bead-id>", "stack_bead": "<bead-id>",
               "sprint_bead": "<bead-id>", "dev_bead": "<bead-id>", "qa_bead": "<bead-id>", "sanity_bead": "<bead-id>"}
    if key in strings:
        return f"bd update {bead} --set-metadata {key}={strings[key]}"
    corrected: dict[str, object] = TypeAdapter(dict[str, object]).validate_python(metadata) if isinstance(metadata, dict) else {}
    if key in {"layer", "round", "max_sanity_rounds"}:
        corrected[key] = int(value) if isinstance(value, str) and value.isdecimal() else 1
    elif key in {"requirements", "adrs"}:
        corrected[key] = ["NONE"]
    elif key == "owned_paths":
        corrected[key] = ["<path>"]
    elif key == "reviewers_round1":
        corrected[key] = ["<reviewer>"]
    elif key == "layers":
        corrected[key] = []
    elif key == "stack_number":
        corrected[key] = None
    return f"bd update {bead} --metadata @<file> (write corrected full metadata JSON to <file>: {json.dumps(corrected, sort_keys=True)})"


def schema_records(schema: Any, phase: str, prospective: list[JsonObject], bd: BaseBd | None = None) -> list[tuple[str, str]]:
    """Use validator locations and error kinds, not rendered validation prose, for repairs."""
    if bd is None:
        current = schema.load_phase(phase)
    else:
        proc = bd.run("list", "-l", f"phase-{phase}", "--status", "open,in_progress,blocked,deferred,closed",
                      "--include-gates", "-n", "0", "--json")
        try:
            current = schema.json_objects(json.loads(proc.stdout), context="bd list output")
        except (ValueError, TypeError) as exc:
            raise TargetError("BEAD_GROUPS_IO", f"bd list -l phase-{phase} --json returned invalid output (exit {proc.returncode}): {exc}; inspect bd and retry") from exc
    rows: list[JsonObject] = [row for row in current if row.get("status") != "closed"] + prospective
    found: list[tuple[str, str]] = []
    for row in rows:
        bead = str(row.get("id", "?"))
        found.extend((issue["bead"], issue["message"]) for issue in row_type_issues(row))
        raw_labels = row.get("labels")
        labels = raw_labels if isinstance(raw_labels, list) else []
        if "anchor" in labels:
            continue
        if re.fullmatch(r".+-phase-[a-z0-9]+", bead):
            model = schema.RootBead
        elif row.get("issue_type") == "gate":
            model = schema.GateBead
        else:
            stages = [label for label in labels if isinstance(label, str) and label.startswith("stage:")]
            model = schema.MODELS_BY_STAGE.get(stages[0]) if len(stages) == 1 else None
        if model is None:
            found.append((bead, f"{bead}: labels: no stage model; Fix: bd label add {bead} <stage:label>"))
            continue
        try:
            model.model_validate(row)
        except ValidationError as error:
            for detail in error.errors():
                loc = detail["loc"]
                key = str(loc[1] if len(loc) > 1 and loc[0] == "metadata" else loc[0] if loc else "metadata")
                meta = row.get("metadata", {})
                if key in {"status", "parent", "labels"}:
                    commands = {"status": f"bd update {bead} --status <status>", "parent": f"bd update {bead} --parent <parent-id>", "labels": f"bd label add {bead} <label>"}
                    repair = commands[key]
                elif key == "dependencies":
                    repair = f"bd dep add {bead} <bead-id> --type blocks"
                else:
                    value = meta.get(key) if isinstance(meta, dict) else None
                    repair = repair_metadata(bead, key, value, meta, optional=False)
                found.append((bead, f"{bead}: {key}: {detail['msg']}; Fix: {repair}"))
    return found
