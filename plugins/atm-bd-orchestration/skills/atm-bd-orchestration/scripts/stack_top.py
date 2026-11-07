# pyright: strict
"""Select a phase's current stack top from its canonical bead ledger."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias, TypeGuard

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def is_object_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def is_json_object(value: object) -> TypeGuard[JsonObject]:
    if not is_object_mapping(value):
        return False
    for key, item in value.items():
        if not isinstance(key, str) or not is_json_value(item):
            return False
    return True


def is_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if is_object_list(value):
        return all(is_json_value(item) for item in value)
    return is_json_object(value)


def is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def stack_bead_id(root: str) -> str:
    """Return the stack ledger bead ID for a phase root."""
    return f"{root}.stack"


@dataclass(frozen=True)
class StackTop:
    pr: int | None
    branch: str | None
    head: str | None


@dataclass(frozen=True)
class StackTopMismatch:
    ledger_top: StackTop | None
    hosted_top: int | None


def select_passed_unlinked_top(layers: list[JsonValue]) -> StackTop | None:
    """Return the passed first layer while it has no hosted stack, excluding holds."""
    for layer in reversed(layers):
        if not is_json_object(layer) or layer.get("held_on") or layer.get("linked") is not False:
            continue
        pr, branch, head = layer.get("pr"), layer.get("branch"), layer.get("head")
        if type(pr) is not int or not isinstance(branch, str) or not branch.strip() or not isinstance(head, str) or not head.strip():
            raise ValueError("passed stack layer must have a PR, branch and head")
        assert isinstance(pr, int)
        return StackTop(pr, branch, head)
    return None


def select_confirmed_stack_top(
    ledger_layers: list[JsonValue], hosted_prs: list[int] | None = None,
) -> StackTop | StackTopMismatch:
    """Select the last linked ledger layer and compare it with hosted membership."""
    linked: list[StackTop] = []
    for layer in ledger_layers:
        if not is_json_object(layer):
            raise ValueError("stack layer must be an object")
        if layer.get("linked") is not True:
            continue
        pr, branch, head = layer.get("pr"), layer.get("branch"), layer.get("head")
        if type(pr) is not int or not isinstance(branch, str) or not branch.strip() or not isinstance(head, str) or not head.strip():
            raise ValueError("linked stack layer must have a PR, branch and head")
        assert isinstance(pr, int)
        linked.append(StackTop(pr, branch, head))
    ledger_top = linked[-1] if linked else None
    if hosted_prs is None:
        return ledger_top or StackTop(None, None, None)
    hosted_top = hosted_prs[-1] if hosted_prs else None
    if (ledger_top.pr if ledger_top else None) != hosted_top:
        return StackTopMismatch(ledger_top, hosted_top)
    return ledger_top or StackTop(None, None, None)


# A live selection can name the trunk without resolving its Git head. Callers own Git I/O.
LiveTop = StackTop


class LedgerError(ValueError):
    def __init__(self, code: str, message: str, fix: str):
        super().__init__(f"{code}: {message}; {fix}")
        self.code, self.fix = code, fix


def is_landed(metadata: JsonObject) -> bool:
    """A recorded landing with no current layers is landed; subsequent layers are live."""
    layers = metadata.get("layers", [])
    archived = metadata.get("landed_layers", [])
    if not isinstance(layers, list) or not isinstance(archived, list):
        raise ValueError("stack bead metadata.layers and metadata.landed_layers must be arrays")
    if layers:
        last = layers[-1]
        if not is_json_object(last) or not all(isinstance(last.get(key), str) and str(last.get(key)).strip() for key in ("branch", "head")):
            raise ValueError("last stack layer must have non-empty branch and head strings")
    if any(not is_json_object(layer) for layer in layers):
        raise ValueError("stack ledger layers must be objects")
    # Phase br's hand-recorded landings archived PR numbers, not full layer rows.
    archived_prs: set[int] = set()
    for layer in archived:
        number = layer.get("pr") if is_json_object(layer) else layer
        if type(number) is not int or number <= 0:
            raise ValueError("landed_layers must contain positive PR numbers or layer objects with a PR")
        archived_prs.add(number)
    if layers and archived and all(is_json_object(layer) and layer.get("pr") in archived_prs for layer in layers):
        raise LedgerError("LEDGER.STALE_LANDING", "current layers are all in landed_layers",
                          "stack-landed was not run or layers was hand-edited; run "
                          f"`stack-landed <stack-bead> --head {metadata.get('landed_head') or '<merged-sha>'} "
                          f"--stack {metadata.get('stack_number') or metadata.get('landed_stack_number') or '<number>'}`")
    return bool(metadata.get("landed_head")) and not layers


def select_live_top(
    metadata: JsonObject, hosted_prs: list[int] | None = None, *, bead: str = "<stack-bead>",
) -> LiveTop | StackTopMismatch:
    """Select using current ledger state, ignoring hosted membership of a landed stack."""
    try:
        landed = is_landed(metadata)
    except LedgerError as error:
        raise LedgerError(error.code, f"{bead}: current layers are all in landed_layers",
                          error.fix.replace("<stack-bead>", bead)) from error
    if landed:
        trunk = metadata.get("pr_target") or metadata.get("trunk")
        if not isinstance(trunk, str) or not trunk.strip():
            raise ValueError("landed stack ledger must name its trunk/pr_target")
        return LiveTop(None, trunk, None)
    layers = metadata.get("layers", [])
    assert isinstance(layers, list)
    return select_confirmed_stack_top(layers, hosted_prs)


def select_stack_top(
    bead: JsonObject,
    pr_target: object,
    resolve_head: Callable[[str], object],
) -> tuple[str, str]:
    """Compatibility wrapper for callers without hosted membership."""
    metadata = bead.get("metadata")
    if metadata is not None and not is_json_object(metadata):
        raise ValueError("stack bead metadata must be an object or null")
    layers = metadata.get("layers", []) if metadata is not None else []
    if not isinstance(layers, list):
        raise ValueError("stack bead metadata.layers must be an array")
    if layers:
        last = layers[-1]
        if not is_json_object(last):
            raise ValueError("last stack layer must have non-empty branch and head strings")
        branch, head = last.get("branch"), last.get("head")
        if not isinstance(branch, str) or not branch.strip() or not isinstance(head, str) or not head.strip():
            raise ValueError("last stack layer must have non-empty branch and head strings")
    selected = select_confirmed_stack_top(layers)
    if isinstance(selected, StackTop) and selected.branch is not None and selected.head is not None:
        return selected.branch, selected.head
    passed = select_passed_unlinked_top(layers)
    if passed is not None:
        assert passed.branch is not None and passed.head is not None
        return passed.branch, passed.head
    if not isinstance(pr_target, str) or not pr_target.strip():
        raise ValueError("pr_target must be a non-empty string")
    head = resolve_head(pr_target)
    if not isinstance(head, str) or not head.strip():
        raise ValueError(f"origin/{pr_target} has no resolvable head")
    return pr_target, head
