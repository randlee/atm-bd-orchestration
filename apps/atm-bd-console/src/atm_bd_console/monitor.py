"""Profile-neutral monitor contract and adapter for the existing console runner."""
from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from atm_bd_types import Refusal

    from .result import Error

from .closed_cache import ClosedBeads
from .state import StateStore
from .step_result import StepResult
from .types import Config, State


class Exit(enum.IntEnum):
    OK = 0
    UNAVAILABLE = 2
    CONFIG = 3


@dataclass(frozen=True)
class MonitorArgs:
    command: Literal["queues", "snapshot", "cron", "console", "show"]
    phase: str | None = None
    root: str | None = None
    all: bool = False
    stack: bool = False
    json: bool = False
    min_age: int = 10
    state_file: str | None = None
    md_table: bool = False
    github: Literal["graphql", "rest", "off"] | None = None
    interval: int | None = None
    github_poll_interval: int | None = None
    github_quota_threshold: int | None = None
    dry_run: bool = False
    no_fetch: bool = False


class PhaseMonitor(Protocol):
    def queues(self, args: MonitorArgs) -> Exit: ...
    def snapshot(self, args: MonitorArgs) -> Exit: ...
    def step(self, config: Config, state: State, force_github: bool, store: StateStore,
             cache: ClosedBeads | None = None) -> StepResult: ...
    def cron(self, args: MonitorArgs) -> Exit: ...


@dataclass(frozen=True)
class Route:
    """The selected monitor and everything the CLI needs to launch it."""
    monitor: PhaseMonitor
    config: object
    root_id: str
    step: Callable[..., StepResult]
    launch: Callable[[Error | None], int]


class TodayMonitor:
    """Delegate legacy behavior to the existing command and runner implementations."""

    def __init__(self, command: Callable[[MonitorArgs], int], step: Callable[..., StepResult]):
        self._command = command
        self.step = step

    def queues(self, args: MonitorArgs) -> Exit:
        return Exit(self._command(args))

    def snapshot(self, args: MonitorArgs) -> Exit:
        return Exit(self._command(args))

    def cron(self, args: MonitorArgs) -> Exit:
        return Exit(self._command(args))


def route(repo_root, args, command, step):
    """Select once from the phase file; old phases retain the existing runner."""
    import re
    import tomllib
    from pathlib import Path

    phase = args.phase

    def today():
        from . import config as config_source
        from .result import Ok
        selected = TodayMonitor(command, step)
        root_id = f"atm-phase-{phase}"
        if phase is None or args.command in ("queues", "show"):
            return Route(selected, None, root_id, selected.step, lambda _startup_error: command(args))
        cadence = config_source.CRON_CADENCE_S if args.interval is None and args.command == "cron" else args.interval
        loaded = config_source.load_config(repo_root, phase, github=args.github, interval_s=cadence,
                                           github_poll_interval_s=args.github_poll_interval,
                                           github_quota_threshold=args.github_quota_threshold,
                                           dry_run=args.dry_run or args.command == "snapshot" or args.md_table,
                                           no_fetch=args.no_fetch)
        config = loaded.value if isinstance(loaded, Ok) else loaded
        return Route(selected, config, root_id, selected.step, lambda _startup_error: command(args))

    def policy(data):
        from atm_bd_types import Refusal
        selected = PolicyMonitor(Path(repo_root), phase, data)
        config = selected._config(args)
        if args.command == "console":
            profile = selected._profile_path()
            if isinstance(profile, Refusal):
                config = profile

        def launch(startup_error):
            import json

            from atm_bd_types import HookReply

            from .app import run
            from .types import INITIAL_STATE
            if isinstance(config, Refusal):
                print(json.loads(HookReply.refused(config).to_json())["message"])
                return int(Exit.CONFIG)
            assert isinstance(config, Config)
            return run(config, None, INITIAL_STATE, startup_error, runner_step=selected.step)

        return Route(selected, config, selected.root_id, selected.step, launch)

    if phase is None:
        return today()
    if re.fullmatch(r"[a-z0-9]+", phase) is None:
        return policy({"_route_error": "invalid phase id"})
    path = Path(repo_root) / ".atm-bd" / f"phase-{phase}.toml"
    try:
        with path.open("rb") as source:
            phase_data = tomllib.load(source)
    except FileNotFoundError:
        return today()
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return policy({"_route_error": str(error)})
    if "profile" not in phase_data and "profile_path" not in phase_data:
        return today()
    return policy(phase_data)


class PolicyMonitor:
    """Adapt a profile tick to console commands without making policy decisions."""

    def __init__(self, root, phase, phase_data):
        self.root, self.phase, self.phase_data = root, phase, phase_data

    def _profile_path(self) -> Path | Refusal:
        from atm_bd_core.profile import LoadedProfile, load_profile
        from atm_bd_types import ErrorId, Refusal

        if "_route_error" in self.phase_data:
            return Refusal(ErrorId.PHASE_UNREADABLE, path=str(self.root), reason=self.phase_data["_route_error"])
        path = self.phase_data.get("profile_path")
        if not isinstance(path, str) or not path:
            return Refusal(ErrorId.PHASE_UNREADABLE, path=str(self.root / ".atm-bd" / f"phase-{self.phase}.toml"),
                           reason="missing profile_path")
        if Path(path).is_absolute():
            return Refusal(ErrorId.PHASE_UNREADABLE, path=path, reason="profile_path must be relative to the primary checkout")
        full_path = self.root / path
        loaded = load_profile(full_path)
        if not isinstance(loaded, LoadedProfile):
            return loaded
        if loaded.profile.name != self.phase_data.get("profile"):
            return Refusal(ErrorId.PROFILE_MISMATCH, path=str(full_path), profile=loaded.profile.name)
        return full_path

    def _tick(self, *, dry_run):
        from atm_bd_core.tick import tick

        profile_path = self._profile_path()
        if isinstance(profile_path, Path):
            return tick(profile_path, self.phase, self.root, dry_run=dry_run)
        return profile_path

    @property
    def root_id(self):
        return str(self.phase_data.get("root") or f"atm-phase-{self.phase}")

    def _config(self, args):
        import os

        from .paths import state_directory
        from .types import Config
        return Config(self.phase, str(self.phase_data.get("lead", "")), os.environ.get("ATM_TEAM", ""),
                      args.github or "off", args.interval or 60, True, args.no_fetch, str(self.root),
                      str(state_directory(self.root, self.root_id)))

    def _snapshot(self, result, config):
        from datetime import UTC, datetime

        from atm_bd_types import HookReply, Refusal, Report

        from .enums import CiState, SprintState
        from .result import ConfigInvalid, IoFailed
        from .types import (
            AgentView,
            GhStatus,
            Metrics,
            Phase,
            Row,
            Section,
            SectionRow,
            Snapshot,
            Sprint,
            SprintView,
            StepView,
        )

        now = datetime.now(UTC)
        if isinstance(result, Refusal):
            import json
            message = json.loads(HookReply.refused(result).to_json())["message"]
            error = ConfigInvalid("config_invalid", result.id.name, message, message)
            return Snapshot(1, now, self.phase, False, None, (), (), (), (error,), Metrics(0, 0, 0, 0),
                            GhStatus("off", None, None, None, False), None, None, "graph TD", (),
                            config.interval_s, config.lead, "", (), (), {})
        view = result.view
        now = datetime.fromtimestamp(view.generated_at, UTC)
        sprints = tuple(SprintView(s.id, s.title, SprintState(s.status.name.lower()), tuple(s.depends_on),
                                   tuple(StepView(t.bead_id, t.stage.name.lower() if t.stage.name.lower() in ("dev", "fix", "qa") else "other", SprintState(t.status.name.lower()),
                                                  t.assignee) for t in s.steps)) for s in view.sprints)
        groups = {}
        for row in view.rows:
            age = max(0, view.generated_at - row.since) if row.since is not None else 0
            groups.setdefault(row.queue, []).append(SectionRow(row.bead_id or row.key, age, row.text, None))
        for action in result.decision.actions:
            if isinstance(action, Report):
                groups.setdefault(action.queue, []).append(SectionRow(action.bead_id or action.key, 0, action.text, None))
        sections = tuple(Section(name, tuple(rows)) for name, rows in groups.items())
        errors = tuple(IoFailed("io_failed", str(e.kind), e.message, e.fix) for e in view.errors)
        task_groups = {}
        kinds = {step.bead_id: step.stage.name.lower() for sprint in view.sprints for step in sprint.steps}
        for task in view.tasks:
            if task.state.name == "COMPLETE":
                continue
            since = datetime.fromtimestamp(task.since, UTC) if task.since is not None else now
            active = task.state.name == "ACTIVE"
            kind = kinds.get(task.task_id, "other")
            row = Row(task.task_id, "running" if active else "queued", kind if kind in ("dev", "fix") else "other", None, "", None,
                      max(0, view.generated_at - task.since) if task.since is not None else 0, task.task_id)
            task_groups.setdefault(task.assignee, []).append((row, since, active))
        agents = tuple(AgentView(name, "busy" if any(item[2] for item in entries) else "idle",
                                 min(item[1] for item in entries), len(entries), tuple(item[0] for item in entries))
                       for name, entries in task_groups.items())
        phase_sprints = tuple(Sprint(s.id, s.title, 0, "", "", "", tuple(s.depends_on),
                                     s.status.name == "CLOSED", 0, SprintState(s.status.name.lower()))
                              for s in view.sprints)
        phase = (Phase(view.root_id, self.phase, view.root_id, view.root_closed, phase_sprints, (), ())
                 if result.facts.beads is not None else None)
        steps = [step for sprint in view.sprints for step in sprint.steps]
        done = sum(step.status.name == "CLOSED" for step in steps)
        metrics = Metrics(done, len(steps), 100 * done // len(steps) if steps else 0, 0)
        ci = {"PASSING": CiState.PASS, "FAILING": CiState.FAIL_BUG,
              "PENDING": CiState.RUNNING, "NONE": CiState.NONE}.get(view.top_ci.name) if view.top_ci else None
        return Snapshot(1, now, self.phase, view.root_closed, "closed" if view.root_closed else None, agents, sections,
                        (), errors, metrics, GhStatus("off", None, None, None, False),
                        None, ci, "graph TD", sprints, config.interval_s, view.lead, "", (), (), {}, phase_data=phase)

    def step(self, config: Config, state: State, force_github: bool, store: StateStore,
             cache: ClosedBeads | None = None) -> StepResult:
        return StepResult(self._snapshot(self._tick(dry_run=True), config), state)

    def queues(self, args: MonitorArgs) -> Exit:
        import json
        import sys

        from atm_bd_types import Refusal, Report
        result = self._tick(dry_run=True)
        if isinstance(result, Refusal):
            self._print_refusal(result)
            return Exit.CONFIG
        rows = [{"queue": row.queue, "key": row.key, "bead_id": row.bead_id, "text": row.text}
                for row in result.view.rows if row.queue != "quiet"]
        rows.extend({"queue": action.queue, "key": action.key, "bead_id": action.bead_id, "text": action.text}
                    for action in result.decision.actions if isinstance(action, Report) and action.queue != "quiet")
        for error in result.view.errors:
            print(f"{error.kind.name}: {error.message}; {error.fix}", file=sys.stderr)
        if args.json:
            print(json.dumps({"phase": self.phase, "rows": rows}))
        else:
            for row in rows:
                print(f"{row['queue']}: {row['text']}")
        return Exit.UNAVAILABLE if result.view.errors else Exit.OK

    @staticmethod
    def _print_refusal(refusal):
        import json

        from atm_bd_types import HookReply
        print(json.loads(HookReply.refused(refusal).to_json())["message"])

    def snapshot(self, args: MonitorArgs) -> Exit:
        from atm_bd_types import Refusal

        from .result import Err
        from .state import acquire_lock
        result = acquire_lock(self.root, self.root_id)
        if isinstance(result, Err):
            print(result.error)
            return Exit.UNAVAILABLE
        with result.value as store:
            tick = self._tick(dry_run=True)
            snapshot = self._snapshot(tick, self._config(args))
            written = store.write_snapshot(snapshot)
            if isinstance(written, Err):
                print(written.error)
                return Exit.UNAVAILABLE
            if isinstance(tick, Refusal):
                self._print_refusal(tick)
                return Exit.CONFIG
            return Exit.OK

    def cron(self, args: MonitorArgs) -> Exit:
        import json

        from atm_bd_types import HookReply, Refusal

        from .result import Err
        from .state import acquire_lock
        result = acquire_lock(self.root, self.root_id)
        if isinstance(result, Err):
            print(result.error)
            return Exit.UNAVAILABLE
        with result.value:
            tick = self._tick(dry_run=args.dry_run or args.md_table)
        if isinstance(tick, Refusal):
            self._print_refusal(tick)
            return Exit.CONFIG
        if args.md_table:
            from . import status_table
            snapshot = self._snapshot(tick, self._config(args))
            if snapshot.errors or snapshot.phase_data is None:
                import sys
                print("policy snapshot is incomplete", file=sys.stderr)
                return Exit.UNAVAILABLE
            print(status_table.markdown(status_table.rows(snapshot)))
            return Exit.OK
        import sys
        for error in tick.view.errors:
            print(f"{error.kind.name}: {error.message}; {error.fix}", file=sys.stderr)
        for action, outcome in zip(tick.view.actions, tick.outcomes):
            failure = (json.loads(HookReply.refused(outcome.failure).to_json())["message"]
                       if outcome.failure is not None else None)
            print(json.dumps({"kind": action.kind.name, "to": action.to, "bead_id": action.bead_id,
                              "key": action.key, "outcome": outcome.kind.name, "error": failure}))
        return Exit.UNAVAILABLE if tick.view.errors or any(outcome.kind.name == "FAILED" for outcome in tick.outcomes) else Exit.OK
