# pyright: strict
"""Typed records decoded from operation-specific bd, atm and gh JSON output.

The JSON transport stays generic. Callers validate records for the operation
they invoked before passing them to report and graph logic.
"""
from __future__ import annotations

import json
from typing import NotRequired, Required, TypeAlias, TypeGuard, TypedDict

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class DependencyRecord(TypedDict, total=False):
    type: str
    dependency_type: str
    depends_on_id: str
    id: str


class BeadMetadata(TypedDict, total=False):
    branch: str
    checked_bead: str
    difficulty: str
    integration_branch: str
    layer: str | int | float | bool | None
    phase: str
    round: str | int | float | bool | None
    severity: str
    stack: str
    sprint: str
    verdict: str
    worktree: str
    pr_target: str


class BeadRecord(TypedDict):
    id: Required[str]
    status: Required[str]
    title: NotRequired[str]
    close_reason: NotRequired[str]
    labels: NotRequired[list[str]]
    dependencies: NotRequired[list[DependencyRecord]]
    metadata: NotRequired[BeadMetadata]
    parent: NotRequired[str]
    priority: NotRequired[int | str]
    blocked_by: NotRequired[list[str]]


class AtmMember(TypedDict, total=False):
    name: str
    identity: str
    id: str
    agent_type: str
    model: str


class AtmTask(TypedDict):
    task_id: Required[str]
    assignee: NotRequired[str]
    owner: NotRequired[str]
    state: NotRequired[str]
    status: NotRequired[str]


class AtmTaskEvent(TypedDict, total=False):
    event: Required[str]
    at: str
    to_state: str


class PullRequestRef(TypedDict):
    ref: Required[str]


class PullRequest(TypedDict, total=False):
    number: Required[int]
    state: Required[str]
    merged_at: str | None
    mergedAt: str | None
    head: PullRequestRef
    base: PullRequestRef
    isDraft: bool
    statusCheckRollup: list["PullRequestCheck"]
    headRefName: str
    baseRefName: str
    title: str
    mergeStateStatus: str
    mergeable: str


class PullRequestCheck(TypedDict, total=False):
    conclusion: str | None
    state: str | None
    status: str | None


def is_object_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def is_object(value: object) -> TypeGuard[dict[str, object]]:
    if not is_object_mapping(value):
        return False
    return all(isinstance(key, str) for key in value)


def is_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if is_object_list(value):
        return all(is_json_value(item) for item in value)
    if not is_object(value):
        return False
    return all(is_json_value(item) for item in value.values())


def is_json_object(value: object) -> TypeGuard[JsonObject]:
    return is_object(value) and all(is_json_value(item) for item in value.values())


def bead_record_to_json(record: BeadRecord) -> JsonObject:
    """Convert a validated bead DTO for the generic schema validator boundary."""
    decoded: object = json.loads(json.dumps(record))
    if not is_json_object(decoded):
        raise ValueError("validated bead record could not be encoded as a JSON object")
    return decoded


def has_string_fields(value: dict[str, object], fields: tuple[str, ...]) -> bool:
    return all(key not in value or isinstance(value[key], str) for key in fields)


def is_dependency_record(value: object) -> TypeGuard[DependencyRecord]:
    if not is_object(value):
        return False
    kind = value.get("type", value.get("dependency_type"))
    target = value.get("depends_on_id", value.get("id"))
    return (isinstance(kind, str) and isinstance(target, str)
            and has_string_fields(value, ("type", "dependency_type", "depends_on_id", "id")))


def is_bead_metadata(value: object) -> TypeGuard[BeadMetadata]:
    if not is_object(value):
        return False
    string_fields = (
        "branch", "checked_bead", "difficulty", "integration_branch", "phase",
        "severity", "stack", "sprint", "verdict", "worktree", "pr_target",
    )
    if not has_string_fields(value, string_fields):
        return False
    for key in ("layer", "round"):
        item = value.get(key)
        if key in value and item is not None and not isinstance(item, (str, int, float, bool)):
            return False
    return True


def is_bead_record(value: object) -> TypeGuard[BeadRecord]:
    if not is_object(value) or not isinstance(value.get("id"), str) or not isinstance(value.get("status"), str):
        return False
    if not has_string_fields(value, ("status", "title", "close_reason", "parent")):
        return False
    labels = value.get("labels")
    if "labels" in value:
        if not is_object_list(labels) or any(not isinstance(label, str) for label in labels):
            return False
    dependencies = value.get("dependencies")
    if "dependencies" in value:
        if not is_object_list(dependencies) or any(not is_dependency_record(edge) for edge in dependencies):
            return False
    metadata = value.get("metadata")
    if "metadata" in value and not is_bead_metadata(metadata):
        return False
    priority = value.get("priority")
    if "priority" in value and (isinstance(priority, bool) or not isinstance(priority, (int, str))):
        return False
    blocked_by = value.get("blocked_by")
    if "blocked_by" in value:
        if not is_object_list(blocked_by) or any(not isinstance(item, str) for item in blocked_by):
            return False
    return True


def is_bead_records(value: object) -> TypeGuard[list[BeadRecord]]:
    return is_object_list(value) and all(is_bead_record(row) for row in value)


def is_atm_member(value: object) -> TypeGuard[AtmMember]:
    return (is_object(value) and has_string_fields(value, ("name", "identity", "id", "agent_type", "model"))
            and any(isinstance(value.get(key), str) for key in ("name", "identity", "id")))


def is_atm_members(value: object) -> TypeGuard[list[AtmMember]]:
    return is_object_list(value) and all(is_atm_member(row) for row in value)


def is_atm_task(value: object) -> TypeGuard[AtmTask]:
    return (is_object(value) and isinstance(value.get("task_id"), str)
            and has_string_fields(value, ("assignee", "owner", "state", "status")))


def is_atm_tasks(value: object) -> TypeGuard[list[AtmTask]]:
    return is_object_list(value) and all(is_atm_task(row) for row in value)


def is_atm_task_event(value: object) -> TypeGuard[AtmTaskEvent]:
    return (is_object(value) and isinstance(value.get("event"), str)
            and has_string_fields(value, ("at", "to_state")))


def is_atm_task_events(value: object) -> TypeGuard[list[AtmTaskEvent]]:
    return is_object_list(value) and all(is_atm_task_event(row) for row in value)


def is_pull_request_ref(value: object) -> TypeGuard[PullRequestRef]:
    return is_object(value) and isinstance(value.get("ref"), str)


def is_pull_request_check(value: object) -> TypeGuard[PullRequestCheck]:
    if not is_object(value):
        return False
    return all(key not in value or value[key] is None or isinstance(value[key], str)
               for key in ("conclusion", "state", "status"))


def is_pull_request(value: object) -> TypeGuard[PullRequest]:
    if not is_object(value) or not isinstance(value.get("state"), str) or not has_string_fields(
        value, ("state", "headRefName", "baseRefName", "title", "mergeStateStatus", "mergeable")
    ):
        return False
    if isinstance(value.get("number"), bool) or not isinstance(value.get("number"), int):
        return False
    if "isDraft" in value and not isinstance(value["isDraft"], bool):
        return False
    for key in ("merged_at", "mergedAt"):
        if key in value and value[key] is not None and not isinstance(value[key], str):
            return False
    for key in ("head", "base"):
        if key in value and not is_pull_request_ref(value[key]):
            return False
    if "statusCheckRollup" in value:
        checks = value["statusCheckRollup"]
        if not is_object_list(checks) or any(not is_pull_request_check(check) for check in checks):
            return False
    return True


def is_pull_requests(value: object) -> TypeGuard[list[PullRequest]]:
    return is_object_list(value) and all(is_pull_request(row) for row in value)


def is_pull_request_pages(value: object) -> TypeGuard[list[list[PullRequest]]]:
    return is_object_list(value) and all(is_pull_requests(page) for page in value)
