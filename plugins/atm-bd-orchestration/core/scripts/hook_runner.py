#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.19.12"]
# ///
# pyright: strict
"""Profile-first runner boundary for the lite transition planner."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

from atm_bd_types import CloseVars, Error, ErrorKind, Profile, Transition
from result import Err, Ok, Result


class HookModule(Protocol):
    Observed: Any
    def plan(self, transition: Transition, vars: CloseVars, observed: object) -> object: ...


Executor = Callable[[Sequence[str]], Result[str]]
TemplateRenderer = Callable[[Path, dict[str, object]], Result[str]]


def render_lite_template(phase_file: Path, template: Path, variables: dict[str, object],
                         renderer: TemplateRenderer) -> Result[str]:
    """Refuse a non-lite phase before asking the renderer to read a template."""
    from phase_profile import require_profile

    gate = require_profile(phase_file, Profile.LITE)
    if isinstance(gate, Err):
        return gate
    return renderer(template, variables)


def _load_hook(path: Path) -> HookModule:
    spec = importlib.util.spec_from_file_location("atm_bd_lite_task_hook", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load lite hook from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(HookModule, module)


def run_transition(phase_file: Path, transition: Transition, close_vars: CloseVars, observed: object,
                   hook_path: Path, executor: Executor) -> Result[None]:
    """Gate before planning, then execute in order and stop at the first typed error."""
    from phase_profile import require_profile

    gate = require_profile(phase_file, Profile.LITE)
    if isinstance(gate, Err):
        return gate
    try:
        plan = _load_hook(hook_path).plan(transition, close_vars, observed)
    except (ImportError, OSError, ValueError) as error:
        return Err(Error(ErrorKind.CONFIG_INVALID, str(error), "Repair the installed lite hook and retry."))
    if hasattr(plan, "error"):
        return Err(cast(Any, plan).error)
    commands = cast(Any, plan).value
    for command in commands:
        if command.idempotent_when(cast(Any, observed)):
            continue
        result = executor(command.argv)
        if isinstance(result, Err):
            return result
    return Ok(None)


def subprocess_executor(cwd: Path) -> Executor:
    def execute(argv: Sequence[str]) -> Result[str]:
        try:
            done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as error:
            return Err(Error(ErrorKind.UNREACHABLE, str(error), f"Repair and rerun: {' '.join(argv)}"))
        if done.returncode:
            return Err(Error(ErrorKind.COMMAND_FAILED, f"{' '.join(argv)}: {done.stderr.strip()}",
                             f"Repair the failed step and rerun the same hook command: {' '.join(argv)}"))
        return Ok(done.stdout)
    return execute


def main(argv: list[str] | None = None) -> int:
    import argparse
    from atm_bd_types import Transition as TransitionType

    parser = argparse.ArgumentParser(prog="atm-bd-task-close")
    parser.add_argument("--phase-file", type=Path, required=True)
    parser.add_argument("--hook", type=Path, required=True)
    parser.add_argument("--transition", choices=[member.name.lower() for member in TransitionType], required=True)
    parser.add_argument("--vars", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    from phase_profile import require_profile

    profile = require_profile(args.phase_file, Profile.LITE)
    if isinstance(profile, Err):
        print(json.dumps({"kind": profile.error.kind.name.lower(), "message": profile.error.message,
                          "fix": profile.error.fix}), file=sys.stderr)
        return 3
    try:
        vars_data = json.loads(args.vars.read_text(encoding="utf-8"))
        if not isinstance(vars_data, dict):
            raise TypeError("close vars must be a JSON object")
        raw_state = json.loads(args.observed.read_text(encoding="utf-8"))
        close_vars = CloseVars()
        transition = cast(Transition, getattr(TransitionType, args.transition.upper()))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(json.dumps({"kind": "config_invalid", "message": str(error), "fix": "Repair the vars and observed JSON."}),
              file=sys.stderr)
        return 3
    loaded = _load_hook(args.hook)
    state = loaded.Observed(**raw_state)
    outcome = run_transition(args.phase_file, transition, close_vars, state, args.hook, subprocess_executor(args.cwd))
    if isinstance(outcome, Err):
        print(json.dumps({"kind": outcome.error.kind.name.lower(), "message": outcome.error.message,
                          "fix": outcome.error.fix}), file=sys.stderr)
        return 3
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
