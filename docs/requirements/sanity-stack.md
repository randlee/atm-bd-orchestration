# sanity-stack (subagent of dev-sanity)

**ID Range:** REQ-SST-0001 through REQ-SST-0013  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-19  
**Last Updated:** 2026-10-26  
**Owner:** Rand Lee  

---

Dealing with the race is the most important thing this agent does: two devs
cut from the same top both pass sanity, and only one can be the next layer.
The subagent exists for the cases where the three link commands do not go
through; when they always work, dev-sanity runs them itself.

## REQ-SST-0001: The stack bead (ledger and lock)

**Status:** Draft  
### Requirement Statement

One bead per stack, `<prefix>-phase-<x>.stack`, child of the phase epic, created by the lead with the integration branch and closed when the stack lands. Its metadata is the whole stack: `trunk`, `stack_number`, and `layers`, an ordered list of `{branch, pr, head, base, linked}`; the last entry is the top. It is the only record of layer order, and it works with GitHub unreachable.


### Rationale

Two devs cut from the same top can both pass sanity, so layer order needs one record that does not depend on GitHub being reachable; the bead metadata ledger is that record and `sanity-stack-link` reads and writes it (CHANGELOG 0.19.x: serialized sanity linking and stack ledger, phase bj).

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd show` on the stack bead named `<prefix>-phase-<x>.stack` shows it as a child of the phase epic with metadata keys `trunk`, `stack_number` and `layers`.
- [ ] Each `layers` entry has exactly the keys `branch`, `pr`, `head`, `base` and `linked`, and the last entry is the current top.
- [ ] `sanity-stack-link` run with GitHub calls failing still reads the layer order from the bead metadata.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_three_passes_link_in_verdict_order`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_unlinked_recorded_layer_is_not_reported_as_already_stacked`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0002: The stack bead (ledger and lock)

**Status:** Draft  
### Requirement Statement

The claim is the lock: `bd update <stack bead> --claim` before any stack write, by sanity-stack and by the lead alike (unstack, restack, land). Release is the compare-and-set `bd update <stack bead> --if-assignee "$ATM_IDENTITY" --status open --assignee ""`. The holder keeps its claim alive with `bd heartbeat` (lease: a script constant, 900 s). A refused claim returns `lock_timeout` immediately; recovery of a stale claim belongs to the phase lead.


### Rationale

Concurrent writers to one stack ledger corrupt layer order, so every stack write goes through a bead claim as lock; a refused claim returns at once instead of blocking the team (commits 6495c1f33 'Integrate sanity PASS stack linking' and d3f30fda1 'Clarify sanity stack lock timeout handling').

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-stack-link` runs `bd update <stack bead> --claim` before its first stack write.
- [ ] After a write, `sanity-stack-link` releases with `bd update <stack bead> --if-assignee "$ATM_IDENTITY" --status open --assignee ""`, and the stack bead assignee is empty afterwards.
- [ ] A run that outlasts the controlled clock's lease interval calls `bd heartbeat` on the stack bead.
- [ ] A refused claim returns `lock_timeout` after exactly one claim attempt and no `bd reclaim` call.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_heartbeat_uses_controlled_clock`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failures_leave_ledger_and_release`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0003: Input (fenced JSON from dev-sanity)

**Status:** Draft  
### Requirement Statement

`checked_bead`, `branch`, `pr_number`, `commit`, `stack_bead` and `budget` (`full` or `lean`) are carried in the dev-sanity assignment's close context. The close hook copies explicit values and supplies `full` only when an override is absent. GraphQL out is detected and forces `lean`.


### Rationale

The sanity task has already closed when stacking runs, so the stack input must be generated from the assignment's close context; the budget field lets a GraphQL-exhausted host link without GraphQL (CHANGELOG: lean mode, `worktree_path` in the generated stack input).

### Success Criteria

**Acceptance Criteria:**

- [ ] The stack input file written for a PASS contains `checked_bead`, `branch`, `pr_number`, `commit`, `stack_bead` and `budget`, with `budget` equal to the close-context value (`lean` in the test).
- [ ] The close hook raises a `ValueError` naming `budget` when the close context has no `budget`.
- [ ] With `budget: full` and GraphQL remaining at 0, `sanity-stack-link` reports `mode` `lean` and `lean_reason` `graphql_remaining_0`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_stack_input_carries_assignment_budget_and_worktree_and_only_passes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_stack_input_requires_assignment_budget`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_mode_and_lean_cause_are_reported`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0004: Procedure (one next-top layer per spawn)

**Status:** Draft  
### Requirement Statement

Make one claim attempt on the stack bead. If another agent holds it, return `lock_timeout` immediately; do not poll or wait.


### Rationale

A sanity subagent that polled for a held lock would stall the dev-sanity handoff queue; the 'one claim attempt, return immediately' rule keeps stacking from blocking the team (agent text: 'do not wait for a person or retry').

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-stack-link` issues exactly one `bd update <stack bead> --claim` call per run.
- [ ] When that claim is refused, the result is `lock_timeout` and the controlled clock has not advanced.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0005: Procedure (one next-top layer per spawn)

**Status:** Draft  
### Requirement Statement

Under the lock, re-read and validate `layers` from the bead (never from the input), read the filtered REST pull list, and, when layers exist, fetch and reconcile the hosted chain. Validate the checked pull and re-read the bead to verify that the claim and ledger are unchanged; then fetch, select the current top (or trunk for an empty ledger), and verify `origin/<top.branch>` is an ancestor of `commit`. Reconciliation of a torn link must precede top selection, and the final fetch and ancestry check stay adjacent (lead ruling 2026-10-19 (bj-3 f9)). An already-recorded linked layer is checked as an idempotent replay. `full`: link every `linked: false` layer in order, then this PR as the new top (`gh stack link <stack_number> <pr>`; the first stack from layers 0 and 1 together with `--base <trunk>`), one `/sc-gh-stack-view`; `lean`: verify the PR base ref equals the top branch from the filtered REST pull list (number, base, head, sha, draft; never the raw body) and record `linked: false`; append the layer; write the metadata. The write is the commit point.


### Rationale

The bead ledger is the authority and the input is only a hint, so a stale or forged input cannot reorder layers; the ancestry check before linking stops a layer that is not built on the current top from being linked (fix commits c2f55957e 'Preserve stack ledger failures when selecting top' and 43bf51c85 'Reject unanchored hosted stack recovery').

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-stack-link` reads `layers` from the stack bead under the lock; a ledger top that moved after validation yields `stack_failed` with no write.
- [ ] A layer whose `origin/<top.branch>` is not an ancestor of `commit` returns `rebase_required` and `gh stack link` and `bd update --metadata` are not called.
- [ ] In `full` mode the run links every `linked: false` layer in order, then the new PR; layers 0 and 1 are linked together with `--base <trunk>`.
- [ ] In `lean` mode the run calls no `gh stack link` and no stacks API, and records the new layer with `linked: false`.
- [ ] A replay of an already recorded layer at the same commit returns `stacked` without a metadata write or a `gh stack link` call.
- [ ] A hosted-only torn link is re-derived into `layers` before the next top is selected.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_divergence_never_links_or_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_moved_ledger_top_fails_closed`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lean_uses_only_rest_and_defers_link`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_already_linked_lower_layer_at_pinned_commit_is_stacked`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_retry_recovers_hosted_only_torn_link`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_next_verdict_recovers_prior_hosted_only_torn_link`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0006: Procedure (one next-top layer per spawn)

**Status:** Draft  
### Requirement Statement

Release the lock. Return fenced JSON: `stacked` (with the new top and `stack_number`), `rebase_required`, `lock_timeout` or `stack_failed`, with the evidence.


### Rationale

The sanity task is already closed, so the only way the lead learns a stack outcome is the returned JSON and the mechanical notice; a fixed set of four results lets the lead and the close hook branch on it (CHANGELOG: workflow diagrams draw each of the four results).

### Success Criteria

**Acceptance Criteria:**

- [ ] After every run the stack bead assignee is empty (lock released).
- [ ] The printed result is one JSON object whose `result` is one of `stacked`, `rebase_required`, `lock_timeout` or `stack_failed`.
- [ ] A `stacked` result contains the new `top` and a `stack_number` key.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failures_leave_ledger_and_release`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lean_uses_only_rest_and_defers_link`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0007: Procedure (one next-top layer per spawn)

**Status:** Draft  
### Requirement Statement

Ancestor check fails: `rebase_required`, link nothing, write nothing. The result and the lead notice carry `next_steps`, the lead's options with their commands: `relink_in_git_order` when the layer is already in the top's history, else `rebase` (clean) and `dev_rebase` (conflicts), each ending in the re-check sanity bead. A third branch also on the old top is not this spawn's problem; it gets `rebase_required` when its own sanity passes.


### Rationale

A layer that is not built on the current top cannot be linked, and a bare 'rebase needed' left the lead guessing; CHANGELOG records that `rebase_required` now carries `next_steps` (`relink_in_git_order`, `rebase`, `dev_rebase`) with commands and the re-check sanity bead (commit 380b73150).

### Success Criteria

**Acceptance Criteria:**

- [ ] When the ancestor check fails the result is `rebase_required`, the bead metadata is unchanged and no `gh stack link` call is made.
- [ ] `next_steps` lists the options `rebase` and `dev_rebase`, where the first `rebase` step contains `git rebase origin/<top branch>` and the second step names `dev-sanity-bead.json.j2`.
- [ ] When the layer is already in the top's history, `next_steps` names `relink_in_git_order` instead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_divergence_never_links_or_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_rebase_required_names_rebase_options`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_rebase_required_inside_top_history_names_relink`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0008: Procedure (one next-top layer per spawn)

**Status:** Draft  
### Requirement Statement

A link that fails for a stack reason (stale local tracking, a stack number minted anew, a PR retargeted or closed, a non-linear stack): repair with the `sc-gh-stack` recipes within this one layer, never rewriting a layer that has children; unrecoverable: `stack_failed` to the lead as stack owner, lock released, ledger unchanged.


### Rationale

A link can fail on stack state (stale tracking, a re-minted stack number, a retargeted PR), and rewriting a layer with children would break the frozen-layer rule; failing closed to the lead keeps the ledger intact (the typed `stack_failed` result with `evidence` and `fix` fields).

### Success Criteria

**Acceptance Criteria:**

- [ ] A failed `gh stack link`, a failed compare-and-set or an ambiguous hosted stack returns `stack_failed`.
- [ ] After each such failure the bead metadata equals its value before the run and the stack bead assignee is empty.
- [ ] No recorded git or gh call in a `stack_failed` run is a force push.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failures_leave_ledger_and_release`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_duplicate_layer_refusal_has_repair`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_ghost_linked_layer_refusal_has_repair`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0009: Procedure (one next-top layer per spawn)

**Status:** Draft  
### Requirement Statement

`layers` on the bead is the authority; gh-stack's own catalog in the linking worktree (`.git/worktrees/<name>/gh-stack`) is a snapshot. The repair this agent owns, under the lock and before anything else, is re-deriving `layers` from the linked chain on GitHub (filtered REST pull list bases plus local ancestry) when the bead and the chain disagree (a torn link).


### Rationale

gh-stack's local catalog is a per-worktree snapshot that diverges from GitHub, so the bead is the authority and a torn link (hosted link made, ledger write lost) is repaired by re-deriving `layers` (commits 43bf51c85 'Reject unanchored hosted stack recovery' and 7433829de).

### Success Criteria

**Acceptance Criteria:**

- [ ] When the hosted chain holds a PR the bead lacks, the next run appends the missing layers to `layers` in chain order before selecting the top.
- [ ] That recovery performs no `gh stack link` call.
- [ ] A hosted chain that does not include the unlinked ledger anchor is refused and the bead metadata is unchanged.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_retry_recovers_hosted_only_torn_link`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_torn_link_recovers_held_children_in_order`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_hosted_ahead_must_include_the_unlinked_ledger_anchor`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0010: Lock timeout (never blocks the team, never a human)

**Status:** Draft  
### Requirement Statement

If the one claim attempt is refused, return `lock_timeout` immediately with the stack bead holder and claim time; do not query ATM tasks.


### Rationale

Polling for the holder, or querying ATM tasks, would make a busy lock hold up the sanity queue; the lead needs only who holds the claim and since when (commit 761b09784 'Keep holder task lookup best effort on lock timeout').

### Success Criteria

**Acceptance Criteria:**

- [ ] A refused claim yields a result with `result` `lock_timeout`, `holder` equal to the bead assignee and `claimed_at` equal to its `started_at`.
- [ ] That run makes one claim call and no `bd reclaim` call.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0011: Lock timeout (never blocks the team, never a human)

**Status:** Draft  
### Requirement Statement

A lock_timeout is reported mechanically to the phase lead as stack owner. The sanity task has already closed; it is never held active, refused or changed to FAIL for a stack outcome. The lead owns any subsequent retry or lease recovery under item 2.


### Rationale

A stack outcome is the lead's to resolve; counting it against the dev's sanity round or holding the task would penalize a PASS the dev earned (CHANGELOG: 'A sanity task stays closed when its layer is not stacked'; dev-sanity.md: no stack outcome increments sanity_round).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-stack-link` sends one notice to the phase lead on `lock_timeout`, `stack_failed` and `rebase_required`.
- [ ] That run makes no `atm task` call.
- [ ] `sanity_round` on the sanity bead is unchanged after a `rebase_required` followed by a re-check.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failed_post_close_handoff_notifies_lead_without_task_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_rebase_then_real_sanity_hook_preserves_round_and_hands_off`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0012: dev-sanity's side

**Status:** Draft  
### Requirement Statement

After its selected PASS closes, dev-sanity hands the generated stack input to sanity-stack. Handoffs are serialized one at a time, independently of sanity close order; an inline sanity-stack-link invocation follows the same locking procedure.


### Rationale

Two PASSes closing at once would write the stack concurrently, so dev-sanity hands off one at a time after each close; a close-order dependency would let one slow sanity block others (CHANGELOG: serialized sanity linking, phase bj; dev-sanity.md 'One handoff at a time').

### Success Criteria

**Acceptance Criteria:**

- [ ] The stack input file is written only when the selected verdict is PASS and is absent for a FAIL.
- [ ] An inline `sanity-stack-link` run claims the stack bead before any stack write, as the subagent does.
- [ ] Three PASSes handed off one after another are linked in the order handed off, not in sanity close order.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_stack_input_carries_assignment_budget_and_worktree_and_only_passes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_three_passes_link_in_verdict_order`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).

## REQ-SST-0013: dev-sanity's side

**Status:** Draft  
### Requirement Statement

The sanity close hook runs on the selected verdict before linking and accepts an absent stack result. An already-linked layer at the same pinned commit returns stacked, even below the top. rebase_required, lock_timeout and stack_failed notify the phase lead and leave the sanity task closed; none increments sanity_round. The lead owns further dev redispatch or stack repairs.


### Rationale

A stack failure must not undo or hold a sanity PASS the dev already earned, and a replayed handoff must be idempotent; the hook therefore closes on the verdict first and treats the stack result as optional (CHANGELOG: sanity task stays closed when not stacked).

### Success Criteria

**Acceptance Criteria:**

- [ ] The close hook, given vars with no stack result, still closes the sanity bead with `PASS at <commit>`.
- [ ] A replay for an already linked layer at the same pinned commit, even below the top, returns `stacked` with `top` equal to the current top and no metadata write.
- [ ] After `rebase_required`, `lock_timeout` or `stack_failed` the sanity task is not reopened and `sanity_round` is unchanged.
- [ ] The lead is notified on those three results.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_already_linked_lower_layer_at_pinned_commit_is_stacked`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_rebase_then_real_sanity_hook_preserves_round_and_hands_off`

### Implementation Notes

Sources: `agents/sanity-stack.md`, `agents/dev-sanity.md`, the stack bead,
`sc-gh-stack` skill. Rulings: Rand, 2026-10-18, anchored ANC-065..069
(atm-core `docs/plans/phase-bj/anchors.md`).
