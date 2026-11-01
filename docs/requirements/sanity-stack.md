# sanity-stack (subagent of dev-sanity)

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

Dealing with the race is the most important thing this agent does: two devs
cut from the same top both pass sanity, and only one can be the next layer.
The subagent exists for the cases where the three link commands do not go
through; when they always work, dev-sanity runs them itself.

### The stack bead (ledger and lock)

1. One bead per stack, `<prefix>-phase-<x>.stack`, child of the phase epic, created by the lead with the integration branch and closed when the stack lands. Its metadata is the whole stack: `trunk`, `stack_number`, and `layers`, an ordered list of `{branch, pr, head, base, linked}`; the last entry is the top. It is the only record of layer order, and it works with GitHub unreachable.
2. The claim is the lock: `bd update <stack bead> --claim` before any stack write, by sanity-stack and by the lead alike (unstack, restack, land). Release is the compare-and-set `bd update <stack bead> --if-assignee "$ATM_IDENTITY" --status open --assignee ""`. The holder keeps its claim alive with `bd heartbeat` (lease: a script constant, 900 s). A refused claim returns `lock_timeout` immediately; recovery of a stale claim belongs to the phase lead.

### Input (fenced JSON from dev-sanity)

3. The input carries `checked_bead`, `branch`, `pr_number`, `commit`, `stack_bead` and `budget`; provider operations determine the available link behavior.

### Procedure (one next-top layer per spawn)

4. Make one claim attempt on the stack bead. If another agent holds it, return `lock_timeout` immediately; do not poll or wait.
5. Under the lock validate the ledger, locate the unique non-draft PR at the pinned head with the provider, recheck the claim, fetch origin, and verify the ledger top and Git ancestry. Set the PR base through the provider. Record the first layer as pending; create the hosted stack with the first two ordered PRs and append later layers through the provider. The provider output supplies the stack number.
6. Release the lock. Return fenced JSON: `stacked` (with the new top and `stack_number`), `rebase_required`, `lock_timeout` or `stack_failed`, with the evidence.
7. If ancestry fails, return `rebase_required` without linking or writing; the recovery gives the current top and rebase and push commands.
8. A link that fails for a stack reason (stale local tracking, a stack number minted anew, a PR retargeted or closed, a non-linear stack): repair with the `sc-gh-stack` recipes within this one layer, never rewriting a layer that has children; unrecoverable: `stack_failed` to the lead as stack owner, lock released, ledger unchanged.
9. The ledger is authoritative. If hosted linking succeeded but the ledger write failed, fail closed and ask the lead to recover the stack number with the provider checkout command and repair the ledger under the lock.

### Lock timeout (never blocks the team, never a human)

10. If the one claim attempt is refused, return `lock_timeout` immediately with the stack bead holder and claim time; do not query ATM tasks.
11. A lock_timeout is reported mechanically to the phase lead as stack owner. The sanity task has already closed; it is never held active, refused or changed to FAIL for a stack outcome. The lead owns any subsequent retry or lease recovery under item 2.

### dev-sanity's side

12. After its selected PASS closes, dev-sanity hands the generated stack input to sanity-stack. Handoffs are serialized one at a time, independently of sanity close order; an inline sanity-stack-link invocation follows the same locking procedure.
13. The sanity close hook runs on the selected verdict before linking and accepts an absent stack result. An already-linked layer at the same pinned commit returns stacked, even below the top. rebase_required, lock_timeout and stack_failed notify the phase lead and leave the sanity task closed; none increments sanity_round. The lead owns further dev redispatch or stack repairs.
