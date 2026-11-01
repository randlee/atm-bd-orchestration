#!/usr/bin/env python3
"""Next triage agent from labels and gate config. Prints one JSON object."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

GAP = ("status/needs-info", "status/needs-repro", "status/needs-design")


def load_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def logins(table: dict, key: str) -> set[str]:
    block = table.get(key) or {}
    raw = block.get("logins") or []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"{key}.logins must be a list of strings")
    return set(raw)


def role_labels(login: str, home: dict, repo: dict) -> list[str]:
    """Repo file contributes contributors only. Approver is home-only."""
    approvers = logins(home, "approver")
    contributors = logins(home, "contributor") | logins(repo, "contributor")
    if login in approvers:
        return ["approver", "contributor"]
    if login in contributors:
        return ["contributor"]
    return []


def _holds(repo: dict, gate: str) -> list[str]:
    block = (repo.get("gates") or {}).get(gate) or {}
    raw = block.get("holds") or []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"gates.{gate}.holds must be a list of strings")
    return raw


def holding(point: str, labels: set[str], priority: int | None, repo: dict) -> str | None:
    if point in _holds(repo, "whitelist") and "contributor" not in labels:
        return "whitelist"
    approver_holds = _holds(repo, "approver")
    if approver_holds and point in approver_holds and "approver" not in labels:
        return "approver"
    priority_gate = (repo.get("gates") or {}).get("priority") or {}
    above = priority_gate.get("blocks_above", 1)
    if (
        point in _holds(repo, "priority")
        and priority is not None
        and priority > above
    ):
        return "priority"
    risk = ((repo.get("gates") or {}).get("risk") or {}).get("labels") or []
    if point in _holds(repo, "risk") and labels.intersection(risk):
        return "risk"
    return None


def _has(labels: set[str], prefix: str) -> bool:
    return any(label.startswith(prefix) for label in labels)


def _one(labels: set[str], prefix: str) -> str | None:
    found = [label for label in labels if label.startswith(prefix)]
    return found[0] if found else None


def next_agent(
    labels: set[str],
    *,
    has_bead: bool,
    priority: int | None,
    repo: dict,
    pr: str,
    replacement: bool,
) -> dict:
    if not has_bead:
        return {"agent": "issue-import", "hold": None, "stop": None}
    if "phase-done/yes" in labels:
        return {"agent": None, "hold": None, "stop": "phase-done"}
    dup = _one(labels, "dup/")
    if dup and dup != "dup/none":
        return {"agent": None, "hold": None, "stop": "duplicate"}
    if not _has(labels, "dup/"):
        return {"agent": "issue-duplicate-judge", "hold": None, "stop": None}
    if not _has(labels, "phase/"):
        return {"agent": "issue-phase-match", "hold": None, "stop": None}
    if _has(labels, "phase/") and not _has(labels, "phase-done/") and _one(labels, "phase/") != "phase/none":
        return {"agent": "issue-phase-done", "hold": None, "stop": None}
    if not _has(labels, "overlap/"):
        return {"agent": "issue-overlap-judge", "hold": None, "stop": None}
    if not _has(labels, "prpair/"):
        return {"agent": "issue-prpair-judge", "hold": None, "stop": None}
    if replacement and _one(labels, "prpair/") not in (None, "prpair/none") and "credit/done" not in labels:
        return {"agent": "pr-author-credit", "hold": None, "stop": None}

    ready = "dup/none" in labels and ("phase/none" in labels or "phase-done/no" in labels)
    if not ready:
        return {"agent": None, "hold": None, "stop": "scan"}

    sequence = (
        ("kind/", "issue-kind-classify", None),
        ("area/", "issue-area-classify", None),
        ("size/", "issue-size-classify", None),
        ("priority/", "issue-priority-classify", None),
    )
    for prefix, agent, _point in sequence:
        if not _has(labels, prefix):
            return {"agent": agent, "hold": None, "stop": None}
    if "status/needs-triage" in labels:
        return {"agent": "issue-report-verify", "hold": None, "stop": None}
    if "status/unverified" in labels and not any(label in labels for label in GAP):
        return {"agent": "issue-gap-classify", "hold": None, "stop": None}
    if not _has(labels, "arch/"):
        return {"agent": "issue-arch-classify", "hold": None, "stop": None}
    if not _has(labels, "security/"):
        return {"agent": "issue-security-classify", "hold": None, "stop": None}
    if "status/planned" not in labels:
        hold = holding("plan", labels, priority, repo)
        return {"agent": None if hold else "issue-plan-write", "hold": hold, "stop": None}
    if "status/plan-accepted" not in labels and "status/plan-rejected" not in labels:
        hold = holding("quality_accept", labels, priority, repo)
        return {"agent": None if hold else "plan-accept", "hold": hold, "stop": None}
    if "status/plan-rejected" in labels:
        return {"agent": None, "hold": None, "stop": "plan-rejected"}
    if not pr:
        hold = holding("pr", labels, priority, repo)
        return {"agent": None, "hold": hold, "stop": None if hold else "open-pr"}
    return {"agent": None, "hold": None, "stop": "pr-open"}


def close_agent(labels: set[str], *, pr: str, commit: str, qa_all: bool, release_due: bool) -> dict:
    if not pr or not commit:
        return {"agent": "issue-landed-record", "hold": None, "stop": None}
    if qa_all and "status/close" not in labels:
        return {"agent": "issue-close-mark", "hold": None, "stop": None}
    if "status/close" in labels and release_due:
        return {"agent": "issue-release-close", "hold": None, "stop": None}
    return {"agent": None, "hold": None, "stop": "open"}


def next_patch(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default="")
    parser.add_argument("--labels", default="")
    parser.add_argument("--priority", type=int)
    parser.add_argument("--home", type=Path, default=Path.home() / ".atm-bd" / "config.toml")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bead", default="")
    parser.add_argument("--pr", default="")
    parser.add_argument("--commit", default="")
    parser.add_argument("--replacement", action="store_true")
    parser.add_argument("--close", action="store_true")
    parser.add_argument("--qa-all", action="store_true")
    parser.add_argument("--release-due", action="store_true")
    parser.add_argument("--version")
    args = parser.parse_args(argv)
    try:
        home = load_toml(args.home)
        if not args.repo.is_file():
            raise ValueError(f"missing {args.repo}")
        repo = load_toml(args.repo)
        labels = {item for item in args.labels.split(",") if item}
        labels.update(role_labels(args.login, home, repo))
        if args.version:
            payload = {"patch": next_patch(args.version)}
        elif args.close:
            payload = close_agent(
                labels, pr=args.pr, commit=args.commit, qa_all=args.qa_all, release_due=args.release_due
            )
        else:
            payload = next_agent(
                labels,
                has_bead=bool(args.bead),
                priority=args.priority,
                repo=repo,
                pr=args.pr,
                replacement=args.replacement,
            )
        payload["role_labels"] = [label for label in ("approver", "contributor") if label in labels]
    except ValueError as exc:
        print(json.dumps({"success": False, "data": None, "error": {"code": "CONFIG.INVALID", "message": str(exc)}}))
        return 2
    print(json.dumps({"success": True, "data": payload, "error": None}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
