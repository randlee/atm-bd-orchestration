---
name: beads-compliance-and-completion-verification
description: Verify bead completion claims against acceptance criteria, code, tests, sanity, QA, and merge evidence. Use for doubtful closures, scoped completion audits, or re-verifying remediation; report confirmed gaps separately from missing evidence.
---

# Verify completion claims

Job 4: establish what was actually delivered, then feed confirmed gaps back to
planning and prioritization. Adapted from the supplied compliance/completion
package. Its central rule is preserved: a status field is a claim, and each
acceptance criterion needs concrete evidence.

## Select the audit, not a new project

Use `atm`, `bd` backed by a Dolt server, and `.atm.toml` for agent configuration.
The lead knows its phase; workers use their assigned worktree and its
`docs/plans/phase-<current>/` information. Audit the requested phase and beads at
the relevant commits, even when other computers are working on other phases.
Use the repository's evidence locations and configured team members.

Identify the requested bead set and what completion means: development,
sanity, QA, merge, integration, or release. Read full live beads and any approved
amendments. An intentionally dev-closed bead awaiting QA is not automatically
a false closure. Do not infer phase membership from a label alone.

Choose depth based on the question:

- **Triage:** locate suspicious or missing evidence; make no verified-complete
  or confirmed-false-closed claim from this pass alone.
- **Single-bead / standard:** inspect each criterion, execute the required proof
  where possible, and verify relevant consumer contracts.
- **Re-verification:** reuse evidence only when its commit, inputs, environment,
  and criterion remain applicable; recheck changed work and affected consumers.
- **Comprehensive:** add independent review and deeper integration/adversarial
  checks for a requested release or high-stakes audit.

The source package's scripts depend on `br`, SQLite layout, and an orchestrator
that performs the substantive verification. They are not installed here.
In particular, its convenience runner's placeholder compliance records are not
real test results. Follow the evidence workflow below using `bd` and the team's
existing sanity/QA artifacts; this skill is not a new mandatory phase gate.

## Evidence workflow

Use a dated artifact directory at the repository's designated evidence location,
or a local temporary directory for report-only investigation. Record the audit
scope, source commit(s), tool versions, and snapshot time. Preserve prior passes.
Do not switch a worker's checkout or run tests against an unverified branch.
Use an isolated checkout when execution requires a different commit.

1. **Inventory:** fetch full live bead records and prerequisite relationships.
   Use [beads-bv](../beads-bv/SKILL.md) for a fresh snapshot and structural impact.
2. **Extract:** enumerate each acceptance criterion literally. Separate approved
   amendments from missing requirements; do not invent new acceptance criteria.
3. **Locate:** map each criterion to code, tests, docs, CI, and the relevant
   commit. Missing citations mean missing evidence, not proof that code is absent.
4. **Execute:** rerun the relevant proof at the checked commit when available.
   Capture command, environment, stdout/stderr, exit code, and actual assertions.
   If unavailable, mark verification blocked/unknown and name the missing check.
   Existing CI evidence must identify its exact head and applicability.
5. **Check substance:** test existence and exit zero are insufficient. Confirm
   it exercises the production behavior and asserts the promised result. Inspect
   stubs, hardcoded outputs, skipped cases, and mocks only where prohibited by
   the criterion. A grep hit is a lead for inspection, not a verdict.
6. **Check depth:** use bead-specific coverage, edge/error cases, requested fuzz
   duration, golden freshness, or real-service evidence as applicable.
7. **Synthesize:** verify producer/consumer contracts, integration handoffs, and
   requirements that fall between beads. Verify sanity and QA at the relevant
   commit and merge state separately from stored closure.
8. **Report:** assign a criterion-level verdict with citations. Use
   [evidence and scoring](references/evidence-and-scoring.md) for the report
   format, optional rubric, calibration, and remediation ordering.
9. **Remediate when authorized:** send confirmed gaps to
   [beads-workflow](../beads-workflow/SKILL.md) to create/update the scoped work
   through the package's existing finding and validation machinery. Do not
   reopen passed gates or create a parallel finding system. Polish changed
   beads for individual clarity, cross-bead consistency, and stability.
10. **Review the audit:** independently check questionable verdicts and the
    largest claimed gaps. Compare subsequent passes for new findings, evidence
    changes, and unresolved contradictions before reporting convergence.

Default to report-only unless the user or current assignment authorizes bead
remediation. A scoped audit does not authorize unrelated code changes, new
release gates, or promoting backlog work into the phase.

## Calibrate before escalating

The source workflow explicitly warns that deterministic scans can produce
large false-positive counts. Inspect several of the most suspicious records
against real evidence before reporting a systemic failure. Explain pipeline
limitations rather than borrowing a false-positive percentage from another
project. Distinguish a confirmed defect, partial implementation, missing proof,
and an audit-tool failure.

Give the user the concrete consequence, bead/criterion, evidence, remaining
work, and next owner/action. Feed confirmed priorities to beads-bv and execution
to [multi-agent-swarm-workflow](../multi-agent-swarm-workflow/SKILL.md). An audit
can finish with unresolved work clearly recorded; do not call the product
complete merely because the audit report exists.
