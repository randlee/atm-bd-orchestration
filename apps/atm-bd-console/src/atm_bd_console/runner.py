"""Impure tick boundary; scheduling and decisions remain in :mod:`model`."""
from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Literal, Protocol

from sc_observability import Level

from . import atm_bd, atm_source, beads_source, git_source, github_source, ledger_source, model
from .closed_cache import ClosedBeads
from .dispatch import candidates, sprint_of, verification_reason
from .enums import MergeState, PrState, SprintState
from .log import EventAction, TickLog, create_console_logger, error_message
from .result import Err, Error, NotFound, Ok, Result
from .state import StateStore, read_snapshot
from .types import (
    Action,
    ActionLine,
    Bead,
    Config,
    GhStatus,
    Inputs,
    Merge,
    MergeFile,
    Metrics,
    Phase,
    PrsFile,
    Snapshot,
    State,
    StepResult,
    Task,
)


def _unique(errors) -> tuple[Error, ...]:
    """Each distinct error once, in first-seen order."""
    return tuple(dict.fromkeys(errors))


def _gh(mode: Literal["graphql", "rest", "off"]) -> GhStatus:
    return GhStatus(mode, None, None, None, False)


class _ActionStore(Protocol):
    def append_action(self, value: ActionLine) -> Result[None]: ...


class _ActionLogger(Protocol):
    def mark_reported(self, error: Error) -> None: ...

    def event(self, action: EventAction, *, level: Level = "info", message: str | None = None,
              **fields: object) -> None: ...


def _run_actions(config: Config, actions: tuple[Action, ...], store: _ActionStore, now: datetime,
                 logger: _ActionLogger) -> tuple[tuple[Action, ...], tuple]:
    """Run actions and retain their actual delivery outcome for reporting."""
    errors = []
    reported = []
    for action in actions:
        bead = action.bead_ids[0] if action.bead_ids else None
        result = Ok(None)
        if config.dry_run:
            logged = store.append_action(ActionLine(now, "dry_run", action.to, bead, action.text))
            if isinstance(logged, Err): errors.append(logged.error)
            reported.append(replace(action, outcome="dry_run"))
        else:
            if action.kind == "assign" and action.spec is not None and bead:
                result = atm_source.assign(action.to, bead, action.spec, config.lead, config.team)
            else:
                sender, sender_team = config.notification_sender.split("@", 1)
                recipient = action.to if "@" in action.to else f"{action.to}@{config.team}"
                result = atm_source.send(recipient, action.text, sender, sender_team)
            logged = store.append_action(ActionLine(now, action.kind, action.to, bead, action.text))
            if isinstance(logged, Err): errors.append(logged.error)
            if isinstance(result, Err):
                errors.append(result.error)
                held = store.append_action(ActionLine(now, "hold", action.to, bead, result.error.fix))
                if isinstance(held, Err): errors.append(held.error)
                reported.append(replace(action, outcome=f"failed {result.error.kind}"))
            else:
                reported.append(replace(action, outcome="sent"))
        if isinstance(result, Err):
            logger.mark_reported(result.error)
        logger.event(
            "action", effect=action.kind, recipient=action.to, task_ids=list(action.bead_ids),
            outcome=reported[-1].outcome,
            level="error" if isinstance(result, Err) else "info",
            message=error_message(asdict(result.error)) if isinstance(result, Err) else None,
            error=asdict(result.error) if isinstance(result, Err) else None,
        )
    return tuple(reported), tuple(errors)


def _durable_state(state: State, proposed: State, actions: tuple[Action, ...], reported: tuple[Action, ...]) -> State:
    """Commit only effects whose boundary call actually succeeded.

    A failed batch keeps its previous due time (or none, so the next tick sends
    it again), so a recipient's problems are never marked delivered unsent.
    """
    successful = tuple(action for action in reported if action.outcome == "sent")
    failed = tuple(action for action in reported if action.outcome and action.outcome.startswith("failed "))
    failed_batches = {action.to for action in failed if action.kind == "batch"}
    batch_due = dict(proposed.batch_due)
    for recipient in failed_batches:
        if recipient in state.batch_due:
            batch_due[recipient] = state.batch_due[recipient]
        else:
            batch_due.pop(recipient, None)
    notices_succeeded = any(action.kind == "batch" for action in successful)
    return replace(
        proposed,
        cycle_first_send=proposed.cycle_first_send if notices_succeeded else state.cycle_first_send,
        last_batch=proposed.last_batch if any(action.kind == "batch" for action in successful) else state.last_batch,
        sent=(*state.sent, *successful)[-5:],
        batch_due=batch_due,
    )


def _write_snapshot(store: StateStore, snapshot: Snapshot, logger: TickLog) -> Snapshot:
    written = store.write_snapshot(snapshot)
    if isinstance(written, Ok):
        return snapshot
    previous_errors = len(logger.errors)
    logger.error(written.error, source="snapshot.write")
    logger.flush()
    return replace(snapshot, errors=(*snapshot.errors, written.error, *logger.errors[previous_errors:]))


def _branch_groups(phase, repo) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(dict.fromkeys((sprint.branch, *(
        step.branch for step in phase.steps if step.branch and sprint_of(step, phase, repo.bead_prefix) == sprint
    )))) for sprint in phase.sprints)


def _phase_heads(phase) -> tuple[str, ...]:
    """Every branch the model can match a PR to: the sprint branches and every step's branch (dev, fix, ...)."""
    if not isinstance(phase, Ok):
        return ()
    return tuple(dict.fromkeys(branch for branch in (*(sprint.branch for sprint in phase.value.sprints),
                                                     *(step.branch for step in phase.value.steps)) if branch))


def _refresh_github(config: Config, now: datetime, gh: GhStatus, groups=(), heads: tuple[str, ...] = ()):
    """One GitHub refresh: the configured stack's membership (None when no stack is configured), then the PRs.

    Membership is read first and through the same quota budget, so every PR it names was linked before the PR
    list was read and is in it."""
    if config.github == "off":
        return Ok(()), _gh("off"), None
    code_root = config.code_root or config.repo_root
    budget = github_source.Budget(config.github, code_root, config.github_quota_threshold,
                                  config.github_poll_interval_s, now, gh, config.github_repo)
    stack = None if config.stack_number is None else github_source.stack_membership(
        config.github, code_root, config.stack_repo or config.github_repo, config.stack_number,
        config.stack_trunk, budget)
    numbers = stack.value if isinstance(stack, Ok) else ()
    result, status = github_source.open_prs(config.github, code_root, groups, budget, config.github_repo,
                                            heads, numbers)
    if status.paused and gh.mode == config.github:
        status = replace(status, ok=gh.ok, error=None, at=gh.at, truncated=gh.truncated)
    return result, status, stack


def _sanity_host(config: Config, phase, logger: TickLog) -> Result[atm_bd.SanityHost] | None:
    """The host reads a sanity re-dispatch needs, made only when a sanity step is ready: the beads directory and each
    of those steps' phases' `atm hook list` rows (close_fields.sanity_assignment_vars)."""
    if not isinstance(phase, Ok):
        return None
    phases = sorted({str((step.sanity_row or {}).get("metadata", {}).get("phase") or "")
                     for step in phase.value.steps if step.kind == atm_bd.SANITY_KIND and step.ready} - {""})
    if not phases:
        return None
    beads_dir = logger.result("beads.where", beads_source.where(cwd=config.repo_root))
    if isinstance(beads_dir, Err):
        return beads_dir
    hooks = {}
    for name in phases:
        rows = logger.result("atm.hooks", atm_source.hooks(name, config.lead, config.team), phase=name)
        if isinstance(rows, Err):
            return rows
        hooks[name] = rows.value
    return Ok(atm_bd.SanityHost(beads_dir.value, hooks))


def _cached_stack(config: Config, cached: PrsFile | None) -> tuple[int, ...] | None:
    """The cached membership, only when it was read for the stack configured now."""
    if cached is None or config.stack_number is None or cached.stack_number != config.stack_number:
        return None
    return cached.stack_prs


def _stack_input(config: Config, cached: tuple[int, ...] | None, read) -> Result[tuple[int, ...]] | None:
    """Membership for this tick: the cached pair when present, else this tick's read, else a typed not-read."""
    if config.stack_number is None:
        return None
    if config.github == "off":
        return github_source.stack_membership("off", None, config.stack_repo or config.github_repo,
                                              config.stack_number, config.stack_trunk)
    if cached is not None:
        return Ok(cached)
    if read is not None:
        return read
    return Err(NotFound("not_found", "hosted stack membership",
                        "wait for the next GitHub poll (github_poll_interval) or force a GitHub refresh"))


def _show_closed(closed: ClosedBeads, ids: tuple[str, ...], logger: TickLog) -> Result[tuple[Bead, ...]]:
    """Read only the ids not yet cached; a failed read is the original Err and caches nothing. Beads that are
    not closed are returned for this tick but never cached."""
    missing = closed.missing_beads(ids)
    if not missing:
        return Ok(closed.cached_beads(ids))
    fresh = logger.result("beads.show_closed", beads_source.show(missing), task_ids=list(missing))
    if isinstance(fresh, Err):
        return fresh
    closed.store_beads(fresh.value)
    returned = {bead.id for bead in fresh.value}
    return Ok((*fresh.value, *closed.cached_beads(bead_id for bead_id in ids if bead_id not in returned)))


def _persist_closed(closed: ClosedBeads, logger: TickLog) -> tuple[Error, ...]:
    """Write the cache when it changed. Returns the errors for the snapshot: the startup load error (once) and
    a failed write; neither stops the tick."""
    errors = [*closed.pending_errors]
    closed.pending_errors.clear()
    saved = closed.save()
    if isinstance(saved, Err):
        errors.append(saved.error)
    for error in errors:
        logger.error(error, source="closed_cache")
    return tuple(errors)


def _stopped_tick(config: Config, state: State, now: datetime, store: StateStore, file, repo, root_bead, logger,
                  force_github: bool = False, closed: ClosedBeads | None = None):
    closed = closed if closed is not None else ClosedBeads()
    shown = _show_closed(closed, atm_bd.closed_show_ids(file, ()), logger)
    closed_errors = _persist_closed(closed, logger)
    phase = shown if isinstance(shown, Err) else atm_bd.phase(file, root_bead, (), (), shown.value)
    if root_bead is not None and root_bead.status == SprintState.CLOSED and isinstance(phase, Ok):
        phase = Ok(replace(phase.value, step_errors=()))
    # Read the caches from the held store, the directory the running ticks write: the console names it
    # atm-phase-<x> whatever the bead prefix, so the phase file's root id (<prefix>-phase-<x>) is not its name.
    cached_prs = store.load_prs()
    cached_merges = store.load_merges()
    cached_snapshot = read_snapshot(store.directory)
    history = store.load_actions()
    prs = Ok(cached_prs.value.prs) if isinstance(cached_prs, Ok) else Ok(())
    gh = cached_prs.value.gh if config.github != "off" and isinstance(cached_prs, Ok) else _gh(config.github)
    gh = replace(gh, poll_interval_s=config.github_poll_interval_s, quota_threshold=config.github_quota_threshold)
    cache_errors = ()
    prs_read_at = cached_prs.value.read_at if isinstance(cached_prs, Ok) else None
    if force_github and config.github != "off":
        groups = _branch_groups(phase.value, repo) if config.github == "rest" and isinstance(phase, Ok) else ()
        refreshed, gh, stack = _refresh_github(config, now, gh, groups, _phase_heads(phase))
        stack_prs = _cached_stack(config, cached_prs.value if isinstance(cached_prs, Ok) else None)
        if isinstance(refreshed, Ok):
            prs = refreshed
            if isinstance(stack, Ok):
                stack_prs = stack.value
        previous_read = cached_prs.value.read_at if isinstance(cached_prs, Ok) else now
        prs_read_at = now if isinstance(refreshed, Ok) else prs_read_at
        saved = store.write_prs(PrsFile(now if isinstance(refreshed, Ok) else previous_read, gh, prs.value, attempted_at=now,
                                        stack_number=config.stack_number if stack_prs is not None else None,
                                        stack_prs=stack_prs))
        if isinstance(saved, Err):
            cache_errors = (saved.error,)
            logger.event("error", source="prs.write", error=asdict(saved.error))
    merges = tuple(Ok(merge) for merge in cached_merges.value.merges.values()) if isinstance(cached_merges, Ok) else ()
    sent = tuple(
        Action(line.at, line.kind if line.kind in ("assign", "send", "batch") else "send", line.to or "—",
               (line.bead,) if line.bead else (),
               line.text if line.kind in ("assign", "send", "batch") else f"{line.kind}: {line.text}", None, "recorded")
        for line in history.value[-5:]
    ) if isinstance(history, Ok) else ()
    snapshot, _, next_state = model.tick(
        Inputs(now, config.lead, repo, config.interval_s, phase, Ok(()), Ok(()), Ok(()), None, merges, prs, gh, Ok(()), Ok(())),
        state,
        now,
        partial(atm_bd.dispatch_spec, templates=file.templates),
    )
    if not snapshot.phase:
        snapshot = replace(snapshot, phase=config.phase)
    if isinstance(cached_snapshot, Ok):
        snapshot = replace(snapshot, agents=cached_snapshot.value.agents)
    snapshot = replace(snapshot, sent=sent)
    next_state = state if config.dry_run else next_state
    written = store.write_state(next_state)
    history_errors = () if isinstance(history, Ok) or isinstance(history.error, NotFound) else (history.error,)
    errors = (*snapshot.errors, *history_errors, *closed_errors, *store.load_errors, *cache_errors, *((written.error,) if isinstance(written, Err) else ()))
    sanity = logger.result("sanity.ledger", ledger_source.sanity_runs(config.repo_root, config.phase))
    for error in errors:
        logger.error(error)
    logger.finish(actions=0)
    persisted = replace(snapshot, errors=_unique((*errors, *logger.errors)), files={"snapshot": str(store.directory / "snapshot.json"), "state": str(store.directory / "state.json")})
    snapshot = _write_snapshot(store, persisted, logger)
    # The open QA rows were not read on a stopped tick: no quality result, so the held rows stay.
    return StepResult(snapshot, next_state, sanity=sanity, failed_reads=logger.failed_reads, prs_read_at=prs_read_at)


def _closed_tasks(
    config: Config, phase: Result[Phase], tasks: Result[tuple[Task, ...]], logger: TickLog,
) -> Result[tuple[str, ...]]:
    """Ids of would-be dispatch candidates whose ATM task is closed. `atm task list` shows open tasks only, so each
    candidate's history is read once per tick with `atm task events`; no other bead costs a call."""
    if not isinstance(phase, Ok) or not isinstance(tasks, Ok):
        return Ok(())
    closed: list[str] = []
    for step in candidates(phase.value, tasks.value, frozenset()):
        result = logger.result("atm.task_events", atm_source.task_closed(step.bead_id, config.team, config.lead),
                               task_id=step.bead_id)
        if isinstance(result, Err):
            return result
        if result.value:
            closed.append(step.bead_id)
    return Ok(tuple(closed))


def step(config: Config, state: State, force_github: bool, store: StateStore,
         cache: ClosedBeads | None = None) -> StepResult:
    """Run one best-effort tick using the caller-owned lock-backed store and closed-bead cache."""
    cache = cache if cache is not None else ClosedBeads()
    now = datetime.now(UTC)
    logger = TickLog(create_console_logger(config.repo_root))
    logger.event("tick_start", phase=config.phase)
    file = logger.result("phase_file", atm_bd.phase_file(config.repo_root, config.phase), phase=config.phase)
    repo = logger.result("repo_config", atm_bd.repo_config(config.repo_root))
    if isinstance(file, Err) or isinstance(repo, Err):
        errors = (*store.load_errors, *(item.error for item in (file, repo) if isinstance(item, Err)))
        snapshot = Snapshot(1, now, config.phase, False, None, (), (), (), errors, Metrics(0, 0, 0, 0),
                            _gh(config.github), None, None, "graph TD", (), config.interval_s, config.lead,
                            "", (), (), {})
        state_written = store.write_state(state)
        if isinstance(state_written, Err): snapshot = replace(snapshot, errors=(*snapshot.errors, state_written.error))
        for error in snapshot.errors:
            logger.error(error)
        logger.finish(actions=0)
        persisted = replace(snapshot, errors=_unique((*snapshot.errors, *logger.errors)), files={"snapshot": str(store.directory / "snapshot.json"), "state": str(store.directory / "state.json")})
        persisted = _write_snapshot(store, persisted, logger)
        return StepResult(persisted, state, failed_reads=logger.failed_reads)
    config = replace(config, lead=file.value.lead)
    # A failed `bd show` is the original Err, passed on unchanged; not_found is only a successful empty read.
    root = logger.result("beads.show_root", beads_source.show((file.value.root_id,)), task_ids=[file.value.root_id])
    root_bead = root.value[0] if isinstance(root, Ok) and root.value else None
    # This is deliberately the sole read on a closed phase.
    if root_bead is not None and root_bead.status == SprintState.CLOSED:
        return _stopped_tick(config, state, now, store, file.value, repo.value, root_bead, logger, force_github, cache)
    if not force_github and isinstance(root, Ok) and model.idle_stop_due(state, now):
        return _stopped_tick(config, state, now, store, file.value, repo.value, root_bead, logger, closed=cache)
    opened = logger.result("beads.open", beads_source.open_rows(file.value.label), label=file.value.label)
    ready = logger.result("beads.ready", beads_source.ready(file.value.label), label=file.value.label)
    known = opened.value.beads if isinstance(opened, Ok) else ()
    if isinstance(opened, Ok):
        cache.forget_beads(bead.id for bead in known)
        cache.note_open(config.phase, opened.value.rows)
    shown = _show_closed(cache, atm_bd.closed_show_ids(file.value, known), logger)
    closed_errors = _persist_closed(cache, logger)
    if isinstance(root, Err):
        phase = root
    elif isinstance(opened, Err):
        phase = opened
    elif isinstance(ready, Err):
        phase = ready
    elif isinstance(shown, Err):
        phase = shown
    else:
        phase = atm_bd.phase(file.value, root_bead, known, ready.value, shown.value)
    logger.result("phase", phase)
    sanity = logger.result("sanity.ledger", ledger_source.sanity_runs(config.repo_root, config.phase))
    quality = opened if isinstance(opened, Err) else Ok(ledger_source.open_quality(config.phase, opened.value.rows))
    members = logger.result("atm.members", atm_source.members(config.team, config.lead), team=config.team)
    tasks = logger.result("atm.tasks", atm_source.tasks(config.team, config.lead), team=config.team)
    closed_tasks = _closed_tasks(config, phase, tasks, logger)
    closed = frozenset(closed_tasks.value) if isinstance(closed_tasks, Ok) else frozenset()
    code_root = config.code_root or config.repo_root
    worktrees = logger.result("git.worktrees", git_source.worktrees(code_root))
    task_ids = tuple(task.id for task in tasks.value) if isinstance(tasks, Ok) else ()
    task_beads = logger.result("beads.show_tasks", beads_source.show_tasks(task_ids), task_ids=list(task_ids))
    if isinstance(task_beads, Ok) and task_beads.value:
        task_beads = logger.result("beads.task_ancestors", beads_source.ancestors(task_beads.value))
    due = model.due(
        state,
        phase.value,
        repo.value.bead_prefix,
        config.github,
        now,
        tasks.value if isinstance(tasks, Ok) else (),
        closed,
    ) if isinstance(phase, Ok) else None
    remotes = None
    if due and due.fetch and not config.no_fetch:
        fetched = logger.result("git.fetch", git_source.fetch(code_root))
        remotes = fetched if isinstance(fetched, Err) else None
        if isinstance(fetched, Ok):
            remotes = logger.result("git.remote_refs", git_source.remote_refs(code_root))
            if isinstance(remotes, Ok) and isinstance(phase, Ok):
                due = model.due(
                    replace(state, remotes=remotes.value), phase.value,
                    repo.value.bead_prefix, config.github, now,
                    tasks.value if isinstance(tasks, Ok) else (),
                    closed,
                )
    saved_merges = logger.result("cache.merges", store.load_merges())
    saved_prs = logger.result("cache.prs", store.load_prs())
    cached_prs = saved_prs.value if config.github != "off" and isinstance(saved_prs, Ok) else None
    gh = cached_prs.gh if cached_prs is not None else _gh(config.github)
    gh = replace(gh, poll_interval_s=config.github_poll_interval_s, quota_threshold=config.github_quota_threshold)
    prs = cached_prs.prs if cached_prs is not None else ()
    prs_read_at = cached_prs.read_at if cached_prs is not None else now
    prs_input = Ok(prs) if cached_prs is not None else None
    attempted_at = cached_prs.attempted_at if cached_prs is not None else None
    github_due = (attempted_at is None or cached_prs is None or cached_prs.gh.mode != config.github
                  or now - attempted_at >= timedelta(seconds=config.github_poll_interval_s))
    refresh_errors = []
    cached_stack = _cached_stack(config, cached_prs)
    stack_read = None
    if config.github != "off" and (force_github or (due and github_due)):
        branch_groups = _branch_groups(phase.value, repo.value) if config.github == "rest" and isinstance(phase, Ok) else ()
        refreshed_prs, gh, stack_read = _refresh_github(config, now, gh, branch_groups, _phase_heads(phase))
        stack_read = logger.result("github.stack_membership", stack_read) if stack_read is not None else None
        attempted_at = now
        if isinstance(refreshed_prs, Ok):
            prs_input, prs, prs_read_at = refreshed_prs, refreshed_prs.value, now
            # Membership and PRs are replaced together or not at all, so the cache never pairs a membership
            # with an older PR list (the false stack_snapshot:stale alert).
            if isinstance(stack_read, Ok):
                cached_stack = stack_read.value
            elif isinstance(stack_read, Err) and cached_stack is not None and github_source.throttled(stack_read.error):
                # Low quota skipped the membership read: keep the cached membership (it is older than the PRs, so it
                # can only name no top, never a stale one) and report the skip once, on this poll.
                refresh_errors.append(stack_read.error)
            elif isinstance(stack_read, Err):
                cached_stack = None
        elif cached_prs is None:
            prs_input = refreshed_prs
        else:
            refresh_errors.append(refreshed_prs.error)
        logger.event("github_read", forced=force_github, outcome="paused" if gh.paused else "failed" if isinstance(refreshed_prs, Err) else "ok",
                     error=asdict(refreshed_prs.error) if isinstance(refreshed_prs, Err) else None)
    merges = dict(saved_merges.value.merges) if isinstance(saved_merges, Ok) else {}
    merge_results = []
    # A pair whose PR is closed or merged is not a merge candidate; a pair with no PR yet is still
    # checked, because dispatch verification of a ready step needs its merge result.
    open_pairs = {(pr.head, pr.base) for pr in prs if pr.state in (PrState.OPEN, PrState.DRAFT)}
    ended_pairs = {(pr.head, pr.base) for pr in prs if pr.state in (PrState.MERGED, PrState.CLOSED)} - open_pairs
    listed = remotes.value if isinstance(remotes, Ok) else state.remotes if remotes is None else None
    remote_branches = None if listed is None else {remote.branch for remote in listed}
    if due:
        for branch, target in due.merges:
            if (branch, target) in ended_pairs:
                if (cached := merges.get(branch)) is not None and cached.target == target:
                    del merges[branch]
                continue
            missing = None if remote_branches is None or (branch, target) not in open_pairs else (
                MergeState.HEAD_NOT_PUSHED if branch not in remote_branches else
                MergeState.BASE_DELETED if target not in remote_branches else None
            )
            if missing is not None:
                merges[branch] = Merge(branch, target, missing, (), (missing.value,), now)
                merge_results.append(Ok(merges[branch]))
                continue
            checked = remotes if isinstance(remotes, Err) else git_source.merge(code_root, branch, target)
            ref_missing = checked.error if isinstance(checked, Err) and isinstance(checked.error, NotFound) and (
                checked.error.what in (f"origin/{branch}", f"origin/{target}")) else None
            if not isinstance(remotes, Err) and ref_missing is None:
                checked = logger.result("git.merge", checked, branch=branch, target=target)
                merge_results.append(checked)
            if isinstance(checked, Ok):
                merges[branch] = checked.value
            elif ref_missing is not None:
                # A ref missing on origin is an unpushed branch or deleted base, not a failed merge check.
                missing = MergeState.HEAD_NOT_PUSHED if ref_missing.what == f"origin/{branch}" else MergeState.BASE_DELETED
                merges[branch] = Merge(branch, target, missing, (), (missing.value,), now)
                merge_results.append(Ok(merges[branch]))
            else:
                unavailable = Merge(branch, target, MergeState.ERROR, (), (verification_reason(checked.error),), now)
                merges[branch] = unavailable
                merge_results.append(Ok(unavailable))
    stack_prs = _stack_input(config, cached_stack, stack_read)
    inputs = Inputs(now, config.lead, repo.value, config.interval_s, phase, members, tasks, worktrees, remotes, tuple(merge_results) if due else tuple(Ok(item) for item in merges.values()), prs_input, gh, task_beads, closed_tasks, stack_prs=stack_prs)
    sanity_host = _sanity_host(config, phase, logger)
    snapshot, actions, next_state = model.tick(inputs, state, now, partial(atm_bd.dispatch_spec, templates=file.value.templates,
                                                                          sanity=sanity_host))
    if not snapshot.phase:
        snapshot = replace(snapshot, phase=config.phase)  # the header keeps the configured id when the phase read failed
    steps = {item.bead_id: item for item in phase.value.steps} if isinstance(phase, Ok) else {}
    for section in snapshot.sections:
        if section.label == "Held":
            for held in section.rows:
                held_step = steps.get(held.bead_id)
                logger.event(
                    "hold", task_ids=[held.bead_id], recipient=held_step.assignee or config.lead if held_step else config.lead,
                    outcome="held", reason=held.reason,
                )
    prs_file = PrsFile(prs_read_at, gh, tuple(prs), attempted_at=attempted_at,
                       stack_number=config.stack_number if cached_stack is not None else None, stack_prs=cached_stack)

    def persist(store: StateStore):
            reported, action_errors = _run_actions(config, actions, store, now, logger)
            errors = [*store.load_errors, *closed_errors, *action_errors, *refresh_errors]
            durable = state if config.dry_run else _durable_state(state, next_state, actions, reported)
            reported_sent = (*state.sent, *reported)[-5:]
            for written in (store.write_merges(MergeFile(now, merges)), store.write_prs(prs_file), store.write_state(durable)):
                if isinstance(written, Err): errors.append(written.error)
            for error in (*snapshot.errors, *errors):
                logger.error(error)
            logger.finish(actions=len(actions))
            errors.extend(logger.errors)
            persisted = replace(snapshot, sent=reported_sent, errors=_unique((*snapshot.errors, *errors)), files={"snapshot": str(store.directory / "snapshot.json"), "state": str(store.directory / "state.json")})
            persisted = _write_snapshot(store, persisted, logger)
            return StepResult(persisted, durable, reported, sanity, quality, logger.failed_reads,
                              prs_read_at=prs_read_at if prs_input is not None else None)
    return persist(store)
