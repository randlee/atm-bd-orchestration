# Plan-hardening evaluation: subagent

Run the shipped plan-hardening skill in **planner with subagents** mode against
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
   iteration and final formula using the shipped step template. For each step,
   give one background general-purpose subagent the exact rendered template;
   record the wisp IDs. Each subagent claims and closes its step bead, with no
   ATM task or ATM command for the step. Run the planner's fix steps through
   subagents too, as the skill requires.
2. Before squashing any wisp or deleting anything, run
   `.claude/skills/plan-hardening/evals/check.sh eval-phase-z subagent` and capture its complete output and
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

The runner asks the same agent after the run closes, using SendMessage:

1. Which instruction was unclear?
2. Where did you guess?
3. Which instruction did you skip or reinterpret, and why?
4. What did you need but not have?
5. What would you change?
