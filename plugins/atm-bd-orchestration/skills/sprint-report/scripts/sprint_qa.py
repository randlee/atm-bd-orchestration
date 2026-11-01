# pyright: strict
"""QA state and finding counts shared by table and DAG reports."""

import sys

import json as _core_json
import sys as _core_sys
from pathlib import Path as _CorePath
_core = next((candidate for parent in _CorePath(__file__).resolve().parents
              for candidate in (parent / ".atm-bd/scripts", parent / "plugins/atm-bd-orchestration/core/scripts")
              if (candidate / "core_paths.py").is_file()), None)
if _core is None:
    print(_core_json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": "run atm-bd skill --dest <repository>"}}), file=_core_sys.stderr)
    raise SystemExit(3)
_core_sys.path.insert(0, str(_core))
import core_paths as _core_paths  # noqa: E402
from result import Err as _CoreErr  # noqa: E402
_core_resolved = _core_paths.core_scripts_dir(_CorePath(__file__))
if isinstance(_core_resolved, _CoreErr):
    print(_core_json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": _core_resolved.error.fix}}), file=_core_sys.stderr)
    raise SystemExit(3)

from operation_models import BeadMetadata, BeadRecord


def metadata(bead: BeadRecord) -> BeadMetadata:
    return bead.get("metadata", {})

def choose_round(candidates: list[BeadRecord]) -> BeadRecord | None:
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

def qa_verdict(qa: BeadRecord) -> str:
    qa_meta = metadata(qa)
    verdict = str(qa_meta.get("verdict") or "").upper()
    if not verdict:
        close_reason = str(qa.get("close_reason") or "")
        verdict = close_reason.split(":", 1)[0].strip().upper()
    if verdict not in {"PASS", "FAIL"}:
        verdict = "IN PROGRESS" if qa.get("status") != "closed" else "UNKNOWN"
    return verdict

def qa_icon(qa: BeadRecord | None, findings: list[BeadRecord]) -> str:
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

def findings_summary(findings: list[BeadRecord]) -> str:
    counts = dict.fromkeys(("blocking", "important", "minor"), 0)
    for finding in findings:
        if finding.get("status") == "closed":
            continue
        labels = finding.get("labels", [])
        severity = str(metadata(finding).get("severity") or next(
            (label.removeprefix("severity:") for label in labels
             if label.startswith("severity:")), ""
        )).lower()
        severity = {"critical": "blocking", "low": "minor"}.get(severity, severity)
        if severity not in counts:
            print(f"sprint-report: unknown severity for finding {finding.get('id')}", file=sys.stderr)
            return "?"
        counts[severity] += 1
    return ":".join(str(count) for count in counts.values())
