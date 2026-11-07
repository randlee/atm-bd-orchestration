"""Pure canonical stack selection shared by the console and its queue report."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta

from .prs import active_pr
from .result import Err, NotFound, Ok, ParseFailed, Result
from .types import PrsFile, PullRequest


def stack_topology(
    prs: tuple[PullRequest, ...],
    stack_prs: Result[tuple[int, ...]] | None,
    stack_ledger: Result[tuple[int, ...]] | None,
    *, layers: Mapping[str, int | None] | None = None,
) -> Result[PullRequest | None]:
    """Membership and ledger must agree; phase ownership only supplies the unconfigured fallback."""
    if isinstance(stack_ledger, Err):
        return stack_ledger
    if isinstance(stack_prs, Err):
        return stack_prs
    fix = "run the console tick and verify the stack ledger and hosted membership"
    if stack_prs is None and stack_ledger is None:
        projected = tuple(pr for pr in prs if layers is not None and pr.head in layers)
        bases = {pr.base for pr in projected}
        candidates = [(layers[pr.head], pr) for pr in projected
                      if layers is not None and active_pr(pr) and pr.head not in bases and layers[pr.head] is not None]
        return Ok(max(candidates, key=lambda pair: (pair[0], pair[1].number))[1] if candidates else None)
    if stack_ledger is None:
        return Err(NotFound("not_found", "STACK.LEDGER_UNREAD: stack ledger was not read", fix))
    if stack_prs is None:
        return Err(NotFound("not_found", "STACK.MEMBERSHIP_UNREAD: hosted stack membership was not read", fix))
    membership = stack_prs.value
    if membership != stack_ledger.value:
        return Err(ParseFailed("parse_failed", "STACK.MISMATCH",
                               f"ledger membership {stack_ledger.value}, hosted membership {membership}", fix))
    if not membership:
        return Ok(None)
    by_number = {pr.number: pr for pr in prs if active_pr(pr)}
    missing = tuple(number for number in membership if number not in by_number)
    if missing:
        return Err(NotFound("not_found", f"STACK.SNAPSHOT_MISSING: canonical members {missing} absent from the active PR snapshot", fix))
    return Ok(by_number[membership[-1]])


def fresh_prs(loaded: Result[PrsFile], now: datetime, interval_s: int) -> Result[PrsFile]:
    """Keep absence, corruption and age distinct without acquiring any hosted input."""
    fix = "run the console tick to refresh prs.json"
    if isinstance(loaded, Err):
        if isinstance(loaded.error, NotFound):
            return Err(NotFound("not_found", f"PRS.MISSING: {loaded.error.what}", fix))
        return Err(ParseFailed("parse_failed", "PRS.UNREADABLE", str(loaded.error), fix))
    if now - loaded.value.read_at > timedelta(seconds=2 * interval_s):
        return Err(ParseFailed("parse_failed", "PRS.STALE", f"PR snapshot read at {loaded.value.read_at.isoformat()} is older than two console intervals", fix))
    return loaded
