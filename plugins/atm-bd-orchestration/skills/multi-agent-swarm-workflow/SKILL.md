---
name: multi-agent-swarm-workflow
description: Coordinate parallel implementation of approved beads using ATM workers and bv recommendations. Use to allocate ready work, manage ownership and blockers, and carry assignments through sanity and QA without expanding the plan.
---

# Coordinate execution

Job 3: turn a reviewed work graph into bounded assignments and verified handoffs.
Adapted from the supplied swarm workflow: shared context, explicit ownership,
prompt acknowledgement, useful parallel work, and review before closure.
ATM supplies the coordination used by Agent Mail/NTM in the source package.

## Establish the team and authority

Use `atm`, `bd` backed by a Dolt server, and `.atm.toml` for agent configuration.
The lead knows its phase; each worker uses the worktree in its bead or assignment
and the phase information in `docs/plans/phase-<current>/`. Query that phase's
work even when other computers are orchestrating other phases in the same repo.
Read current ATM task state before allocating a worker. Use the existing roster
and difficulty rules; adding agents or changing the lead is a separate decision.

Use [atm-bd-orchestration](../atm-bd-orchestration/SKILL.md) as the canonical
dispatch/lifecycle contract. Its templates, assignment gates, round limits,
and close handling apply here. Resolve recipients from `.atm.toml` and pass
them in assignment vars. This skill does not establish a
competing set of claim/close commands. Resolve template paths from the installed
skills root; existing scripts may require the repository's `.claude` installation.

Before querying or claiming across computers, follow the repository's configured
Dolt sync procedure. Route cross-phase prerequisites to their owning lead.

## Lead loop

1. Refresh `bd ready -n 0 --json` and the ATM task/owner state. Read
   [beads-bv](../beads-bv/SKILL.md) for graph-informed ordering within the approved
   phase. Never dispatch the phase epic or a lead-only gate as coding work.
2. Match ready, scoped beads to available workers. Validate the plan and
   assignment gates. Confirm the declared `pr_target` and owned paths.
3. Check concurrency beyond the DAG: overlapping files, shared branch bases,
   test ports, and integration artifacts. Use repository-supported ownership or
   reservation mechanisms; a worktree alone does not eliminate merge conflicts.
4. Send the assignment with the canonical ATM template and vars. Include the
   phase/root, worktree, change specification, acceptance criteria, owned paths,
   dependency artifacts, and required completion evidence. The task ID is the bead ID.
5. On progress, refusal, or completion, acknowledge as the repository protocol
   requires, inspect the evidence, and perform the next canonical transition.
   Recompute readiness after state changes rather than keeping a cached queue.

Spend lead attention on dispatch, blockers, evidence, and integration. Workers
perform the implementation and bounded reviews. Prioritization should keep
useful work moving without a stream of redundant instructions or repeated
requests for information already present in beads.

## Worker loop

Read the assignment and full bead, governing requirements, repository rules,
and prerequisite artifacts. Follow its ready/claim/start gates. Work inside
the declared scope and branch; self-review the diff and run the required checks.
Send concrete progress or a specific blocker, not just an assertion of activity.

Complete through the paired task/bead template with commit, changed behavior,
validation, and known gaps. Development completion is the input to sanity and
QA, not proof of their success. A push alone closes neither the task nor the bead.
Workers take their next assigned task through ATM; bv recommendations do not
authorize bypassing the lead's queue or claiming another worker's assignment.

If a worker disappears, first inspect its task, branch, commits, bead notes,
and outstanding ownership. Recover the actual state before reassigning. After
compaction, reload these records and continue rather than restart the task.

## Review, blockers, and completion

Preserve the source workflow's self-review and independent cross-review loops,
bounded to the approved work and repository review limits. A clean exploratory
review is useful evidence, not a substitute for acceptance tests or QA.
Unrelated discoveries are reported to the backlog process; they do not silently
become new phase deliverables or merge blockers.

Classify a stalled task before dispatching more work: unmet prerequisite,
missing decision, unclear acceptance, unavailable environment, or conflicting
ownership. Route plan defects to [beads-workflow](../beads-workflow/SKILL.md),
ordering decisions to beads-bv, and doubtful completion to
[completion verification](../beads-compliance-and-completion-verification/SKILL.md).

The lead retains stack/integration ownership. Follow repository merge approval
rules and identify the PRs covered by an approval. Do not replace a requested
delegation with a lead handoff. Report completed, in-flight, blocked, and
undispatched work separately, with exact IDs and the next action for each blocker.
