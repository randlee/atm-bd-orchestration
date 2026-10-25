"""Hosted-stack membership: trunk check, poll cadence, quota gate, and no false stale alert.

Every test drives the runner or the GitHub source with controlled inputs: a fixed
clock, a fake command boundary and a real on-disk state store. Nothing sleeps.
"""

from __future__ import annotations

import json
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

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

        root = replace(BEAD, id=PHASE_FILE.root_id, status=SprintState.OPEN)
        monkeypatch.setattr(runner, "datetime", Clock)
        monkeypatch.setattr(runner, "create_console_logger", lambda *_: Err(CommandFailed("command_failed", (), 1, "", "")))
        monkeypatch.setattr(runner.atm_bd, "phase_file", lambda *_: Ok(PHASE_FILE))
        monkeypatch.setattr(runner.atm_bd, "repo_config", lambda *_: Ok(REPO_CONFIG))
        monkeypatch.setattr(runner.beads_source, "show", lambda ids: Ok((root,) if PHASE_FILE.root_id in ids else ()))
        monkeypatch.setattr(runner.beads_source, "open_rows", lambda *_: Ok(runner.beads_source.BeadRows((), ())))
        monkeypatch.setattr(runner.beads_source, "ready", lambda *_: Ok(()))
        monkeypatch.setattr(runner.atm_bd, "phase", lambda *_: Ok(PHASE))
        monkeypatch.setattr(runner.atm_source, "members", lambda *_: Ok(()))
        monkeypatch.setattr(runner.atm_source, "tasks", lambda *_: Ok(()))
        monkeypatch.setattr(runner.git_source, "worktrees", lambda *_: Ok(()))
        monkeypatch.setattr(runner.model, "due", lambda *_: Due(False, (), True))

        def open_prs(mode, *_args):
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


def tick(world: World, tmp_path, state=STATE):
    config = replace(CONFIG, github="graphql", repo_root=str(tmp_path), github_repo=REPO, github_poll_interval_s=600,
                     stack_number=7, stack_trunk=TRUNK)
    locked = acquire_lock(tmp_path, PHASE_FILE.root_id)
    assert isinstance(locked, Ok)
    with locked.value as store:
        snapshot, next_state = runner.step(config, state, False, store)
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
