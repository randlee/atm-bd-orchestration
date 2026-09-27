---
name: beads-workflow
description: Convert an approved plan into self-contained beads and explicit dependencies, then refine the graph before implementation. Use for plan-to-bead work and polishing remediation beads, not dispatch or completion audits.
---

# Plan to actionable beads

Job 1 of four: plan → beads → prioritization → execution → verification.
Adapted from the supplied beads-workflow package. Preserve its core practice:
review the work in plan space before spending implementation effort.

## Repository contract

Use `atm`, `bd` backed by a Dolt server, and `.atm.toml` for agent configuration.
The lead knows its phase; workers use the worktree specified in their bead or
assignment. Read that phase's information in `docs/plans/phase-<current>/`.
Several phases can run on separate computers; scope bead work to the assigned
phase and retain cross-phase prerequisites without taking over their work.

## Establish the scope

Read the approved plan in `docs/plans/phase-<current>/` and repository instructions. Identify the phase root,
deliverables, exclusions, acceptance criteria, and governing requirements.
When the plan already lives in beads, read those beads rather than reconstructing
it from chat. Keep authored planning documents and review evidence in that phase directory.
Beads carry executable scope and current work state; the planning files are not
a second live status database. Importing a markdown plan does not authorize
expanding its scope.

Use [atm-beads](../atm-beads/SKILL.md) for the schema, dev/sanity pairs,
templates, import commands, and validation. For a markdown source, use its
[import procedure](../atm-beads/resources/importing-md-plan.md). These remain
the package's implementation contract; this skill supplies the planning job.
Use `bd`, not a second tracker, and never edit the database or exported JSONL
as a substitute for a bead update.

## Construct the graph

Make each bead understandable to a worker who did not attend planning:

- Explain the user outcome, background, and technical approach.
- State concrete deliverables, owned paths, exclusions, and handoff artifacts.
- Define observable acceptance criteria and the tests/evidence needed for them.
- Name dependencies by bead ID and explain the prerequisite each edge represents.
- Carry the package's required requirements/ADR, difficulty, assignee, and
  branch-target fields. Resolve missing decisions before dispatch.

`bd dep add A B` means **A depends on B**. Keep parent-child organization and
discovered-from provenance distinct from scheduling dependencies. Wire the
required sanity gates through the existing plan contract. Merge order and
execution order must be explicit; neither a wave name nor a branch stack alone
proves that work is ready.

If the repository uses a foundational sprint index, it records bead identities
and membership, not another copy of their titles, status, or dependencies.
Follow the installed atm-beads schema and artifact requirements.

## Polish before implementation

Use the [review prompts](references/planning-prompts.md) in three passes:

1. Individual clarity: can the assignee implement and prove every deliverable?
2. Cross-bead consistency: do producer/consumer contracts and ownership agree?
3. Stability: did the previous changes introduce gaps, duplication, or cycles?

The source workflow recommends repeated reviews, commonly six to nine passes.
Here, follow the repository's review-round limits; use diminishing changes as
evidence of convergence, not a quota or permission to loop indefinitely. If
meaningful problems remain at the limit, report the unresolved decisions.
Do not expand an approved phase to absorb incidental tooling or historical debt.
Route such discoveries to the repository's backlog process.

After authorized edits, validate the plan using atm-beads. Use
[beads-bv](../beads-bv/SKILL.md) to investigate cycles, bottlenecks, missing-edge
suggestions, and priority mismatches from a fresh export. Review suggestions
against the intended artifacts before changing edges; removing an edge solely
to make a graph acyclic can hide a real prerequisite.

## Handoff

Provide the phase/root ID, exact sprint membership, unresolved decisions,
validation evidence, and reviewed dependency structure. Every wave or batch
must enumerate its members and completion rule. Hand the validated graph to
beads-bv for prioritization, then
[multi-agent-swarm-workflow](../multi-agent-swarm-workflow/SKILL.md) for execution.
Planning does not claim tasks or declare implementation complete.
