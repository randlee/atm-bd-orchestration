# Planning prompts adapted for bd

These retain the supplied workflow's plan-space review pattern while using
the shared package's schema and the user's approved scope.

## Convert a plan

Read the entire approved plan. Turn its deliverables into a comprehensive set
of self-contained beads with explicit dependency relationships. Preserve the
background, reasoning, constraints, acceptance criteria, tests, and handoffs a
future worker needs. Account for every approved deliverable without adding
new scope. Use the atm-beads templates and validation contract; use `bd` for
all bead writes. Identify missing decisions rather than inventing requirements.

## Polish a bead set

Read the repository instructions again. Review every bead in the specified
set: is its scope clear, does the approach satisfy the intended user outcome,
and can the acceptance criteria be verified? Preserve required functionality.
Include meaningful unit and end-to-end evidence where the deliverable needs
it. Check dependencies, ownership, and producer/consumer contracts. Use `bv`
to find graph problems and `bd` for authorized changes. Record the substantive
changes and remaining questions; a no-change pass is a useful result.

## After context loss

Read the repository instructions, the phase/root bead, the current approved
membership, and relevant full bead records. Recover prior review findings and
their dispositions. Continue the existing plan and its review-round budget;
do not restart planning or treat a summary as a replacement for the live beads.
