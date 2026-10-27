"""Close fields carried by every poured dev, fix, sanity and QA bead, and the close vars built from one bead (#557).

A pour stamps `POURED` into the bead's metadata, so a validated open bead holds everything its close needs
that is known at pour time. `close_vars` turns that one bead into the `--vars` object for
`atm-task-close.py --role <role>`: the poured fields, the task ids (equal to the bead ids) and the two
host paths, projected onto the role's fields in `task-close-vars.j2`. It reads no other bead.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CONTRACT = Path(__file__).resolve().parents[2] / "atm-bd-orchestration" / "templates" / "task-close-vars.j2"
# An important or minor finding is fixed under the fix template; the lead stamps its close fields at dispatch.
ROLE_BY_STAGE = {"stage:dev": "dev", "stage:fix": "fix", "stage:finding": "fix", "stage:dev-sanity": "sanity", "stage:qa": "qa"}
# Stamped at pour on every open stage bead; bead_schema.CloseMetadata enforces them.
POURED = ("role", "phase", "sprint", "sprint_bead", "stack", "stack_bead", "branch", "worktree", "pr_target", "base",
          "checked_bead", "checked_title", "sanity_bead", "qa_bead", "phase_feature", "lint_command", "policy_path",
          "max_sanity_rounds")
# A QA bead's reviewers_round1 is planned on that bead (bead_schema.QaMetadata); a sanity close takes it from its qa_bead.
# Host-local: never stored on a bead.
HOST = ("primary_checkout", "worktree_path")


class CloseFieldsError(ValueError):
    def __init__(self, code: str, message: str, fix: str):
        super().__init__(message)
        self.code, self.fix = code, fix

    def as_json(self) -> dict:
        return {"code": self.code, "message": str(self), "fix": self.fix}


def contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8").split("---", 2)[1])


def stamp(*, role: str, phase: str, sprint: str, sprint_bead: str, stack: str, stack_bead: str, branch: str,
          worktree: str, pr_target: str, checked_bead: str, checked_title: str, sanity_bead: str, qa_bead: str,
          phase_feature: str, config: dict) -> dict:
    """The POURED metadata of one bead; `config` is the repository configuration (repo_config.load)."""
    return {"role": role, "phase": phase, "sprint": sprint, "sprint_bead": sprint_bead, "stack": stack,
            "stack_bead": stack_bead, "branch": branch, "worktree": worktree, "pr_target": pr_target, "base": pr_target,
            "checked_bead": checked_bead, "checked_title": checked_title, "sanity_bead": sanity_bead, "qa_bead": qa_bead,
            "phase_feature": phase_feature, "lint_command": config["lint_command"], "policy_path": config["policy_path"],
            "max_sanity_rounds": config["max_sanity_rounds"]}


def role_of(row: dict) -> str:
    stages = [label for label in row.get("labels") or [] if label in ROLE_BY_STAGE]
    if len(stages) != 1:
        raise CloseFieldsError("CLOSE_VARS.NOT_A_TASK_BEAD", f"{row.get('id')}: labels {row.get('labels')} name no single "
                               "stage:dev, stage:fix, stage:finding, stage:dev-sanity or stage:qa",
                               "Pass the id of a poured dev, fix, finding, sanity or QA bead.")
    return ROLE_BY_STAGE[stages[0]]


def close_vars(row: dict, repo: Path) -> tuple[str, dict, list[str]]:
    """(role, vars, fields the closing agent still supplies) for one bead; refuses a bead missing a poured field."""
    role = role_of(row)
    metadata = row.get("metadata") or {}
    missing = [name for name in POURED if metadata.get(name) in (None, "", [])]
    if missing:
        raise CloseFieldsError("CLOSE_VARS.NOT_POURED", f"{row['id']}: metadata lacks {', '.join(missing)}",
                               f"The pour or backfill did not stamp {row['id']}: ask the phase lead to run "
                               f"close_fields_backfill.py for its phase; never assemble these fields from other beads.")
    if metadata["role"] != role:
        raise CloseFieldsError("CLOSE_VARS.ROLE_MISMATCH", f"{row['id']}: metadata.role {metadata['role']!r} but its stage is {role}",
                               f"Correct metadata.role on {row['id']} to {role!r}.")
    worktree = Path(metadata["worktree"])
    available = {**{name: metadata[name] for name in POURED if name not in ("role", "worktree")},
                 "task_id": row["id"], "dev_task_id": metadata["checked_bead"], "sanity_task_id": metadata["sanity_bead"],
                 "qa_task_id": metadata["qa_bead"], "primary_checkout": str(repo),
                 "worktree_path": str(worktree if worktree.is_absolute() else (repo / worktree).resolve())}
    terms = contract()
    required = terms["required_variables_by_role"][role]
    values = {name: available[name] for name in required if name in available}
    remaining = [name for name in required if name not in values]
    return role, values, remaining


# The checked bead records these at its dev or fix close (atm-task-close.py); a QA assignment takes them from it.
RECORDED = ("commit", "branch", "pr_number")
# Also recorded there: the PR's actual base; a bead closed before it was recorded falls back to the poured base.
RECORDED_BASE = "pr_base"


def qa_assignment_vars(qa_row: dict, checked_row: dict, repo: Path) -> dict:
    """The `templates.qa` vars of one QA bead: its poured fields plus the PR its checked bead recorded.

    The PR, its base, commit and branch come from the checked bead, never from hand-assembled vars, so a QA assignment
    cannot render without its PR (#2214). A value the QA bead also holds must agree with the checked bead.
    """
    role, values, _ = close_vars(qa_row, repo)
    if role != "qa":
        raise CloseFieldsError("ASSIGN_VARS.NOT_QA", f"{qa_row['id']} is a {role} bead",
                               "Pass the QA bead; only QA assignments are built here.")
    metadata = qa_row.get("metadata") or {}
    checked = checked_row.get("metadata") or {}
    missing = [name for name in RECORDED if checked.get(name) in (None, "")]
    if missing:
        raise CloseFieldsError("ASSIGN_VARS.NOT_RECORDED", f"{checked_row['id']}: metadata lacks {', '.join(missing)}",
                               f"{checked_row['id']} has no recorded close: finish its dev or fix close "
                               f"(atm-task-close.py records commit, branch and pr_number), then rebuild these vars.")
    conflicts = [f"{name} {metadata[name]!r} != {checked[name]!r}" for name in RECORDED
                 if metadata.get(name) not in (None, "") and str(metadata[name]) != str(checked[name])]
    if conflicts:
        raise CloseFieldsError("ASSIGN_VARS.CONFLICT", f"{qa_row['id']} disagrees with {checked_row['id']}: {'; '.join(conflicts)}",
                               f"Correct the stale value on {qa_row['id']} to the checked bead's recorded close.")
    for name in ("layer", "round", "reviewers_round1"):
        if metadata.get(name) in (None, "", []):
            raise CloseFieldsError("ASSIGN_VARS.NOT_PLANNED", f"{qa_row['id']}: metadata lacks {name}",
                                   f"Set {name} on {qa_row['id']} (layer when its PR is linked, round and reviewers at pour).")
    is_fix = checked.get("role") == "fix" or "stage:fix" in (checked_row.get("labels") or [])
    return {"task_id": qa_row["id"], "qa_task_id": qa_row["id"], "checked_bead": values["checked_bead"],
            "dev_task_id": values["checked_bead"], "sanity_task_id": metadata.get("sanity_bead") or "",
            "phase": metadata["phase"], "phase_feature": metadata["phase_feature"], "sprint": metadata["sprint"],
            "sprint_bead": metadata["sprint_bead"], "stack": metadata["stack"], "layer": metadata["layer"],
            "round": metadata["round"], "base": str(checked.get(RECORDED_BASE) or metadata["base"]), "worktree_path": values["worktree_path"],
            "policy_path": metadata["policy_path"], "reviewers_round1": metadata["reviewers_round1"],
            "commit": str(checked["commit"]), "branch": str(checked["branch"]), "pr_number": str(checked["pr_number"]),
            "carry_forward": checked_row["id"] if is_fix else ""}


# The dev/fix fields the sanity close reads back from close_context: sanity-close-vars build() and
# write_stack_input(), then atm-task-close.py --role sanity and the templates it renders and sends
# (dev-sanity-complete, sanity-fail, qa-template). Every other field is overwritten there or never read.
SANITY_CLOSE_CONTEXT = frozenset((
    "base", "carry_forward", "checked_title", "evidence", "layer", "layer_prs", "max_sanity_rounds", "outcome",
    "phase", "phase_feature", "policy_path", "pr_number", "pr_url", "primary_checkout", "qa_bead", "qa_task_id",
    "reviewers_round1", "round", "sprint_bead", "stack", "stack_bead"))
SANITY_CLOSE_HOOK_MODULE = "sanity_task_close_hook.py"
# A not-reproducible close records its evidence in the checked bead's close reason (atm-task-close.py finish_dev).
NOT_REPRODUCIBLE_REASON = "not reproducible: "


def sanity_close_mode(rows, phase, member):
    """`daemon` when `atm hook list --phase <phase> --json` shows an active task.close registration of the sanity
    close hook that enables `member` (SANITY-CLOSE-HOOK.md); otherwise `legacy`."""
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        custom = row.get("custom")
        agents = custom.get("sanity_agents") if isinstance(custom, dict) else None
        if (row.get("phase") == phase and row.get("hook") == "task.close" and row.get("active") is True
                and Path(str(row.get("module_path") or "")).name == SANITY_CLOSE_HOOK_MODULE
                and isinstance(agents, list) and member in agents):
            return "daemon"
    return "legacy"


def sanity_dispatch_vars(context: dict, *, lead: str, beads_dir: str, close_mode: str) -> dict:
    """The `dev-sanity-template.xml.j2` vars from one dev or fix close's values: those values, the close context the
    sanity close reads back, the beads directory and the close mode. Both the dev close hook and a re-dispatch
    (`sanity_assignment_vars`) build here."""
    close_context = {name: context[name] for name in SANITY_CLOSE_CONTEXT if name in context}
    close_context.update(phase_lead=lead, budget=context.get("budget", "full"))
    return {**context, "close_context": close_context, "beads_dir": beads_dir, "sanity_close_mode": close_mode}


def sanity_assignment_vars(sanity_row: dict, checked_row: dict, qa_row: dict, repo: Path, *, lead: str, beads_dir: str,
                           close_mode: str) -> dict:
    """The sanity assignment of a closed dev or fix bead, rebuilt from the beads as the dev close hook dispatches it
    (re-dispatch after a refusal or a lost assignment): the checked bead's close vars and the commit, branch and PR
    it recorded at close; the poured phase_feature, policy_path and stack; and the layer and reviewers its QA bead
    plans, which the sanity close's QA handoff reads back. An open checked bead or one with no recorded close is
    refused. The base is the PR base the checked bead recorded, as for QA (`qa_assignment_vars`)."""
    if role_of(sanity_row) != "sanity":
        raise CloseFieldsError("ASSIGN_VARS.NOT_SANITY", f"{sanity_row['id']} is not a sanity bead",
                               "Pass the sanity bead; only sanity assignments are built here.")
    sanity = sanity_row.get("metadata") or {}
    named = sanity.get("dev_bead") or sanity.get("checked_bead")
    if named != checked_row["id"]:
        raise CloseFieldsError("ASSIGN_VARS.CONFLICT", f"{sanity_row['id']} checks {named!r}, not {checked_row['id']}",
                               f"Pass the checked bead {sanity_row['id']} names in metadata.dev_bead.")
    role, values, _ = close_vars(checked_row, repo)
    if role not in ("dev", "fix"):
        raise CloseFieldsError("ASSIGN_VARS.NOT_CHECKED", f"{checked_row['id']} is a {role} bead",
                               "A sanity check checks a dev, fix or finding bead.")
    if sanity_row["id"] != values["sanity_task_id"]:
        raise CloseFieldsError("ASSIGN_VARS.CONFLICT", f"{checked_row['id']} names sanity {values['sanity_task_id']!r}, not {sanity_row['id']}",
                               f"Correct metadata.sanity_bead on {checked_row['id']} to the sanity bead that checks it.")
    if qa_row["id"] != values["qa_task_id"]:
        raise CloseFieldsError("ASSIGN_VARS.CONFLICT", f"{checked_row['id']} names QA {values['qa_task_id']!r}, not {qa_row['id']}",
                               f"Pass the QA bead {checked_row['id']} names in metadata.qa_bead.")
    if checked_row.get("status") != "closed":
        raise CloseFieldsError("ASSIGN_VARS.NOT_CLOSED", f"{checked_row['id']} is {checked_row.get('status')}",
                               f"The dev close of {checked_row['id']} dispatches its sanity check; run atm-task-close.py "
                               "for it instead.")
    reason = str(checked_row.get("close_reason") or "")
    outcome = "not_reproducible" if reason.startswith(NOT_REPRODUCIBLE_REASON) else "fixed"
    checked = checked_row.get("metadata") or {}
    recorded = ("commit", "branch") if outcome == "not_reproducible" else (*RECORDED, "pr_url")
    missing = [name for name in recorded if checked.get(name) in (None, "")]
    if missing:
        raise CloseFieldsError("ASSIGN_VARS.NOT_RECORDED", f"{checked_row['id']}: metadata lacks {', '.join(missing)}",
                               f"{checked_row['id']} has no recorded close: record {', '.join(missing)} on it from its "
                               "dev or fix close (atm-task-close.py records them), then rebuild these vars.")
    qa = qa_row.get("metadata") or {}
    planned = {"layer": qa.get("layer") if qa.get("layer") not in (None, "") else checked.get("layer"),
               "reviewers_round1": qa.get("reviewers_round1")}
    unplanned = [name for name, value in planned.items() if value in (None, "", [])]
    if unplanned:
        raise CloseFieldsError("ASSIGN_VARS.NOT_PLANNED", f"{qa_row['id']}: metadata lacks {', '.join(unplanned)}",
                               f"Set {', '.join(unplanned)} on {qa_row['id']} (layer when its PR is linked, reviewers at pour).")
    context = {**values, "phase_feature": checked["phase_feature"], "policy_path": checked["policy_path"],
               "stack": checked["stack"], **planned,
               **({"round": checked["round"]} if checked.get("round") not in (None, "") else {}),
               "commit": str(checked["commit"]), "branch": str(checked["branch"]),
               "pr_number": str(checked.get("pr_number") or ""), "pr_url": str(checked.get("pr_url") or ""),
               "base": str(checked.get(RECORDED_BASE) or values["base"]), "outcome": outcome,
               "evidence": reason.removeprefix(NOT_REPRODUCIBLE_REASON) if outcome == "not_reproducible" else ""}
    return sanity_dispatch_vars(context, lead=lead, beads_dir=beads_dir, close_mode=close_mode)
