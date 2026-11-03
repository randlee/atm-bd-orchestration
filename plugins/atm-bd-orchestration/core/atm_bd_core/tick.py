"""The cron host: one tick. Load the profile, its policy and cron script; collect PhaseFacts; call the plug-in's
decide(facts, params); dedupe by key; execute; return TickResult. The same for every profile; names no profile.

The plug-in decides every meaningful state change; this module only loads, collects, dedupes and executes.
"""
from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from atm_bd_types import Action, Assign, Bead, Notify, PhaseFacts, PhaseFile, Refusal, Status
from atm_bd_types._core import (ActionKind, ActionOutcome, CommandResult, Decision, PhaseView, Ports, TickResult,
                                ViewAction, ViewSprint, ViewStep, ViewTask)

from .collect import collect
from .execute import Executor, Ledger, action_key, dedupe
from .profile import load_cron, load_policy, load_profile
from .store import CacheStore, PhaseFilesCli

Collector = Callable[[str, PhaseFile, Ports, int, Path], PhaseFacts]


class SubprocessRunner:
    """The production CommandRunner: runs argv with stdin and captures text output."""

    def run(self, argv: list[str], stdin: str | None) -> CommandResult:
        done = subprocess.run(argv, input=stdin, capture_output=True, text=True, check=False)
        return CommandResult(done.returncode, done.stdout, done.stderr)


def phase_paths(primary: Path, phase: str) -> tuple[Path, Path]:
    """The phase file and the phase's state directory under the primary checkout."""
    base = primary / ".atm-bd"
    return base / f"phase-{phase}.toml", base / "state" / f"phase-{phase}"


def default_ports(phase: str) -> Ports | Refusal:
    cache = CacheStore.for_phase(phase)
    return cache if isinstance(cache, Refusal) else Ports(SubprocessRunner(), cache)


def tick(profile_path: Path, phase: str, primary: Path, *, ports: Ports | None = None, now: int | None = None,
         dry_run: bool = False, collector: Collector = collect) -> TickResult | Refusal:
    """One tick. Refuses before any read when the profile, policy, cron script or phase file does not load."""
    loaded = load_profile(profile_path)
    if isinstance(loaded, Refusal):
        return loaded
    policy = load_policy(loaded)
    if isinstance(policy, Refusal):
        return policy
    cron = load_cron(loaded)
    if isinstance(cron, Refusal):
        return cron
    phase_path, state_dir = phase_paths(primary, phase)
    phase_file = PhaseFilesCli().load(str(phase_path), loaded.profile.name)
    if isinstance(phase_file, Refusal):
        return phase_file
    ledger = Ledger.load(state_dir)
    if isinstance(ledger, Refusal):
        return ledger
    if ports is None:
        made = default_ports(phase)
        if isinstance(made, Refusal):
            return made
        ports = made

    facts = collector(phase, phase_file, ports, int(time.time()) if now is None else now, state_dir)
    decided: list[Action] = [] if cron is None else list(cron.decide(facts, policy.params))
    reported = None if facts.reported_keys is None else list(facts.reported_keys)
    decision = dedupe(decided, reported, ledger)
    executor = Executor(ports.runner, state_dir, loaded.root, phase_file.lead, policy.notify_template)
    outcomes = executor.run(decision, decided, reported, ledger, dry_run)
    root_id = phase_file.key("root") or ""
    return TickResult(facts, decision, view(facts, decision, outcomes, root_id), outcomes)


def _view_action(action: Action, lead: str, outcome: ActionOutcome | None) -> ViewAction:
    kind, to, bead = (
        (ActionKind.ASSIGN, action.to, action.bead_id) if isinstance(action, Assign)
        else (ActionKind.NOTIFY, action.to, None) if isinstance(action, Notify)
        else (ActionKind.REPORT, lead, action.bead_id))
    return ViewAction(kind, to, bead, action_key(action), None if outcome is None else outcome.kind)


def _sprints(beads: list[Bead], ready: set[str]) -> list[ViewSprint]:
    by_id = {bead.id: bead for bead in beads}
    groups: dict[str, list[Bead]] = {}
    for bead in beads:
        if bead.sprint and bead.sprint != bead.id:
            groups.setdefault(bead.sprint, []).append(bead)
    sprints = []
    for sprint_id, members in sorted(groups.items()):
        steps = [ViewStep(b.id, b.stage, b.status, b.assignee, b.id in ready) for b in members]
        head = by_id.get(sprint_id)
        if head is not None:
            status, depends = head.status, list(head.open_blockers)
        else:
            done = all(b.status == Status.CLOSED for b in members)
            status, depends = (Status.CLOSED if done else Status.OPEN), []
        # Facts carry no bead titles; the sprint id is the only name available.
        sprints.append(ViewSprint(sprint_id, sprint_id, status, depends, steps))
    return sprints


def view(facts: PhaseFacts, decision: Decision, outcomes: list[ActionOutcome], root_id: str) -> PhaseView:
    """The tick's PhaseView, built only from facts, the decision and its outcomes."""
    lead = facts.phase_file.lead
    beads = facts.beads or []
    ready = {bead.id for bead in facts.ready or []}
    events = {e.task_id: e for e in facts.task_events or []}
    tasks = [ViewTask(t.task_id, t.assignee, t.state,
                      events[t.task_id].reminders_since_start if t.task_id in events else 0,
                      events[t.task_id].last_start if t.task_id in events else None)
             for t in facts.tasks or []]
    by_action = dict(zip((action_key(a) for a in decision.actions), outcomes))
    actions = [_view_action(a, lead, by_action.get(action_key(a))) for a in decision.actions]
    root_closed = any(b.id == root_id and b.status == Status.CLOSED for b in beads)
    return PhaseView(facts.phase, root_id, root_closed, lead, facts.now, _sprints(beads, ready), tasks,
                     list(decision.rows), actions, facts.top_checks.state if facts.top_checks else None,
                     list(facts.errors))


__all__ = ["SubprocessRunner", "default_ports", "phase_paths", "tick", "view"]
