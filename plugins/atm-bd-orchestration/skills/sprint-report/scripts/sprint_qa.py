# pyright: strict
"""QA state and finding counts shared by table and DAG reports."""

import sys
from typing import TypeAlias, TypeGuard

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


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


def metadata(bead: JsonObject) -> JsonObject:
    value = bead.get("metadata")
    return value if is_json_object(value) else {}

def choose_round(candidates: list[JsonObject]) -> JsonObject | None:
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda bead: (
            int(str(metadata(bead).get("round", "0")))
            if str(metadata(bead).get("round", "0")).isdigit() else 0,
            str(bead.get("id", "")),
        ),
    )

def qa_verdict(qa: JsonObject) -> str:
    qa_meta = metadata(qa)
    verdict = str(qa_meta.get("verdict") or "").upper()
    if not verdict:
        close_reason = str(qa.get("close_reason") or "")
        verdict = close_reason.split(":", 1)[0].strip().upper()
    if verdict not in {"PASS", "FAIL"}:
        verdict = "IN PROGRESS" if qa.get("status") != "closed" else "UNKNOWN"
    return verdict

def qa_icon(qa: JsonObject | None, findings: list[JsonObject]) -> str:
    if not qa:
        return ""
    verdict = qa_verdict(qa)
    if verdict == "FAIL" or any(finding.get("status") != "closed" for finding in findings):
        return "🚩"
    if verdict == "PASS":
        return "✅"
    if qa.get("status") == "in_progress":
        return "🌀"
    if qa.get("status") in {"open", "deferred", "blocked"}:
        return "📥"
    return ""

def findings_summary(findings: list[JsonObject]) -> str:
    counts = dict.fromkeys(("blocking", "important", "minor"), 0)
    for finding in findings:
        if finding.get("status") == "closed":
            continue
        raw_labels = finding.get("labels")
        labels = raw_labels if is_object_list(raw_labels) else []
        severity = str(metadata(finding).get("severity") or next(
            (label.removeprefix("severity:") for label in labels
             if isinstance(label, str) and label.startswith("severity:")), ""
        )).lower()
        severity = {"critical": "blocking", "low": "minor"}.get(severity, severity)
        if severity not in counts:
            print(f"sprint-report: unknown severity for finding {finding.get('id')}", file=sys.stderr)
            return "?"
        counts[severity] += 1
    return ":".join(str(count) for count in counts.values())
