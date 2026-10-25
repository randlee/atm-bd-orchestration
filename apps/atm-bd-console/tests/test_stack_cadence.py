"""Hosted-stack membership: trunk check, poll cadence, quota gate, and no false stale alert.

Every test drives the runner or the GitHub source with controlled inputs: a fixed
clock, a fake command boundary and a real on-disk state store. Nothing sleeps.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Self, cast

import pytest
from contract_samples import BEAD, CONFIG, PHASE_FILE, REPO_CONFIG

from atm_bd_console import github_source, runner
from atm_bd_console.command import Output
from atm_bd_console.enums import CiState, PrState, SprintState
from atm_bd_console.result import CommandFailed, ConfigInvalid, Err, Ok
from atm_bd_console.state import acquire_lock
from atm_bd_console.types import Due, GhStatus, Phase, PullRequest, Sprint, State, Step

T0 = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
REPO = "owner/repo"
TRUNK = "integrate/phase-bk"
STACK_ARGV = github_source.stack_argv(REPO, 7)
QUOTA_ARGV = github_source.quota_argv(REPO)
STATE = State((), None, None, None, None, (), (), {})


def stack_body(numbers, base=TRUNK):
    return {"number": 7, "base": {"ref": base}, "pull_requests": [{"number": number} for number in numbers]}


def run_returning(body, calls):
    def run(argv, *_args, **_kwargs):
        calls.append(argv)
        return Ok(Output(0, json.dumps(body)))
    return run


# --- item 2: the configured trunk must be the hosted stack's base -----------------------------------------

def test_stack_on_the_configured_trunk_is_read(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(github_source.command, "run", run_returning(stack_body((1, 2)), calls))

    assert github_source.stack_membership("graphql", "/code", REPO, 7, TRUNK) == Ok((1, 2))
    assert calls == [STACK_ARGV]


def test_stack_on_another_base_is_refused_as_misconfigured(monkeypatch) -> None:
    monkeypatch.setattr(github_source.command, "run", run_returning(stack_body((1, 2), base="main"), []))

    result = github_source.stack_membership("graphql", "/code", REPO, 7, TRUNK)

    assert isinstance(result, Err) and isinstance(result.error, ConfigInvalid)
    assert (result.error.key, result.error.value) == ("console.stack.trunk", repr("main"))


# --- item 3: quota gate --------------------------------------------------------------------------------------

def test_stack_read_obeys_the_quota_threshold(monkeypatch) -> None:
    calls: list = []
    low = {"resources": {"graphql": {"remaining": 100, "limit": 5000, "reset": int((T0 + timedelta(hours=1)).timestamp())}}}

    def run(argv, *_args, **_kwargs):
        calls.append(argv)
        return Ok(Output(0, json.dumps(low if argv == QUOTA_ARGV else stack_body((1,)))))

    monkeypatch.setattr(github_source.command, "run", run)
    budget = github_source.Budget("graphql", "/code", 50, 600, T0, GhStatus("graphql", None, None, None, False), REPO)

    result = github_source.stack_membership("graphql", "/code", REPO, 7, TRUNK, budget)

    assert isinstance(result, Err) and isinstance(result.error, CommandFailed)
    assert calls == [QUOTA_ARGV], "the stack endpoint must not be called below the quota threshold"
    assert budget.status.paused is True


# --- items 3 and 4: runner cadence and the stale alert ---------------------------------------------------------

def _step(number: int) -> Step:
    return Step(
        bead_id=f"atm-bk-{number}", sprint=f"atm-bk-{number}", kind="dev", quick_fix=False, anchor=False,
        status=SprintState.IN_PROGRESS, ready=False, assignee="dev", branch=f"sprint/bk-{number}",
        target=TRUNK if number == 1 else f"sprint/bk-{number - 1}", worktree=f"/worktrees/sprint/bk-{number}",
        layer=number, difficulty="normal", tag=f"bk-{number}", top_epic=PHASE_FILE.root_id, claimed_at=None,
        closed_at=None, title=f"bk-{number}", checked_bead=None, sprint_bead=None, qa_round=None, carry_forward=None,
    )


def _pr(number: int) -> PullRequest:
    base = TRUNK if number == 1 else f"sprint/bk-{number - 1}"
    return PullRequest(number, f"https://x/{number}", f"sprint/bk-{number}", base, f"sha{number}", CiState.PASS, (),
                       PrState.OPEN)


PHASE = Phase(PHASE_FILE.root_id, "phase:bk", "Phase BK", False,
              tuple(Sprint(f"atm-bk-{n}", f"bk-{n}", n, f"sprint/bk-{n}", TRUNK, "phase-bk", (), False, 0)
                    for n in (1, 2, 3)),
              tuple(_step(n) for n in (1, 2, 3)), ())


class World:
    """GitHub as the runner sees it: the linked stack and the PR list, both changeable between ticks."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, phase_file=PHASE_FILE, lock_id: str | None = None) -> None:
        self.file = phase_file
        # The console locks its state directory as atm-phase-<x> (cli.py), whatever the phase file's root id is.
        self.lock_id = lock_id or phase_file.root_id
        self.root_closed = False
        self.now = T0
        self.linked: tuple[int, ...] = (1, 2)
        self.prs_fail = False
        self.stack_error = None
        self.calls: list[str] = []
        world = self

        class Clock(datetime):
            @classmethod
            def now(cls, tz: tzinfo | None = None) -> Self:
                return cast(Self, world.now)

        def root_bead():
            return replace(BEAD, id=world.file.root_id,
                           status=SprintState.CLOSED if world.root_closed else SprintState.OPEN)
        monkeypatch.setattr(runner, "datetime", Clock)
        monkeypatch.setattr(runner, "create_console_logger", lambda *_: Err(CommandFailed("command_failed", (), 1, "", "")))
        monkeypatch.setattr(runner.atm_bd, "phase_file", lambda *_: Ok(world.file))
        monkeypatch.setattr(runner.atm_bd, "repo_config", lambda *_: Ok(REPO_CONFIG))
        monkeypatch.setattr(runner.beads_source, "show",
                            lambda ids: Ok((root_bead(),) if world.file.root_id in ids else ()))
        monkeypatch.setattr(runner.beads_source, "open_rows", lambda *_: Ok(runner.beads_source.BeadRows((), ())))
        monkeypatch.setattr(runner.beads_source, "ready", lambda *_: Ok(()))
        monkeypatch.setattr(runner.atm_bd, "phase",
                            lambda *_: Ok(replace(PHASE, root_id=world.file.root_id, closed=world.root_closed)))
        monkeypatch.setattr(runner.atm_source, "members", lambda *_: Ok(()))
        monkeypatch.setattr(runner.atm_source, "tasks", lambda *_: Ok(()))
        monkeypatch.setattr(runner.git_source, "worktrees", lambda *_: Ok(()))
        monkeypatch.setattr(runner.model, "due", lambda *_: Due(False, (), True))

        def open_prs(mode, *_args, **_kwargs):
            world.calls.append("prs")
            if world.prs_fail:
                error = CommandFailed("command_failed", ("gh",), 1, "boom", "retry")
                return Err(error), GhStatus(mode, False, error, world.now, False)
            return Ok(tuple(_pr(n) for n in world.linked)), GhStatus(mode, True, None, world.now, False)

        def stack_membership(*_args, **_kwargs):
            world.calls.append("stack")
            return Err(world.stack_error) if world.stack_error is not None else Ok(world.linked)

        monkeypatch.setattr(runner.github_source, "open_prs", open_prs)
        monkeypatch.setattr(runner.github_source, "stack_membership", stack_membership)


@pytest.fixture
def world(monkeypatch):
    return World(monkeypatch)


def tick(world: World, tmp_path, state=STATE, force_github=False, stack_number: int | None = 7):
    config = replace(CONFIG, github="graphql", repo_root=str(tmp_path), github_repo=REPO, github_poll_interval_s=600,
                     stack_number=stack_number, stack_trunk=TRUNK)
    locked = acquire_lock(tmp_path, world.lock_id)
    assert isinstance(locked, Ok)
    with locked.value as store:
        snapshot, next_state = runner.step(config, state, force_github, store)
    return snapshot, next_state


def keys(snapshot) -> set[str]:
    return {problem.key for problem in snapshot.problems}


def test_stack_membership_is_read_on_the_github_poll_cadence_only(world, tmp_path) -> None:
    for seconds in (0, 60, 599, 600):
        world.now = T0 + timedelta(seconds=seconds)
        tick(world, tmp_path)

    assert world.calls.count("stack") == 2, "one membership read per GitHub poll, none between polls"
    # Membership first, then the PR list, in the same refresh: every linked PR predates the PR read.
    assert world.calls == ["stack", "prs", "stack", "prs"]


def test_a_new_link_between_polls_raises_no_false_stale_alert(world, tmp_path) -> None:
    snapshot, _ = tick(world, tmp_path)
    assert snapshot.top_pr == 2 and "stack_snapshot:stale" not in keys(snapshot)

    world.linked = (1, 2, 3)  # a layer is linked on GitHub between polls
    world.now = T0 + timedelta(seconds=60)
    snapshot, _ = tick(world, tmp_path)
    assert "stack_snapshot:stale" not in keys(snapshot), keys(snapshot)
    assert snapshot.top_pr == 2, "between polls the cached membership and PR list agree on the previous top"

    world.now = T0 + timedelta(seconds=600)
    snapshot, _ = tick(world, tmp_path)
    assert "stack_snapshot:stale" not in keys(snapshot)
    assert snapshot.top_pr == 3


def test_a_failed_pr_refresh_keeps_the_cached_membership_with_its_pr_list(world, tmp_path) -> None:
    tick(world, tmp_path)
    world.linked, world.prs_fail = (1, 2, 3), True
    world.now = T0 + timedelta(seconds=600)

    snapshot, _ = tick(world, tmp_path)

    assert "stack_snapshot:stale" not in keys(snapshot), keys(snapshot)
    assert snapshot.top_pr == 2


def test_an_unreadable_stack_stays_loud_between_polls_without_rereading(world, tmp_path) -> None:
    tick(world, tmp_path)
    world.stack_error = ConfigInvalid("config_invalid", "console.stack.trunk", repr("main"), "fix the stack")
    for seconds in (600, 660):
        world.now = T0 + timedelta(seconds=seconds)
        snapshot, _ = tick(world, tmp_path)
        assert snapshot.top_pr is None
        assert "stack_membership:unavailable" in keys(snapshot)
    assert world.calls.count("stack") == 2


# --- the real quota gate, end to end: every GitHub command the runner sends is recorded ----------------------

def test_core_quota_below_threshold_skips_the_stack_read_in_graphql_mode(monkeypatch) -> None:
    calls: list = []
    resources = {"graphql": {"remaining": 4000, "limit": 5000, "reset": int((T0 + timedelta(hours=1)).timestamp())},
                 "core": {"remaining": 100, "limit": 5000, "reset": int((T0 + timedelta(hours=1)).timestamp())}}

    def run(argv, *_args, **_kwargs):
        calls.append(argv)
        return Ok(Output(0, json.dumps({"resources": resources} if argv == QUOTA_ARGV else stack_body((1,)))))

    monkeypatch.setattr(github_source.command, "run", run)
    budget = github_source.Budget("graphql", "/code", 50, 600, T0, GhStatus("graphql", None, None, None, False), REPO)

    result = github_source.stack_membership("graphql", "/code", REPO, 7, TRUNK, budget)

    assert isinstance(result, Err) and github_source.throttled(result.error)
    assert calls == [QUOTA_ARGV], "a REST call is not sent while the REST (core) quota is below the threshold"
    assert budget.status.paused is False, "low core quota does not pause the graphql PR read"


class GitHub:
    """The gh boundary: rate_limit, the GraphQL PR list and the stack endpoint, with settable quotas."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[str] = []
        self.linked: tuple[int, ...] = (1, 2)
        self.remaining = {"graphql": 4000, "core": 4000}
        reset = int((T0 + timedelta(hours=1)).timestamp())
        github = self
        real_run = github_source.command.run

        def run(argv, *args, **kwargs):
            argv = tuple(argv)
            if argv[:1] != ("gh",):
                return real_run(argv, *args, **kwargs)  # local git plumbing only; no GitHub request
            if argv == QUOTA_ARGV:
                github.calls.append("rate_limit")
                body = {"resources": {name: {"remaining": value, "limit": 5000, "reset": reset}
                                      for name, value in github.remaining.items()}}
            elif argv == STACK_ARGV:
                github.calls.append("stack")
                body = stack_body(github.linked)
            elif argv[:3] == ("gh", "api", "graphql"):
                github.calls.append("graphql")
                nodes = [{"number": n, "url": f"https://x/{n}", "state": "OPEN", "isDraft": False,
                          "headRefName": f"sprint/bk-{n}", "baseRefName": TRUNK if n == 1 else f"sprint/bk-{n - 1}",
                          "headRefOid": f"sha{n}", "commits": {"nodes": []}} for n in github.linked]
                repository: dict = {"pullRequests": {
                    "totalCount": len(nodes), "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}}
                # The phase-head history and stack-number lookups: every PR here is open, so no history;
                # each linked number resolves to its open PR.
                named = [argv[index + 1].split("=", 1) for index in range(len(argv) - 1) if argv[index] in ("-f", "-F")]
                for key, value in named:
                    if re.fullmatch(r"h\d+", key):
                        repository[key] = {"totalCount": 0, "nodes": []}
                    elif re.fullmatch(r"n\d+", key):
                        repository[key] = next(node for node in nodes if node["number"] == int(value))
                body = {"data": {"repository": repository}}
            else:
                raise AssertionError(f"unexpected command {argv}")
            return Ok(Output(0, json.dumps(body)))

        monkeypatch.setattr(github_source.command, "run", run)


@pytest.fixture
def github(world, monkeypatch):
    # The World fixture patches the runner's reads; undo its fakes for the GitHub source so the real
    # Budget, open_prs and stack_membership run against the recorded gh boundary.
    monkeypatch.setattr(runner.github_source, "open_prs", REAL_OPEN_PRS)
    monkeypatch.setattr(runner.github_source, "stack_membership", REAL_STACK_MEMBERSHIP)
    return GitHub(monkeypatch)


REAL_OPEN_PRS = github_source.open_prs
REAL_STACK_MEMBERSHIP = github_source.stack_membership


def ticks(world, tmp_path, seconds):
    snapshots = []
    for value in seconds:
        world.now = T0 + timedelta(seconds=value)
        snapshots.append(tick(world, tmp_path)[0])
    return snapshots


EVERY_TICK_FOR_21_MINUTES = range(0, 1260, 60)


def test_normal_quota_sends_exactly_one_refresh_per_poll_interval(world, github, tmp_path) -> None:
    ticks(world, tmp_path, EVERY_TICK_FOR_21_MINUTES)

    # 21 one-minute ticks, polls due at 0s, 600s and 1200s; nothing is sent between polls.
    assert github.calls == ["rate_limit", "stack", "rate_limit", "graphql"] * 3


def test_low_graphql_quota_sends_one_quota_check_then_nothing_until_reset(world, github, tmp_path) -> None:
    github.remaining["graphql"] = 100

    snapshots = ticks(world, tmp_path, EVERY_TICK_FOR_21_MINUTES)

    assert github.calls == ["rate_limit"], "below the threshold no stack, PR or check-run call is ever sent"
    assert all(snapshot.gh.paused for snapshot in snapshots)


def test_low_core_quota_keeps_the_cached_membership_and_reports_the_skip_once(world, github, tmp_path) -> None:
    ticks(world, tmp_path, (0,))
    github.calls.clear()
    github.remaining["core"] = 100
    github.linked = (1, 2, 3)

    snapshots = ticks(world, tmp_path, range(600, 1200, 60))

    assert github.calls == ["rate_limit", "rate_limit", "graphql"], "the REST stack call is skipped, the PR read runs"
    skipped = [index for index, snapshot in enumerate(snapshots)
               if any(github_source.throttled(error) for error in snapshot.errors)]
    assert skipped == [0], "the skipped membership read is reported on its poll only"
    for snapshot in snapshots:
        assert not {"stack_membership:unavailable", "stack_snapshot:stale"} & keys(snapshot), keys(snapshot)
