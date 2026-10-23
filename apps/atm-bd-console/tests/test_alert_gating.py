"""Deterministic tests for the two CONSOLE-STALE alert defects.

Defect 1: `_pr_rows` selects the "top" PR as the first active PR whose head is
not another PR's base, in GitHub tuple order. A superseded lower-layer PR that
is still open can therefore win over the real stack top, and the alert then
advises editing that (possibly frozen) branch.

Defect 2: the `missing_pr:` predicate never consults `step.ready`/dependencies,
so a not-ready step (blocked behind an open dependency) whose branch was pushed
still gets "open a PR" advice.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from atm_bd_console.enums import CiState, PrState, SprintState
from atm_bd_console.model import tick
from atm_bd_console.result import Err, NotFound, Ok
from atm_bd_console.types import GhStatus, Inputs, PullRequest, RemoteRef, RepoConfig, Sprint, State, Step

NOW = datetime(2026, 10, 23, 19, 0, tzinfo=UTC)
REPO = RepoConfig("atm", "dev-sanity", "quality-mgr", "/repo", "/worktrees", "just lint", "/policy", (), "/plans")
STATE = State((), None, None, None, None, (), (), {})


def step(bead_id: str, sprint_id: str, *, layer: int | None, branch: str, target: str, **changes) -> Step:
    value = Step(
        bead_id=bead_id, sprint=sprint_id, kind="dev", quick_fix=False, anchor=False,
        status=SprintState.OPEN, ready=False, assignee="dev", branch=branch, target=target,
        worktree=f"/worktrees/{branch}", layer=layer,  # type: ignore[arg-type]
        difficulty="normal", tag=sprint_id,
        top_epic="atm-phase-bk", claimed_at=None, closed_at=None, title=bead_id,
        checked_bead=None, sprint_bead=None, qa_round=None, carry_forward=None,
    )
    from dataclasses import replace
    return replace(value, **changes)


def sprint(number: int, depends_on=()) -> Sprint:
    return Sprint(
        f"atm-bk-{number}", f"bk-{number}", number, f"sprint/bk-{number}", "sprint/bk-1",
        "phase-bk", depends_on, False, 0,
    )


def make_phase(*steps: Step, sprints):
    from atm_bd_console.types import Phase
    return Phase("atm-phase-bk", "phase-bk", "Phase BK", False, tuple(sprints), tuple(steps), ())


def inputs(value, **changes) -> Inputs:
    original = Inputs(
        NOW, "solar", REPO, 60, Ok(value), Ok(()), Ok(()), Ok(()), Ok(()), (), Ok(()),
        GhStatus("graphql", True, None, NOW, False), Ok(()), Ok(()),
    )
    from dataclasses import replace
    return replace(original, **changes)


def render(context):
    raise AssertionError(f"unexpected dispatch: {context.step.bead_id}")


def pr(number: int, head: str, base: str, *, ci: CiState = CiState.PASS, state: PrState = PrState.OPEN) -> PullRequest:
    return PullRequest(number, f"https://x/{number}", head, base, f"sha{number}", ci, (), state)


def test_top_pr_is_canonical_stack_top_not_open_lower_layer() -> None:
    """A stale open lower-layer PR must not be selected as the stack top.

    The superseded fix branch is not the base of the current top branch, so the
    stack-graph test (head not in bases) admits BOTH. Selection must then follow
    stack layer order, not tuple order.
    """
    value = make_phase(
        step("atm-bk-9", "atm-bk-9", layer=1, branch="sprint/bk-9", target="main"),
        step("atm-bk-9-fix", "atm-bk-9", layer=1, kind="fix", branch="fix/bk-9-qa1-f5-1",
             target="sprint/bk-9"),
        step("atm-bk-10", "atm-bk-10", layer=2, branch="sprint/bk-10", target="sprint/bk-9"),
        sprints=(sprint(1), sprint(2)),
    )
    # #2202 (superseded, lower layer) appears first; #2203 is the current top.
    prs = Ok((
        pr(2202, "fix/bk-9-qa1-f5-1", "sprint/bk-9", ci=CiState.FAIL_WINDOWS),
        pr(2203, "sprint/bk-10", "sprint/bk-9"),
    ))

    snapshot, _, _ = tick(inputs(value, prs=prs), STATE, NOW, render)

    assert snapshot.top_pr == 2203, f"expected canonical top 2203, got {snapshot.top_pr}"


def test_unknown_layer_metadata_never_authorizes_a_frozen_branch_edit() -> None:
    """With no layer metadata, refuse to name a top instead of guessing by PR number.

    Solar's guard: arbitrary PR-number fallback must not silently authorize
    editing a frozen lower layer.
    """
    value = make_phase(
        step("atm-bk-1", "atm-bk-1", layer=None, branch="sprint/bk-1", target="main"),
        step("atm-bk-2", "atm-bk-2", layer=None, branch="sprint/bk-2", target="main"),
        sprints=(sprint(1), sprint(2)),
    )
    prs = Ok((
        pr(2202, "sprint/bk-1", "main", ci=CiState.FAIL_WINDOWS),
        pr(2203, "sprint/bk-2", "main"),
    ))

    snapshot, actions, _ = tick(inputs(value, prs=prs), STATE, NOW, render)

    assert snapshot.top_pr is None
    assert not any(problem.key.startswith("top_ci:") for problem in snapshot.problems)
    for action in actions:
        assert "fix them on" not in getattr(action, "text", "")


def test_unlinked_higher_layer_checkpoint_is_not_selected_as_top() -> None:
    """Hosted-stack membership beats layer order: an unlinked checkpoint loses.

    Defect 3: a checkpoint/sprint PR claiming a higher layer but not registered
    and linked in the hosted stack must never become the top.
    """
    value = make_phase(
        step("atm-bk-26", "atm-bk-26", layer=26, branch="sprint/bk-26", target="main"),
        step("atm-bk-26-ckpt", "atm-bk-26", layer=2208, kind="sanity",
             branch="sprint/bk-26-ckpt", target="main"),
        sprints=(sprint(26),),
    )
    prs = Ok((
        pr(2206, "sprint/bk-26", "main"),
        pr(2208, "sprint/bk-26-ckpt", "main"),
    ))

    snapshot, _, _ = tick(inputs(value, prs=prs, stack_prs=Ok((2206,))), STATE, NOW, render)

    assert snapshot.top_pr == 2206, f"expected linked top 2206, got {snapshot.top_pr}"

    # Membership order is the SSOT: when the stack lists 2208 before 2206, 2206 is
    # the last linked entry and therefore the top, even though 2208 claims a
    # higher layer.
    snapshot, _, _ = tick(inputs(value, prs=Ok((pr(2206, "sprint/bk-26", "main"),
                                               pr(2208, "sprint/bk-26-ckpt", "main"))),
                              stack_prs=Ok((2208, 2206))), STATE, NOW, render)
    assert snapshot.top_pr == 2206, f"expected last-linked top 2206, got {snapshot.top_pr}"


def test_missing_pr_not_advised_for_not_ready_dependency_blocked_step() -> None:
    """A dependency-blocked (not ready) step must not get submit-PR advice."""
    value = make_phase(
        step("atm-bk-1", "atm-bk-1", layer=1, branch="sprint/bk-1", target="main"),
        # BK10: open/UNASSIGNED, in the dependent sprint, branch already pushed.
        step("atm-bk-10", "atm-bk-2", layer=2, branch="sprint/bk-10", target="sprint/bk-1",
             ready=False, assignee=None),
        sprints=(sprint(1), sprint(2, depends_on=("atm-bk-1",))),
    )
    remotes = Ok((RemoteRef("sprint/bk-10", "sha10"),))

    snapshot, actions, _ = tick(inputs(value, prs=Ok(()), remotes=remotes), STATE, NOW, render)

    keys = {problem.key for problem in snapshot.problems}
    assert not any(key.startswith("missing_pr:") for key in keys), keys
    assert not any("has no open PR" in action.text for action in actions)


def test_unreadable_membership_suppresses_top_and_reports_it() -> None:
    """Fail loud: an unreadable stack membership names no top and says so.

    Falling back to a layer rule here could re-crown an unlinked checkpoint,
    which is the exact hazard this fix exists to kill.
    """
    value = make_phase(
        step("atm-bk-26", "atm-bk-26", layer=26, branch="sprint/bk-26", target="main"),
        sprints=(sprint(26),),
    )
    prs = Ok((pr(2206, "sprint/bk-26", "main"),))
    failure = Err(NotFound("not_found", "gh", "stack 2180"))

    snapshot, _, _ = tick(inputs(value, prs=prs, stack_prs=failure), STATE, NOW, render)

    assert snapshot.top_pr is None
    assert "stack_membership:unavailable" in {problem.key for problem in snapshot.problems}
