#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.20.0"]
# ///
# pyright: strict
"""Run one profile-gated lite queue tick."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol, cast

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

from atm_bd_types import Error, ErrorKind, Profile
from atm_bd_console.command import Output
from result import Result


class Cache(Protocol):
    def sync(self, phase: str) -> object: ...


Runner = Callable[..., Result[Output]]


def tick(repo_root: Path, phase: str, *, cache: Cache, queue_runner: Runner,
         now: datetime | None = None) -> tuple[Error | None, dict[str, object] | None]:
    """Refresh then return actionable lite queue and stalled task rows."""
    from atm_bd_console import atm_bd, queues
    from phase_profile import require_profile
    from result import Err, Ok

    phase_path = repo_root / ".atm-bd" / f"phase-{phase}.toml"
    gated = require_profile(phase_path, Profile.LITE)
    if isinstance(gated, Err):
        return gated.error, None
    resolved = atm_bd.phase_file(str(repo_root), phase, expected_profile=Profile.LITE)
    if isinstance(resolved, Err):
        return resolved.error, None
    try:
        cache.sync(phase)
        captured: list[dict[str, object]] = []

        def capture(argv: list[str], fix: str, *, cwd: str | Path | None = None) -> Result[Output]:
            result = queue_runner(argv, fix, cwd=cwd)
            if argv[:4] == ["atm", "task", "list", "--all"] and isinstance(result, Ok):
                rows = json.loads(result.value.stdout or "[]")
                if isinstance(rows, list):
                    captured.extend(cast(dict[str, object], row) for row in cast(list[object], rows)
                                    if isinstance(row, dict))
            return result

        report = queues.build(SimpleNamespace(phase=phase, root=None, stack=False),
                              repo_root, now=now, runner=capture)
    except (OSError, RuntimeError, ValueError, queues.QueueFailure) as exc:
        return Error(ErrorKind.COMMAND_FAILED, str(exc), "Repair the phase queue source and retry the lite cron tick."), None
    root_id = resolved.value.root_id
    phase_prefix = f"{root_id.removesuffix(f'-phase-{phase}')}-{phase}-"
    stalled = [row for row in captured
               if isinstance(row.get("task_id"), str)
               and cast(str, row["task_id"]).startswith(phase_prefix)
               and row.get("state") == "active"
               and isinstance(row.get("reminder_count"), int)
               and cast(int, row["reminder_count"]) >= queues.STALL_REMINDERS]
    queue_rows = cast(dict[str, list[dict[str, object]]], report["queues"])
    if not any(queue_rows.values()) and not stalled:
        return None, None
    return None, {"phase": phase, "root": root_id, "profile": "lite", "queues": queue_rows,
                  "stalled_tasks": stalled, "generated_at": report["generated_at"]}


def _core_scripts(repo_root: Path) -> Path | None:
    for path in (repo_root / ".atm-bd" / "scripts",
                 repo_root / "plugins" / "atm-bd-orchestration" / "core" / "scripts"):
        if (path / "core_paths.py").is_file():
            return path
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lite_cron.py")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--md-table", action="store_true")
    parser.add_argument("--github", choices=("graphql", "rest", "off"))
    parser.add_argument("--interval", type=int)
    parser.add_argument("--github-poll-interval", type=int)
    parser.add_argument("--github-quota-threshold", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    args = parser.parse_args(argv)
    from atm_bd_console.config import repo_root

    root = repo_root()
    core = _core_scripts(root)
    if core is None:
        print(json.dumps({"kind": "not_found", "message": "atm-bd core scripts are not installed",
                          "fix": "Install atm-bd-orchestration core scripts."}), file=sys.stderr)
        return 3
    sys.path.insert(0, str(core))
    import bd_cache
    from atm_bd_console.command import run

    error, output = tick(root, args.phase, cache=bd_cache.BdCache(root), queue_runner=run)
    if error is not None:
        print(json.dumps({"kind": error.kind.name.lower(), "message": error.message, "fix": error.fix}), file=sys.stderr)
        return 3
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
