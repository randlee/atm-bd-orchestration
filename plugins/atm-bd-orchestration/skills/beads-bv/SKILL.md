---
name: beads-bv
description: Prioritize approved bead work with bv graph analysis from a fresh bd/Dolt export. Use for next-work decisions, bottlenecks, parallel tracks, alerts, and priority review; hand dispatch and completion verification to their own skills.
---

# Graph-aware prioritization

Job 2: explain which useful work should happen next and what it unlocks.
Adapted from the supplied beads-bv package and the compliance package's
consequence-aware prioritization. Beads own the plan; bv analyzes its graph.
Graph importance, dispatch readiness, and verified completion are different.

## Scope and fresh input

Use `atm`, `bv`, `bd` backed by a Dolt server, and `.atm.toml` for agent
configuration. The lead knows its phase; workers use the worktree specified in
their bead or assignment and its `docs/plans/phase-<current>/` information.
Different computers may orchestrate different phases; rank the assigned phase's
work and inspect cross-phase prerequisites separately.

Identify the approved phase/root, sprint or explicit bead set first. Read its
membership and exclusions. A label is a search aid, not authorization to pull
backlog work into the phase. A sprint wave and a finding batch need distinct,
explicit membership if they differ. If no scope is specified, state that the
analysis covers the whole database.

Locate the checkout connected to the intended live database, which may be the
primary checkout rather than the worktree. Check `bd info --json` and database
identity in `.beads/metadata.json`. Use the helper from this skill directory:

```bash
python3 <skill-dir>/scripts/analyze.py --repo <live-checkout> --epic <phase-epic-id>
```

It exports `bd --readonly export --all` to a new temporary JSONL, filters to the
epic and its descendants through `parent-child` edges, then runs
`--robot-triage` and `--robot-alerts` against that filtered file. It records
membership, excluded cross-boundary edges, timestamps, tool versions, SHA-256,
and source-loading checks in `receipt.json`. The complete export is retained
for external blocker checks. Use `--label` instead when label scope is intended;
omitting both scopes analyzes the full database.
It never falls back to an existing JSONL if live export fails. Exported records
can contain team memories: keep the artifacts local unless sharing is requested.

For planning depth, add `--modes triage alerts plan insights priority`.
For a stalled bead, add `--target <id>`; its blocker chain uses the whole
export so filtering cannot hide an external prerequisite. Inspect the receipt's
`excluded_dependencies` before calling a scoped candidate ready. Scoped metrics
and unlock counts cover the epic only; external blockers still require a full
blocker-chain and live readiness check. The epic root itself is planning context,
not a worker assignment.
Refresh after relevant team activity and before a new prioritization pass.
For separate computers, follow the configured Dolt remote-sync procedure first;
a new local export alone does not prove that another machine's changes arrived.

**Never run bare `bv`: it opens the TUI.** Use robot commands and explicit
`--db <snapshot> --no-cache --format json`. Do not install or upgrade tools
as a side effect of analysis. See [commands and metrics](references/commands-and-metrics.md).

## Turn metrics into decisions

1. Read triage recommendations and blockers-to-clear, then alerts. Separate
   immediately actionable work from important work that is still blocked.
2. For candidates within approved scope, compare stored priority, concrete
   user consequence, downstream work released, critical-path position, and
   evidence of effort. Explain why one candidate goes ahead of another.
3. If the highest-impact bead is blocked, trace its prerequisites to work that
   can actually advance now. Distinguish implementation from gate verification,
   QA, merge, or a decision the lead must resolve.
4. Use plan tracks to propose concurrency, then check owned paths, branch bases,
   shared test resources, and existing owners. Graph independence alone does
   not establish safe concurrent edits.
5. Before recommending dispatch, re-read the full live candidate with
   `bd show <id> --json`, compare `bd ready -n 0 --json`, and check ATM ownership
   and current task availability through the execution skill. Do not treat
   generated claim commands or `claim_safe` as authorization.

For a lead-owned gate, read its closure conditions. Closed prerequisites may
still lack required QA or merge evidence. Report the mismatch and route the
evidence question to
[completion verification](../beads-compliance-and-completion-verification/SKILL.md).
Do not close a gate because its centrality score or readiness looks good.

Use alerts to investigate stale work, priority mismatches, and possible graph
defects. Shared templates often produce duplicate suggestions; compare actual
scope before recommending a merge or closure. Do not infer missing development
from absent logs, or completed development from a closed bead alone.

## Return a decision brief

State the snapshot time and approved scope. Prefer a short table:

| Order | Bead / next action | Why now / what it unlocks | Blocker or evidence still needed | Owner / availability |
| --- | --- | --- | --- | --- |

Follow with useful parallel work and a concise alerts summary. Report
out-of-scope prerequisites separately for disposition; graph rank does not
promote them into the plan. Show actual IDs and reasons, not raw JSON by default.

Counts must name their population. Stored `blocked` status is not the count of
dependency-blocked beads. Some commands include neighbor nodes; metrics may be
approximated, timed out, or skipped. Inspect scope and computation status before
claiming a critical path, no cycles, or an ETA. Historical/closed nodes can
affect ranking. Do not present heuristic effort or saved-days estimates as facts.

Hand the recommendation to
[multi-agent-swarm-workflow](../multi-agent-swarm-workflow/SKILL.md). Analysis
does not mutate priorities, dependencies, claims, PRs, or team assignments.
If the user authorizes graph corrections, use
[beads-workflow](../beads-workflow/SKILL.md) to make and validate them.
