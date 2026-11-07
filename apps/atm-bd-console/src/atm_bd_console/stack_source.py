"""The shared bounded stack-ledger read; failures retain their original Result error."""
from __future__ import annotations

from . import beads_source
from .log import TickLog
from .result import Err, NotFound, Ok, ParseFailed, Result


def read_stack_ledger(root_id: str, logger: TickLog | None = None, *, runner=None, cwd: str | None = None) -> Result[tuple[int, ...]]:
    """Read the linked ledger without collapsing read, malformed and empty states."""
    bead_id = f"{root_id}.stack"
    shown = beads_source.show((bead_id,)) if runner is None else beads_source.show((bead_id,), runner=runner, cwd=cwd)
    if logger is not None:
        shown = logger.result("beads.show_stack", shown, task_ids=[bead_id])
    if isinstance(shown, Err):
        return shown
    if not shown.value:
        return Err(NotFound("not_found", bead_id, f"inspect `bd show {bead_id} --json` and restore the stack bead"))
    if len(shown.value) != 1:
        return Err(ParseFailed("parse_failed", bead_id, "expected exactly one stack bead",
                               f"inspect `bd show {bead_id} --json` and repair the stack bead"))
    if shown.value[0].id != bead_id:
        return Err(ParseFailed("parse_failed", bead_id, f"read returned {shown.value[0].id}",
                               f"inspect `bd show {bead_id} --json` and repair the stack bead"))
    layers = shown.value[0].metadata.get("layers")
    fix = f"inspect `bd show {bead_id} --json` and repair metadata.layers"
    if not isinstance(layers, list):
        return Err(ParseFailed("parse_failed", f"{bead_id}.metadata.layers", "expected an array", fix))
    linked = []
    seen: set[int] = set()
    for index, layer in enumerate(layers):
        if (not isinstance(layer, dict) or type(layer.get("pr")) is not int or layer["pr"] <= 0
                or type(layer.get("linked")) is not bool):
            return Err(ParseFailed("parse_failed", f"{bead_id}.metadata.layers[{index}]",
                                   "expected a positive pr and boolean linked", fix))
        if layer["pr"] in seen:
            return Err(ParseFailed("parse_failed", f"{bead_id}.metadata.layers[{index}]",
                                   f"duplicate pr {layer['pr']}", fix))
        seen.add(layer["pr"])
        if layer["linked"]:
            linked.append(layer["pr"])
    return Ok(tuple(linked))

