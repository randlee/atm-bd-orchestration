#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.20.0"]
# ///
# pyright: strict
"""Gather live lite workflow state and execute a pure transition plan."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

from atm_bd_types import CloseVars, Error, ErrorDetail, ErrorKind, PrRef, Profile, StackGateResult, Transition
from result import Err, Ok, Result
from stack_gate import GitStackGate
from stack_gate_types import StackGate
from stack_top import is_json_object, select_stack_top


class HookModule(Protocol):
    Observed: Any

    def plan(self, transition: Transition, vars: CloseVars, observed: object) -> object: ...


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
PrFinder = Callable[..., Result[PrRef]]
GateFactory = Callable[[Path], StackGate]


def _load_hook(path: Path) -> HookModule:
    spec = importlib.util.spec_from_file_location("atm_bd_lite_task_hook", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load lite hook from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return cast(HookModule, module)


def _run(argv: Sequence[str], cwd: Path, runner: ProcessRunner) -> Result[str]:
    try:
        completed = runner(list(argv), cwd=cwd, capture_output=True, text=True, check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as failure:
        return Err(Error(ErrorKind.UNREACHABLE, f"{' '.join(argv)}: {failure}",
                         f"Restore the command and rerun the same hook invocation."))
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        return Err(Error(ErrorKind.COMMAND_FAILED, f"{' '.join(argv)}: {detail}",
                         f"Repair this step and rerun the same hook invocation.",
                         ErrorDetail.CommandFailed(list(argv), completed.returncode, detail)))
    return Ok(completed.stdout)


def _json(argv: Sequence[str], cwd: Path, runner: ProcessRunner) -> Result[object]:
    result = _run(argv, cwd, runner)
    if isinstance(result, Err):
        return result
    try:
        return Ok(json.loads(result.value))
    except json.JSONDecodeError as failure:
        return Err(Error(ErrorKind.PARSE_FAILED, f"{' '.join(argv)}: {failure}",
                         "Repair the command's JSON output and rerun the hook."))


def _one_row(value: object, command: str) -> Result[dict[str, object]]:
    if isinstance(value, list):
        rows = cast(list[object], value)
        if len(rows) == 1:
            value = rows[0]
    if not isinstance(value, dict):
        return Err(Error(ErrorKind.PARSE_FAILED, f"{command}: expected one JSON object",
                         "Repair the bead command output and rerun the hook."))
    return Ok(cast(dict[str, object], value))


def _value(values: Mapping[str, object], *names: str) -> str | None:
    for name in names:
        found = values.get(name)
        if isinstance(found, str) and found.strip():
            return found
    return None


def close_vars_from_mapping(values: Mapping[str, object]) -> Result[CloseVars]:
    """Validate the optional typed close fields carried alongside lite runner inputs."""
    sanity_bead = values.get("sanity_bead")
    max_sanity_rounds = values.get("max_sanity_rounds")
    if sanity_bead is not None and not isinstance(sanity_bead, str):
        return Err(Error(ErrorKind.CONFIG_INVALID, "sanity_bead must be a string or null",
                         "Correct sanity_bead in the supplied close vars and retry."))
    if max_sanity_rounds is not None and (
        isinstance(max_sanity_rounds, bool)
        or not isinstance(max_sanity_rounds, int)
        or not 0 <= max_sanity_rounds <= 0xFFFF_FFFF
    ):
        return Err(Error(ErrorKind.CONFIG_INVALID, "max_sanity_rounds must be a u32 or null",
                         "Correct max_sanity_rounds in the supplied close vars and retry."))
    try:
        return Ok(CloseVars(sanity_bead, max_sanity_rounds))
    except (TypeError, ValueError) as failure:
        return Err(Error(ErrorKind.CONFIG_INVALID, f"invalid close vars: {failure}",
                         "Correct the supplied close vars and retry."))


def collect_observed(
    values: Mapping[str, object],
    result_values: Mapping[str, object],
    transition: Transition,
    repo: Path,
    hook_path: Path,
    *,
    runner: ProcessRunner = subprocess.run,
    pr_finder: PrFinder | None = None,
    gate_factory: GateFactory = GitStackGate,
) -> Result[object]:
    """Read current bead/task/stack/PR state and evaluate the pushed stack gate."""
    from pr_lookup import find_pr_by_head

    task_id = _value(values, "task_id", "dev_task_id", "qa_task_id")
    bead_id = _value(values, "checked_bead", "task_id", "dev_task_id", "qa_task_id")
    stack_bead = _value(values, "stack_bead")
    branch = _value(values, "branch")
    commit = _value(values, "commit")
    pr_target = _value(values, "pr_target", "base")
    if not all((task_id, bead_id, stack_bead, branch, commit, pr_target)):
        missing = [name for name, item in (("task_id", task_id), ("checked_bead", bead_id),
                   ("stack_bead", stack_bead), ("branch", branch), ("commit", commit),
                   ("pr_target", pr_target)) if not item]
        return Err(Error(ErrorKind.CONFIG_MISSING, f"close vars lack {', '.join(missing)}",
                         "Supply the shared lite close vars for this task and retry."))

    bead_result = _json(["bd", "show", cast(str, bead_id), "--json"], repo, runner)
    if isinstance(bead_result, Err):
        return bead_result
    bead = _one_row(bead_result.value, f"bd show {bead_id}")
    if isinstance(bead, Err):
        return bead

    stack_result = _json(["bd", "show", cast(str, stack_bead), "--json"], repo, runner)
    if isinstance(stack_result, Err):
        return stack_result
    stack = _one_row(stack_result.value, f"bd show {stack_bead}")
    if isinstance(stack, Err):
        return stack
    if not is_json_object(stack.value):
        return Err(Error(ErrorKind.PARSE_FAILED, "stack bead has malformed JSON", "Repair the stack bead and retry."))

    def resolve_head(name: str) -> object:
        resolved = _run(["git", "rev-parse", "--verify", f"refs/remotes/origin/{name}"], repo, runner)
        return resolved.value.strip() if isinstance(resolved, Ok) else ""

    try:
        stack_top, _top_sha = select_stack_top(stack.value, pr_target, resolve_head)
    except ValueError as failure:
        return Err(Error(ErrorKind.CONFIG_INVALID, str(failure), "Repair stack metadata and rerun the hook."))

    lookup = pr_finder or find_pr_by_head
    pr = lookup(cast(str, branch), repo, expected_head=cast(str, commit), runner=runner)
    if isinstance(pr, Err):
        return pr
    gate = gate_factory(repo).check(pr.value.base, cast(str, branch), pr.value.head_sha, stack_top)
    if isinstance(gate, Err):
        return gate
    gate_stacked = isinstance(gate.value, StackGateResult.Stacked)

    events_result = _json(["atm", "task", "events", cast(str, task_id), "--json"], repo, runner)
    if isinstance(events_result, Err):
        return events_result
    event_object = events_result.value
    if isinstance(event_object, dict):
        event_data = cast(dict[str, object], event_object)
        events_value: object = event_data.get("events", [])
    else:
        events_value = event_object
    if not isinstance(events_value, list):
        return Err(Error(ErrorKind.PARSE_FAILED, "atm task events: expected events array",
                         "Repair the task event output and retry."))
    event_rows = cast(list[object], events_value)
    task_state = ""
    assigned_by: str | None = None
    for event in reversed(event_rows):
        if not isinstance(event, dict):
            continue
        event_data = cast(dict[str, object], event)
        if not task_state and isinstance(event_data.get("to_state"), str):
            task_state = cast(str, event_data["to_state"])
        actor_value = event_data.get("actor")
        actor = cast(dict[str, object], actor_value) if isinstance(actor_value, dict) else {}
        if event_data.get("to_state") == "assigned" and isinstance(actor.get("member"), str):
            assigned_by = cast(str, actor["member"])
            break
    task_closed = task_state in ("complete", "completed")

    tasks_result = _json(["atm", "task", "list", "--all", "--json"], repo, runner)
    if isinstance(tasks_result, Err):
        return tasks_result
    tasks_value: object = tasks_result.value
    if not isinstance(tasks_value, list):
        return Err(Error(ErrorKind.PARSE_FAILED, "atm task list: expected array",
                         "Repair the task list output and retry."))
    tasks = cast(list[object], tasks_value)
    qa_id = _value(values, "qa_task_id", "qa_bead") or f"{bead_id}.group-qa"
    qa_assigned = any(
        isinstance(item, dict) and cast(dict[str, object], item).get("task_id") == qa_id
        for item in tasks
    )
    qa_closed = str(bead.value.get("status", "")).lower() == "closed" if transition in (Transition.QA_PASS, Transition.QA_FAIL) else False
    metadata_value = stack.value.get("metadata")
    metadata = cast(dict[str, object], metadata_value) if isinstance(metadata_value, dict) else {}
    layers = metadata.get("layers", [])
    layer_rows = cast(list[object], layers) if isinstance(layers, list) else []
    layer_linked = any(
        isinstance(item, dict) and cast(dict[str, object], item).get("branch") == branch
        for item in layer_rows
    )
    status = str(bead.value.get("status", "")).lower()
    refused = transition is Transition.REFUSED and status == "open"
    lead = _value(values, "lead", "phase_lead", "team_lead_member") or assigned_by
    if not lead:
        return Err(Error(ErrorKind.CONFIG_MISSING, "task events do not identify the assigning lead",
                         "Supply lead in the shared close vars or repair the task assignment event."))
    hook = _load_hook(hook_path)
    observed = hook.Observed(
        task_id=task_id, bead_id=bead_id, lead=lead,
        reason=str(result_values.get("reason_md", result_values.get("reason", ""))),
        findings_file=str(result_values.get("findings_file", values.get("result_file", ""))),
        pr_number=pr.value.number, pr_base=pr.value.base, pr_head=cast(str, branch),
        pr_sha=pr.value.head_sha, stack_top=stack_top, gate_stacked=gate_stacked,
        bead_closed=status == "closed", layer_linked=layer_linked, qa_assigned=qa_assigned,
        task_closed=task_closed, qa_closed=qa_closed,
        findings_poured=False, notified=False, refused=refused,
    )
    return Ok(observed)


def run_transition(
    phase_file: Path,
    transition: Transition,
    values: Mapping[str, object],
    result_values: Mapping[str, object],
    repo: Path,
    hook_path: Path,
    *,
    runner: ProcessRunner = subprocess.run,
    pr_finder: PrFinder | None = None,
    gate_factory: GateFactory = GitStackGate,
) -> Result[None]:
    """Gate first, then repeatedly observe, plan and execute one unsatisfied step."""
    from phase_profile import require_profile

    profile = require_profile(phase_file, Profile.LITE)
    if isinstance(profile, Err):
        return profile
    close_vars = close_vars_from_mapping(values)
    if isinstance(close_vars, Err):
        return close_vars
    hook = _load_hook(hook_path)
    while True:
        observed = collect_observed(values, result_values, transition, repo, hook_path, runner=runner,
                                   pr_finder=pr_finder, gate_factory=gate_factory)
        if isinstance(observed, Err):
            return observed
        planned = hook.plan(transition, close_vars.value, observed.value)
        if hasattr(planned, "error"):
            return Err(cast(Any, planned).error)
        commands = cast(Any, planned).value
        next_command = next((command for command in commands
                             if not command.idempotent_when(cast(Any, observed.value))), None)
        if next_command is None:
            return Ok(None)
        result = _run(next_command.argv, repo, runner)
        if isinstance(result, Err):
            return result


def _dict(path: Path) -> Result[dict[str, object]]:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as failure:
        return Err(Error(ErrorKind.CONFIG_INVALID, f"{path}: {failure}", "Repair the JSON file and retry."))
    if not isinstance(decoded, dict):
        return Err(Error(ErrorKind.CONFIG_INVALID, f"{path}: expected a JSON object", "Supply a JSON object."))
    return Ok(cast(dict[str, object], decoded))


def _transition(role: str, result_values: Mapping[str, object]) -> Result[Transition]:
    outcome = str(result_values.get("verdict", result_values.get("outcome", ""))).upper()
    if outcome == "REFUSED":
        return Ok(Transition.REFUSED)
    match role, outcome:
        case "dev", _:
            return Ok(Transition.DEV_CLOSE)
        case "fix", _:
            return Ok(Transition.FIX_CLOSE)
        case "qa", "PASS":
            return Ok(Transition.QA_PASS)
        case "qa", "FAIL":
            return Ok(Transition.QA_FAIL)
        case _:
            return Err(Error(ErrorKind.CONFIG_INVALID, f"invalid role/outcome {role}/{outcome}",
                             "Use dev, fix, or QA with verdict PASS or FAIL."))


def _lite_hook(repo: Path) -> Path | None:
    for path in (repo / ".atm-bd/skills/atm-bd-lite/scripts/atm-bd-task-hook.py",
                 repo / ".claude/skills/atm-bd-lite/scripts/atm-bd-task-hook.py",
                 repo / ".codex/skills/atm-bd-lite/scripts/atm-bd-task-hook.py",
                 repo / "plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py"):
        if path.is_file():
            return path
    return None


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="hook_runner.py")
    parser.add_argument("--role", choices=("dev", "fix", "qa"), required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--vars", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = Path.cwd()
    phase_file = repo / ".atm-bd" / f"phase-{args.phase}.toml"
    from phase_profile import require_profile

    profile = require_profile(phase_file, Profile.LITE)
    if isinstance(profile, Err):
        print(json.dumps({"kind": profile.error.kind.name.lower(), "message": profile.error.message,
                          "fix": profile.error.fix}), file=sys.stderr)
        return 3
    values = _dict(args.vars)
    result_values = _dict(args.result)
    if isinstance(values, Err) or isinstance(result_values, Err):
        failure = values.error if isinstance(values, Err) else cast(Err, result_values).error
        print(json.dumps({"kind": failure.kind.name.lower(), "message": failure.message, "fix": failure.fix}),
              file=sys.stderr)
        return 3
    transition = _transition(args.role, result_values.value)
    if isinstance(transition, Err):
        print(json.dumps({"kind": transition.error.kind.name.lower(), "message": transition.error.message,
                          "fix": transition.error.fix}), file=sys.stderr)
        return 3
    hook_path = _lite_hook(repo)
    if hook_path is None:
        print(json.dumps({"kind": "not_found", "message": "lite transition hook is not installed",
                          "fix": "Install the atm-bd-lite skill."}), file=sys.stderr)
        return 3
    outcome = run_transition(phase_file, transition.value, values.value, result_values.value,
                             repo, hook_path)
    if isinstance(outcome, Err):
        print(json.dumps({"kind": outcome.error.kind.name.lower(), "message": outcome.error.message,
                          "fix": outcome.error.fix}), file=sys.stderr)
        return 3
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
