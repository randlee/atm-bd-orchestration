# BV graph analysis for the lead

Routine task assignment is the dispatcher's job: the dispatcher (parallax,
where installed; otherwise whoever runs the Loop in `SKILL.md`) assigns what
`bd ready` returns, with the templates, in priority order. The lead does not
re-run that loop by hand. The lead's orchestration work has two halves:

1. finding process porn and ceremony and eliminating it, with the
   `just-say-no-to-process-porn-and-ceremony` skill;
2. optimizing the work in progress and planning the continuing work, with BV
   (`bv`, the beads graph analyzer) and similar tools. This file covers this half.

BV is advisory. It never overrides `validate-plan`, `sprints.jsonl`, the plan
gate, the sanity and QA rules, round caps or the assignees the plan names, and
it never writes the graph. Every action below goes through the existing
workflow: a bead write the lead already owns, or a replan through the planner
(`sprints.jsonl` and the beads changed together in a plan PR, `SKILL.md`,
Loop). A BV result is read and acted on, or dropped. It is not committed,
attached to a bead, or turned into a gate or a report.

## Running it

From the repository root:

```bash
S=.claude/skills/atm-bd-orchestration/scripts/bv-analyze
$S --epic <root>                                     # live phase: triage + alerts
$S --epic <root> --modes triage alerts plan insights priority
$S --epic <root> --target <bead>                     # adds that bead's blocker chain
$S --file <scratch>/plan.jsonl --modes triage plan insights   # rendered plan, before bd import
```

`<root>` is the phase root (`<prefix>-phase-<x>`). Without `--file` the
script runs `bd --readonly export --all` into a fresh temp directory, keeps
that full export (`issues.jsonl`) and writes `epic.jsonl`: the root and every
recursive `parent-child` descendant (sprints, sanity checks, plan-review, QA,
finding and fix beads) with only the edges between them. BV runs on
`epic.jsonl`, except `--target`'s blocker chain, which runs on the full export
so a prerequisite outside the phase stays visible. With `--file` it analyzes
a copy of the rendered import JSONL and needs no database; add `--epic` only
when the file contains the root.

It prints a receipt summary. `receipt.json` beside the outputs holds `members`
(the descendant set) and `excluded_dependencies` (every edge crossing the
phase boundary, either direction); each mode's output is `<mode>.json`.

- An export failure, a duplicate id, an absent root or target, or BV reading a
  different, stale or partial source exits 1 with no output. Fix the cause;
  there is no fallback to an older JSONL.
- Rerun it for every decision. Like `bd ready`, a BV result is never cached.
- Never run bare `bv`: it opens the TUI.
- Exports hold full bead text; keep the temp directory local.
- Use `--epic`, not `--label`: phase membership is the hierarchy, and labels
  miss legacy findings. The two are exclusive.

## Reading the outputs

| Output | Path in the JSON | Meaning here |
| --- | --- | --- |
| triage | `.triage.quick_ref` | open, actionable and blocked counts for the phase subgraph |
| triage | `.triage.recommendations[]` | beads ranked by graph score, with `reasons` and `breakdown` |
| triage | `.triage.blockers_to_clear[]` | open beads and what each releases (`unblocks_ids`) |
| triage | `.triage.project_health.graph` | `node_count`, `edge_count`, `has_cycles` |
| alerts | `.alerts[]` (`type`, `severity`, `issue_id`) | stale work, priority mismatch, possible duplicates |
| plan | `.plan.tracks[]` | dependency-respecting parallel tracks; their count is the parallel width |
| insights | `.full_stats.critical_path_score` | length of the longest serial chain from each bead |
| insights | `.Slack` | slack 0 means the bead is on the critical path |
| insights | `.Bottlenecks`, `.Keystones` | where paths concentrate; what most work rests on |
| insights | `.Articulation` | a bead whose removal disconnects the graph |
| insights | `.Cycles`, `.Orphans` | dependency cycles; beads with no dependency edges |
| priority | `.recommendations[]` | suggested priority changes with `reasoning` |

Before trusting a metric, read `.status` in insights, plan and priority. Each
metric is `computed`, `approx`, `timeout` or `skipped`; an empty `Cycles`
list from a skipped computation proves nothing. Counts cover the phase
subgraph, closed beads included, not the team's live queue.

- **PageRank / keystone:** foundational beads that much rests on. Confirm the
  dependents and the edge direction before acting.
- **Betweenness / bottleneck:** paths concentrate here. In this graph that is
  usually a sanity check bead, because dependents wait on the sanity bead,
  never on the dev bead.
- **Critical path / slack:** structure only. No durations are recorded, so a
  length counts serial steps, not days.
- **Cycles:** a planning mistake. Breaking one by deleting an arbitrary edge
  can hide a real prerequisite; find the edge whose prerequisite is not real.
- Graph independence is not edit independence. Two sprints are parallel only
  when their `owned_paths` are disjoint (`atm-beads-plan-guidelines.md`,
  Tracks And Balance).

Expected in this workflow, not findings:

- `potential_duplicate` alerts between sanity check, plan-review or QA beads,
  which are rendered from shared templates;
- orphans that are the phase root, `stage:plan*` beads, `bd gate` beads or a
  release bead (a dev or sanity bead with no edges is worth a look);
- triage `claimable` flags and emitted commands: assignment is the
  dispatcher's, so never run what BV emits.

`priority_mismatch` alerts and `--robot-priority` suggestions are inputs, not
instructions. Finding priority comes from severity (`SKILL.md`, Priority) and
the dispatcher works in priority order, so a priority change is a lead
decision with a reason, never a suggestion applied as-is.

## Optimizing the work in progress

### At each wave boundary

A wave boundary is a sanity PASS releasing dependents, or a QA verdict filing
findings. Run `--epic <root> --modes triage alerts plan insights`. Then:

| Signal | Lead action |
| --- | --- |
| a slack-0 bead is open behind slack>0 work at the same priority | re-prioritize: `bd update <bead> --priority <n>` with the reason in its notes, so the dispatcher takes it next |
| `plan.tracks` shows fewer live tracks than devs, while a serial chain holds the rest | split or re-order: if a queued sprint on the chain has a part with disjoint `owned_paths`, replan it into two sprints through the planner; if a `must_follow` edge has no real prerequisite, have the planner make it `parallel_safe` |
| a top `blockers_to_clear` or `Bottlenecks` entry is a sanity check | the sanity member is the bottleneck: confirm its task is moving; if checks queue behind each other, raise it with the user (staffing is a roster decision) |
| findings pile up under one dev bead on the critical path | send its blocking findings to the strongest dev (the lead picks finding assignees); add a finding-to-finding `blocks` edge only where one fix needs another |
| an open bead nothing downstream needs and no requirement governs | cut it: close it with a reason, or run it through the ceremony skill if it exists only as process |
| `stale_issue` on an in-progress bead | read the assignee's branch read-only (`git -C <worktree> log`, `gh pr view`) and its last report before anything else; quiet is not a stall |

### When work stalls

A stall is `bd ready -l phase-<x>` listing only the root while open beads
remain, a bead staying blocked after its prerequisites look done, or a
not-ready report or task-refused close naming a blocker. Run
`--epic <root> --target <stuck bead>`, read `blocker-chain.json` and the
receipt's `excluded_dependencies`, and act on the root blocker:

| Root blocker | Lead action |
| --- | --- |
| an open sanity check whose dev bead closed | the dispatcher missed or lost it: tell the dispatcher, or re-assign it with the same task id |
| an open finding child of a sanity FAIL | the dev-fix or fix assignment is missing: the dispatcher sends it (`SKILL.md`, Loop) |
| the plan-review bead | the plan gate has not passed (`SKILL.md`, Plan Gate) |
| a `bd gate` bead | only the user releases it; say what it holds |
| a bead outside the phase (`excluded_dependencies`) | a cross-phase prerequisite: report it to that phase's lead or the user (`blocking-findings-guidelines.md`); never pull it into this phase |
| a `blocked` bead with a `failed:` note | task-refused handling: reassign, split or close it with a reason |
| a wrong or missing `blocks` edge | stop dispatch; `validate-plan` is the check and the planner replans |
| nothing in the graph | the cause is outside it: unclear acceptance, a missing decision, the environment, or overlapping `owned_paths`. Read the bead and the agent's last report |

## Planning the continuing work

### Before import and at plan review

Run `--file <scratch>/plan.jsonl --modes triage plan insights` after
`validate-plan --file` passes and before `bd import`, then
`--epic <root> --modes triage alerts plan insights` after import, before the
plan-review bead is dispatched, and after each FAIL round's fixes. Fix what it
shows in the plan before the review spends a round on it:

| Signal | Lead action |
| --- | --- |
| `has_cycles` or a non-empty `Cycles` | do not import or dispatch review; the planner fixes the edge whose prerequisite is not real |
| parallel width (`plan.tracks`) below the devs the phase is staffed for | find each serial edge on the longest chain between sprints with disjoint `owned_paths` and have the planner make it `parallel_safe`, or split the sprint that holds the chain |
| one chain's `critical_path_score` far above the other tracks | the phase ends when that chain does: split its largest sprint, or move work off it (`atm-beads-plan-guidelines.md`, Split Early) |
| a dev bead that is an `Articulation` point or top `Keystones` | everything funnels through one sprint: make sure it is a small contract sprint placed first, not a large one |
| a dev or sanity bead in `Orphans` | confirm `relation: root` and that something consumes its work; otherwise it is scope the phase does not need |

The plan-scope reviewer still owns the plan-review verdict on shape and width.

### Next wave and next phase

When sprints are added to a running phase (`<root>-plan-qa-<n>`), run the
pre-import check on the new beads' JSONL and the live check on the root, and
compare the critical path before and after: new work should not lengthen it
unless it has to.

At phase end, before landing the stack, run `--epic <root>`:

- `.triage.quick_ref.open_count` is 1 (the root) when the phase is done. Any
  other open member shows in `recommendations[]`; the hierarchy finds a
  finding the label query misses.
- `receipt.json` `members` is the root's descendant set that the post-mortem
  inventory asks for (`post-mortem.md`, Inventory and target). Hand it to the
  reviewer as the list to reconcile; closed status is still only a claim.
- Each `excluded_dependencies` edge needs a disposition in the post-mortem.

Which beads were bottlenecks and which chain set the phase length is input to
the next phase's plan shape. Bring it to the next planning session; do not
write it up as an artifact.

## Requirements

`bv` with the robot interface and `source_authority` output (tested with
v0.25.0) and, for the live modes, `bd` connected to the repository's Dolt
server. BV is optional: the orchestration runs without it and nothing gates
on it.
