#!/usr/bin/env python3
"""Print the close vars of one poured dev, fix, sanity or QA bead (#557).

    close-vars.py <bead-id> --out <vars.json> [--repo <beads repository root>]
    close-vars.py <qa-bead-id> --qa-assignment --out <vars.json> [--repo <beads repository root>]
    close-vars.py <sanity-bead-id> --sanity-assignment --out <vars.json> [--repo <beads repository root>]

Every validated open task bead carries its close fields (close_fields.POURED), so the vars come from that one
bead: the poured fields, the task ids (equal to the bead ids) and the host paths. A sanity close adds its round
(the task's `started` events) and the reviewers of its QA bead; a QA close adds its round. Beads are read from the
bd-cache (pending journal writes replayed on top); the close hooks write through it, so it holds their recorded
fields. When a field the vars need is missing there, the beads are re-read from bd once (`bd list --id`) and the
vars rebuilt; `bd show` is used when the cache cannot be opened. Each fallback is named in `read_fallback`.

It writes `--out` and prints JSON: role, the fields the closing agent still supplies (`remaining`) and the
manual close commands. A bead missing a poured field is refused with the fix; never assemble its fields from
other beads.

`--qa-assignment` instead writes the `templates.qa` vars of a QA bead: its poured fields plus the commit,
branch and PR its checked bead recorded at close (close_fields.qa_assignment_vars), and prints the
`atm task assign` command. A checked bead with no recorded PR is refused, never sent with an empty PR.

`--sanity-assignment` writes the `templates.sanity` vars of a sanity bead whose dev or fix bead has closed, as that
close would have dispatched them (close_fields.sanity_assignment_vars, which also reads the checked bead's QA bead
for its layer and reviewers): for a sanity task re-issued after a refusal or a lost assignment. The phase lead comes from `.atm-bd/phase-<x>.toml`, the beads directory from BEADS_DIR or
`bd where --json`, and the close mode from `atm hook list --phase <x> --json`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "atm-beads" / "scripts"))
import bd_cache  # noqa: E402
import close_fields  # noqa: E402

ATM_TIMEOUT_S = 10
BD_SHOW_TIMEOUT_S = 30


# Refusals that a cached row lagging a direct `bd update` could cause; a fresh read from bd settles them.
MISSING = ("CLOSE_VARS.NOT_POURED", "ASSIGN_VARS.NOT_RECORDED", "ASSIGN_VARS.NOT_PLANNED")


def read(repo: Path, bead: str, fallback: list[str], cache_factory=bd_cache.BdCache, *, fresh: bool = False) -> dict:
    """The bead from the bd-cache with pending journal writes replayed on top; `fresh` reads bd first.

    A failed fresh read falls back to the cached row, and a cache that cannot be opened to `bd show`.
    """
    try:
        cache = cache_factory(repo)
    except (bd_cache.CacheError, OSError) as error:
        fallback.append(f"bd-cache: {error}")
        return show(repo, bead)
    if fresh:
        try:
            row = cache.bd_rows([bead]).get(bead)
        except (bd_cache.CacheError, OSError) as error:
            fallback.append(f"bd list --id {bead} failed, using the cached row: {error}")
        else:
            if row is None:
                raise close_fields.CloseFieldsError("CLOSE_VARS.READ_FAILED", f"{bead}: not found in bd",
                                                    "Check the bead id and that bd works here.")
            cache.store(row, force=True)
            return cache.view(row)
    try:
        return cache.get(bead)
    except (bd_cache.CacheError, OSError) as error:
        fallback.append(f"bd-cache: {error}")
        return show(repo, bead)


def show(repo: Path, bead: str) -> dict:
    try:
        shown = subprocess.run(["bd", "show", bead, "--json"], cwd=repo, capture_output=True, text=True,
                               timeout=BD_SHOW_TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.READ_FAILED", f"{bead}: bd show failed: {error}",
                                            "Check that bd and its dolt server answer here (`bd version`), then rerun.") from error
    if shown.returncode != 0:
        raise close_fields.CloseFieldsError("CLOSE_VARS.READ_FAILED", f"{bead}: bd show exited {shown.returncode}: "
                                            f"{(shown.stderr or shown.stdout).strip()[-300:]}", "Check the bead id and that bd works here.")
    try:
        rows = json.loads(shown.stdout)
        return rows[0] if isinstance(rows, list) else rows
    except (ValueError, IndexError) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.READ_FAILED", f"{bead}: bd show printed no bead: {error}",
                                            "Check the bead id and the bd version.") from error


def started_runs(task: str) -> int:
    try:
        events = subprocess.run(["atm", "task", "events", task, "--all", "--json"], capture_output=True, text=True,
                                timeout=ATM_TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.EVENTS_FAILED", f"atm task events {task} failed: {error}",
                                            "Check that the ATM daemon answers (`atm task list`), then rerun.") from error
    if events.returncode != 0:
        raise close_fields.CloseFieldsError("CLOSE_VARS.EVENTS_FAILED", f"atm task events {task} exited {events.returncode}: "
                                            f"{(events.stderr or events.stdout).strip()[-300:]}", "Check that atm can read this task.")
    try:
        count = sum(1 for event in json.loads(events.stdout)["events"] if event.get("event") == "started")
    except (ValueError, KeyError, TypeError) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.EVENTS_FAILED", f"atm task events {task} printed no events: {error}",
                                            "Check the atm version.") from error
    if count < 1:
        raise close_fields.CloseFieldsError("CLOSE_VARS.NOT_STARTED", f"{task} has no started event",
                                            f"Run `atm task start {task} \"<plan>\"` first.")
    return count


def build(repo: Path, bead: str, *, runs=started_runs) -> dict:
    return cached_then_fresh(lambda fresh, fallback: _build(repo, bead, runs, fresh, fallback))


def _build(repo, bead, runs, fresh, fallback):
    row = read(repo, bead, fallback, fresh=fresh)
    role, values, remaining = close_fields.close_vars(row, repo)
    metadata = row.get("metadata") or {}
    derived = {}
    if role == "qa":
        derived["round"] = metadata.get("round")
    if role == "sanity":
        derived["round"] = runs(bead)
        derived["reviewers_round1"] = (read(repo, metadata["qa_bead"], fallback, fresh=fresh).get("metadata") or {}).get("reviewers_round1")
    for name, value in derived.items():
        if name in remaining and value not in (None, "", []):
            values[name] = value
            remaining.remove(name)
    return {"bead": bead, "role": role, "vars": values, "remaining": remaining, "read_fallback": fallback}


def build_qa_assignment(repo: Path, bead: str) -> dict:
    return cached_then_fresh(lambda fresh, fallback: _build_qa_assignment(repo, bead, fresh, fallback))


def _build_qa_assignment(repo, bead, fresh, fallback):
    row = read(repo, bead, fallback, fresh=fresh)
    checked = (row.get("metadata") or {}).get("checked_bead")
    if not checked:
        raise close_fields.CloseFieldsError("CLOSE_VARS.NOT_POURED", f"{bead}: metadata lacks checked_bead",
                                            "Ask the phase lead to run close_fields_backfill.py for its phase.")
    values = close_fields.qa_assignment_vars(row, read(repo, checked, fallback, fresh=fresh), repo)
    return {"bead": bead, "role": "qa-assignment", "vars": values, "remaining": [], "read_fallback": fallback}


def build_sanity_assignment(repo: Path, bead: str, *, host=None) -> dict:
    return cached_then_fresh(lambda fresh, fallback: _build_sanity_assignment(repo, bead, host or sanity_host, fresh, fallback))


def _build_sanity_assignment(repo, bead, host, fresh, fallback):
    row = read(repo, bead, fallback, fresh=fresh)
    metadata = row.get("metadata") or {}
    checked = metadata.get("dev_bead") or metadata.get("checked_bead")
    if not checked:
        raise close_fields.CloseFieldsError("CLOSE_VARS.NOT_POURED", f"{bead}: metadata lacks dev_bead",
                                            "Ask the phase lead to run close_fields_backfill.py for its phase.")
    phase = str(metadata.get("phase") or "")
    lead, member, beads_dir, rows = host(repo, phase)
    checked_row = read(repo, checked, fallback, fresh=fresh)
    qa = (checked_row.get("metadata") or {}).get("qa_bead") or metadata.get("qa_bead")
    if not qa:
        raise close_fields.CloseFieldsError("CLOSE_VARS.NOT_POURED", f"{checked}: metadata lacks qa_bead",
                                            "Ask the phase lead to run close_fields_backfill.py for its phase.")
    values = close_fields.sanity_assignment_vars(row, checked_row, read(repo, qa, fallback, fresh=fresh), repo, lead=lead,
                                                 beads_dir=beads_dir,
                                                 close_mode=close_fields.sanity_close_mode(rows, phase, member))
    return {"bead": bead, "role": "sanity-assignment", "vars": values, "remaining": [], "read_fallback": fallback}


def _json_command(argv: list[str], repo: Path, fix: str):
    try:
        done = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=BD_SHOW_TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.HOST_FAILED", f"{' '.join(argv)} failed: {error}", fix) from error
    if done.returncode != 0:
        raise close_fields.CloseFieldsError("CLOSE_VARS.HOST_FAILED", f"{' '.join(argv)} exited {done.returncode}: "
                                            f"{(done.stderr or done.stdout).strip()[-300:]}", fix)
    try:
        return json.loads(done.stdout)
    except ValueError as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.HOST_FAILED", f"{' '.join(argv)} printed no JSON: {error}", fix) from error


def sanity_host(repo: Path, phase: str) -> tuple[str, str, str, list]:
    """(phase lead, dev-sanity member, beads directory, `atm hook list` rows): what the dev close hook reads."""
    import repo_config  # noqa: E402
    import sprint_index_common  # noqa: E402
    try:
        lead = sprint_index_common.load_phase_config(repo, phase)["lead"]
        member = repo_config.load(repo)["dev_sanity_member"]
    except (RuntimeError, repo_config.ConfigError, KeyError) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.CONFIG", f"cannot name the phase lead or sanity member: {error}",
                                            f"Fix lead in .atm-bd/phase-{phase}.toml or dev_sanity_member in "
                                            ".claude/project/atm-bd-orchestration.yaml.") from error
    beads_dir = os.environ.get("BEADS_DIR") or ""
    if not beads_dir:
        location = _json_command(["bd", "where", "--json"], repo, "Set BEADS_DIR or repair `bd where --json`.")
        beads_dir = location.get("path") if isinstance(location, dict) else None
        if not isinstance(beads_dir, str) or not Path(beads_dir).is_absolute():
            raise close_fields.CloseFieldsError("CLOSE_VARS.HOST_FAILED", f"bd where --json path {beads_dir!r}",
                                                "Set BEADS_DIR or repair `bd where --json` to return an absolute beads path.")
    rows = _json_command(["atm", "hook", "list", "--phase", phase, "--json"], repo,
                         "Check that the ATM daemon answers (`atm hook list`), then rerun.") if phase else []
    return lead, member, beads_dir, rows


def cached_then_fresh(attempt) -> dict:
    """Build from cached rows; a refusal for a missing field is retried once on rows read fresh from bd."""
    fallback: list[str] = []
    try:
        return attempt(False, fallback)
    except close_fields.CloseFieldsError as error:
        if error.code not in MISSING:
            raise
        fallback.append(f"{error.code} on cached rows ({error}); re-read from bd")
        return attempt(True, fallback)


def assign_command(repo: Path, values: dict, out: str, purpose: str = "qa") -> list[str]:
    import repo_config  # noqa: E402
    import sprint_index_common  # noqa: E402
    member_key = "dev_sanity_member" if purpose == "sanity" else "qa_member"
    task = values["sanity_task_id"] if purpose == "sanity" else values["task_id"]
    try:
        template = sprint_index_common.load_phase_config(repo, values["phase"])["templates"][purpose]
        member = repo_config.load(repo)[member_key]
    except (RuntimeError, repo_config.ConfigError, KeyError) as error:
        raise close_fields.CloseFieldsError("CLOSE_VARS.CONFIG", f"cannot name the {purpose} template or member: {error}",
                                            f"Fix .atm-bd/phase-{values['phase']}.toml templates.{purpose} or {member_key} in "
                                            ".claude/project/atm-bd-orchestration.yaml.") from error
    return [f"atm task assign {member} --task-id {task} --template {template} --vars {out}"]


def commands(role: str, bead: str, out: str) -> list[str]:
    close = ".claude/skills/atm-bd-orchestration/scripts/atm-task-close.py"
    if role in ("dev", "fix"):
        return [f"write the remaining fields to <result.json>",
                f"{close} --role {role} --vars {out} --result <result.json>"]
    return [f"add the remaining fields to {out}", f"{close} --role {role} --vars {out}"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="close-vars.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bead")
    parser.add_argument("--out", required=True)
    parser.add_argument("--repo", default=".")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--qa-assignment", action="store_true", help="write the templates.qa vars of a QA bead")
    mode.add_argument("--sanity-assignment", action="store_true",
                      help="write the templates.sanity vars of a sanity bead whose checked bead has closed")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        if args.qa_assignment:
            result = build_qa_assignment(repo, args.bead)
            steps = assign_command(repo, result["vars"], args.out)
        elif args.sanity_assignment:
            result = build_sanity_assignment(repo, args.bead)
            steps = assign_command(repo, result["vars"], args.out, "sanity")
        else:
            result = build(repo, args.bead)
            steps = commands(result["role"], args.bead, args.out)
    except close_fields.CloseFieldsError as error:
        print(json.dumps({"ok": False, "error": error.as_json()}, indent=2))
        return 2
    for message in result["read_fallback"]:
        print(f"close-vars: {message}", file=sys.stderr)
    Path(args.out).write_text(json.dumps(result["vars"], indent=2) + "\n")
    print(json.dumps({"ok": True, "bead": result["bead"], "role": result["role"], "vars_path": args.out,
                      "remaining": result["remaining"], "read_fallback": result["read_fallback"],
                      "next": steps}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
