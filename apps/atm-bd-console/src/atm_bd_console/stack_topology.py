"""Pure canonical stack selection shared by the console and its queue report."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta

from .enums import StackReason
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
        return Err(NotFound("not_found", f"{StackReason.LEDGER_UNREAD}: stack ledger was not read", fix))
    if stack_prs is None:
        return Err(NotFound("not_found", f"{StackReason.MEMBERSHIP_UNREAD}: hosted stack membership was not read", fix))
    membership = stack_prs.value
    if membership != stack_ledger.value:
        return Err(ParseFailed("parse_failed", StackReason.MISMATCH,
                               f"ledger membership {stack_ledger.value}, hosted membership {membership}", fix))
    if not membership:
        return Ok(None)
    # Only the last canonical member decides the top. Lower members are frozen layers: merged, closed or
    # outside the snapshot is their normal life after a landing and never fails the stack.
    top_number = membership[-1]
    top = next((pr for pr in prs if pr.number == top_number), None)
    if top is None:
        return Err(NotFound("not_found", f"{StackReason.SNAPSHOT_MISSING}: canonical top #{top_number} absent from the PR snapshot", fix))
    if not active_pr(top):
        # A merged or closed top is a landed or abandoned stack: there is no live top, and that is distinct from an unread snapshot.
        return Err(ParseFailed("parse_failed", StackReason.TOP_INACTIVE,
                               f"canonical top #{top_number} ({top.head}) is {top.state}, not open", fix))
    return Ok(top)


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
