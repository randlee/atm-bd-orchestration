from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from . import command
from .atm_source import sprint_state_of
from .result import CommandFailed, Err, Ok, ParseFailed, Result, Timeout
from .types import Bead


@dataclass(frozen=True)
class BeadRows:
    """One bd list response retained both as typed beads and raw rows for read-only projections."""

    beads: tuple[Bead, ...]
    rows: tuple[dict[str, Any], ...]


def _bead(raw: dict[str, Any]) -> Bead:
    def when(name: str) -> datetime | None:
        value = raw.get(name)
        return datetime.fromisoformat(value).astimezone(UTC) if value else None
    close_reason = raw.get("close_reason")
    return Bead(
        raw["id"], raw["title"], sprint_state_of(raw["status"]), tuple(raw.get("labels", ())), raw.get("parent"),
        tuple(raw.get("blocked_by", ())), raw.get("assignee"), raw.get("metadata", {}),
        when("created_at") or datetime.now(UTC), when("claimed_at"), when("closed_at"),
        close_reason if isinstance(close_reason, str) else None, raw["status"],
    )


def _raw(argv: list[str], *, cwd: str | None = None) -> Result[list[dict[str, Any]]]:
    line = " ".join(argv)
    completed = command.run(argv, f"run `{line}` by hand and repair what it reports", cwd=cwd)
    if isinstance(completed, Err):
        error = completed.error
        if isinstance(error, Timeout):
            fix = (f"bd or Dolt is slow or the host is loaded; the call waited {error.seconds}s; "
                   f"check the host load, then run `{line}` by hand to see how long it takes")
            return Err(replace(error, fix=fix))
        if isinstance(error, CommandFailed):
            fix = (f"`{line}` exited {error.code}; read its stderr above and repair that "
                   f"(is bd installed and the Dolt server up?), then run it by hand to confirm")
            return Err(replace(error, fix=fix))
        return completed
    try:
        raw = json.loads(completed.value.stdout)
        if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
            raise ValueError("expected an array of bead objects")
        return Ok(raw)
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return Err(ParseFailed("parse_failed", "bd", str(error), f"run `{line}` by hand; its JSON is not the expected array of bead objects, so upgrade or repair bd"))


def _run(argv: list[str], *, cwd: str | None = None) -> Result[tuple[Bead, ...]]:
    raw = _raw(argv, cwd=cwd)
    if isinstance(raw, Err):
        return raw
    try:
        return Ok(tuple(_bead(item) for item in raw.value))
    except (KeyError, TypeError, ValueError) as error:
        return Err(ParseFailed("parse_failed", "bd", str(error), "repair bd JSON"))


def where(*, cwd: str | None = None) -> Result[str]:
    """The absolute beads directory, as the dev close hook reads it: BEADS_DIR, else `bd where --json` .path."""
    configured = os.environ.get("BEADS_DIR")
    if configured:
        return Ok(configured)
    fix = "set BEADS_DIR or repair `bd where --json` to print an absolute beads path"
    completed = command.run(["bd", "where", "--json"], fix, cwd=cwd)
    if isinstance(completed, Err):
        return completed
    try:
        path = json.loads(completed.value.stdout).get("path")
    except (AttributeError, json.JSONDecodeError) as error:
        return Err(ParseFailed("parse_failed", "bd where", str(error), fix))
    if not isinstance(path, str) or not os.path.isabs(path):
        return Err(ParseFailed("parse_failed", "bd where", f"path {path!r} is not absolute", fix))
    return Ok(path)


def show(ids: tuple[str, ...]) -> Result[tuple[Bead, ...]]:
    return Ok(()) if not ids else _run(["bd", "show", *ids, "--json"])


def _only_not_found(stderr: str, ids: tuple[str, ...]) -> bool:
    lines = [line.strip() for line in stderr.splitlines() if line.strip() and not line.strip().startswith("Hint:")]
    return bool(lines) and all(line in {f"Issue {bead_id} not found" for bead_id in ids} for line in lines)


def show_tasks(ids: tuple[str, ...]) -> Result[tuple[Bead, ...]]:
    """The beads of open ATM task ids. A task need not be a bead: bd returns the beads it has and names the
    others on stderr, and exits 1 when no id is a bead, which is no beads, not a failed read (#590)."""
    found = show(ids)
    if isinstance(found, Err) and isinstance(found.error, CommandFailed) and _only_not_found(found.error.stderr, ids):
        return Ok(())
    return found


def open_rows(label: str) -> Result[BeadRows]:
    raw = _raw(["bd", "list", "-l", label, "-n", "0", "--json"])
    if isinstance(raw, Err):
        return raw
    try:
        return Ok(BeadRows(tuple(_bead(item) for item in raw.value), tuple(raw.value)))
    except (KeyError, TypeError, ValueError) as error:
        return Err(ParseFailed("parse_failed", "bd", str(error), "repair bd JSON"))


def ready(label: str) -> Result[tuple[Bead, ...]]:
    return _run(["bd", "ready", "-l", label, "--json"])


def closed_stage_rows(phase: str, stage: str, *, cwd: str | None = None) -> Result[list[dict[str, Any]]]:
    """Read one run-tab stage, on demand, never the full closed phase."""
    result = _raw(["bd", "list", "-l", f"phase-{phase},stage:{stage}", "--status", "closed", "-n", "0", "--json"], cwd=cwd)
    if isinstance(result, Err):
        return result
    if not all(isinstance(row.get("id"), str) for row in result.value):
        return Err(ParseFailed("parse_failed", "bd", "expected bead objects with ids", "repair bd JSON"))
    return result


def show_rows(ids: tuple[str, ...], *, cwd: str | None = None) -> Result[list[dict[str, Any]]]:
    return Ok([]) if not ids else _raw(["bd", "show", *ids, "--json"], cwd=cwd)


def ancestors(beads: tuple[Bead, ...]) -> Result[tuple[Bead, ...]]:
    known = {bead.id: bead for bead in beads}
    frontier = {bead.parent for bead in beads if bead.parent and bead.parent not in known}
    visited: set[str] = set()
    while frontier:
        visited.update(frontier)
        found = show(tuple(sorted(frontier)))
        if isinstance(found, Err):
            return found
        for bead in found.value:
            known[bead.id] = bead
        frontier = {bead.parent for bead in found.value if bead.parent and bead.parent not in known
                    and bead.parent not in visited}
    return Ok(tuple(known.values()))
