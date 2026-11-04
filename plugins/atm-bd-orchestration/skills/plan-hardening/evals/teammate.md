# Plan-hardening evaluation: teammate

Run the shipped plan-hardening skill in **planner with teammates** mode against
only this seeded plan. Run from the isolated evaluation worktree supplied by
the dispatcher, with the bp-2 skill installed under `.claude/skills/plan-hardening`
and `.beads` linked to the live store. Use one iteration, then the final formula.
All bead writes must be under the evaluation root or carry its phase-z labels.
Never push from this worktree or change another plan. This is a live
run against the current repository's bead database: before importing, check
that `eval-phase-z` and `eval-z-1` through `eval-z-4` do not already exist;
if any exists, stop and report it. Do not inspect `planted.json` before the
review has completed.

1. Import `.claude/skills/plan-hardening/evals/fixture-plan.jsonl` with `bd import`. Read `.claude/skills/plan-hardening/SKILL.md` and the plan beads; perform the
   iteration and final formula using the shipped step template. Assign every
   step as an ATM task using `atm task assign --template --vars`; the assigned
   teammate must start and close its own ATM task and claim and close its step
   bead. The planner takes the fix steps. Record the wisp IDs.
2. Before squashing any wisp or deleting anything, run
   `.claude/skills/plan-hardening/evals/check.sh eval-phase-z teammate` and capture its complete output and
   exit status. A failure is a failed cell; retain the evidence for the caller.
3. After the check, squash the evaluation wisps. Remove only plan-fix beads
   created under `eval-phase-z` and the five fixture IDs, using `bd delete
   --force` on the explicit IDs. Before deleting, verify that every dependent
   belongs to the evaluation; never use `--cascade` or delete unrelated beads.
   Preserve the check output and any digest IDs in scratch.
4. Tell the caller the check exit status, output, and cleanup result. Remain
   available for the caller's post-run questions; do not answer them before
   they are asked.

## Post-run questions

The runner asks the same agent after the run closes, using `atm send`:

1. Which instruction was unclear?
2. Where did you guess?
3. Which instruction did you skip or reinterpret, and why?
4. What did you need but not have?
5. What would you change?
