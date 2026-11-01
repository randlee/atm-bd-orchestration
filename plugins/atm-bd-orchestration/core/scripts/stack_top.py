# pyright: strict
"""Select a phase's current stack top from its canonical bead ledger."""

from __future__ import annotations

from collections.abc import Callable
from typing import NotRequired, TypeAlias, TypeGuard, TypedDict

class StackLayer(TypedDict):
    branch: str
    pr: int
    base: str
    head: str
    linked: NotRequired[bool]


class StackMetadata(TypedDict):
    layers: list[StackLayer]
    stack_number: int | None


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


def select_stack_top(
    bead: JsonObject,
    pr_target: object,
    resolve_head: Callable[[str], object],
) -> tuple[str, str]:
    metadata = bead.get("metadata")
    if metadata is not None and not is_json_object(metadata):
        raise ValueError("stack bead metadata must be an object or null")
    layers = metadata.get("layers", []) if metadata is not None else []
    if not isinstance(layers, list):
        raise ValueError("stack bead metadata.layers must be an array")
    for layer in reversed(layers):
        if not is_json_object(layer):
            raise ValueError("last stack layer must have non-empty branch and head strings")
        linked = layer.get("linked", True)
        if not isinstance(linked, bool):
            raise ValueError("stack layer linked flag must be boolean")
        if not linked:
            continue
        branch = layer.get("branch")
        head = layer.get("head")
        if isinstance(branch, str) and isinstance(head, str):
            if not branch.strip() or not head.strip():
                raise ValueError("last stack layer must have non-empty branch and head strings")
            return branch, head
        raise ValueError("last stack layer must have non-empty branch and head strings")
    trunk = metadata.get("trunk") if metadata is not None else None
    if trunk is not None and (not isinstance(trunk, str) or not trunk.strip()):
        raise ValueError("stack trunk must be a non-empty string")
    target = trunk if isinstance(trunk, str) else pr_target
    if not isinstance(target, str) or not target.strip():
        raise ValueError("stack trunk or pr_target must be a non-empty string")
    head = resolve_head(target)
    if not isinstance(head, str) or not head.strip():
        raise ValueError(f"origin/{target} has no resolvable head")
    return target, head
