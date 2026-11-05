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
    """Confirmed ledger and hosted membership beat layer order: an unlinked checkpoint loses.

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

    snapshot, _, _ = tick(inputs(value, prs=prs, stack_prs=Ok((2206,)), stack_ledger=Ok((2206,))), STATE, NOW, render)

    assert snapshot.top_pr == 2206, f"expected linked top 2206, got {snapshot.top_pr}"

    # When both sources list 2208 before 2206, 2206 is
    # the last linked entry and therefore the top, even though 2208 claims a
    # higher layer.
    snapshot, _, _ = tick(inputs(value, prs=Ok((pr(2206, "sprint/bk-26", "main"),
                                               pr(2208, "sprint/bk-26-ckpt", "main"))),
                              stack_prs=Ok((2208, 2206)), stack_ledger=Ok((2208, 2206))), STATE, NOW, render)
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


def test_snapshot_behind_stack_names_no_top_and_says_so() -> None:
    """A correct selector fed a stale candidate set must not emit yesterday's top.

    Third D1/D3 instance: membership advanced to #2211 but the polled PR snapshot
    still ended at #2208, so the alert named #2208 (the previous top) with
    frozen-edit advice.
    """
    value = make_phase(
        step("atm-bk-26", "atm-bk-26", layer=26, branch="sprint/bk-26", target="main"),
        step("atm-bk-27", "atm-bk-27", layer=27, branch="sprint/bk-27", target="main"),
        sprints=(sprint(26), sprint(27)),
    )
    # Snapshot only holds #2208; the stack's last entry is #2211, absent here.
    prs = Ok((pr(2208, "sprint/bk-26", "main"),))

    snapshot, _, _ = tick(inputs(value, prs=prs, stack_prs=Ok((2206, 2208, 2211)), stack_ledger=Ok((2206, 2208, 2211))), STATE, NOW, render)

    assert snapshot.top_pr is None
    assert any("#2211" in row.reason for section in snapshot.sections if section.label == "Diagnostics" for row in section.rows)


def test_empty_pr_snapshot_is_diagnostic_without_sending_a_batch() -> None:
    value = make_phase(sprints=())
    snapshot, actions, _ = tick(inputs(value, prs=Ok(()), stack_prs=Ok((99,)), stack_ledger=Ok((99,))), STATE, NOW, render)

    rows = [row for section in snapshot.sections if section.label == "Diagnostics" for row in section.rows]
    assert len(rows) == 1 and rows[0].bead_id == "atm-phase-bk.stack" and "#99" in rows[0].reason
    assert not any(action.kind == "batch" for action in actions)
    assert not any(problem.key == "stack_snapshot:stale" for problem in snapshot.problems)


def test_stack_read_errors_name_bead_and_explicit_fix() -> None:
    value = make_phase(sprints=())
    failure = Err(NotFound("not_found", "stack", "restore the stack"))
    snapshot, actions, _ = tick(inputs(value, stack_prs=failure, stack_ledger=failure), STATE, NOW, render)

    problems = [p for p in snapshot.problems if p.key in ("stack_ledger:unavailable", "stack_membership:unavailable")]
    assert len(problems) == 2
    assert all(p.bead_id == "atm-phase-bk.stack" and "Fix:" in p.text for p in problems)
    assert any(action.kind == "batch" and "atm-phase-bk.stack" in action.bead_ids for action in actions)


@pytest.mark.parametrize("ledger,hosted,expected", [
    (Err(NotFound("not_found", "metadata", "restore ledger")), Ok(()), "stack ledger unavailable"),
    (None, Ok(()), "stack ledger was not read"),
    (Ok(()), Err(NotFound("not_found", "hosted", "repair access")), "hosted stack membership is unreadable"),
    (Ok((1,)), Ok((2,)), "ledger top #1, hosted top #2"),
])
def test_each_outbound_stack_notice_contains_its_bead_id(ledger, hosted, expected) -> None:
    snapshot, actions, _ = tick(inputs(make_phase(sprints=()), prs=Ok(()), stack_prs=hosted, stack_ledger=ledger),
                                STATE, NOW, render)
    assert snapshot.problems
    batches = [action for action in actions if action.kind == "batch"]
    assert len(batches) == 1
    assert "atm-phase-bk.stack" in batches[0].text
    assert expected in batches[0].text
    assert "Fix:" in batches[0].text
