# Plan-hardening evaluation: subagent

Run the shipped plan-hardening skill in **planner with subagents** mode on the
seeded plan. The dispatcher supplies absolute paths `EVAL_ROOT` (the source
`plugins/atm-bd-orchestration/evals/plan-hardening` directory) and `EVAL_WORKTREE`
(a disposable atm-core worktree with the skill under test installed), and
`EVAL_MODEL` (the cell model: `haiku` or `gpt-6-luna`). Use that exact model
for every step subagent; do not silently substitute a model. Run all steps from
`EVAL_WORKTREE`. Do not inspect `$EVAL_ROOT/planted.json` before review ends.
Never push or mutate another plan.

1. Create a private database for this cell, not the live team database:

```bash
set -euo pipefail
EVAL_SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/atm-plan-eval.XXXXXXXX")
export BEADS_DIR="$EVAL_SCRATCH/.beads"
# The isolated worktree must not already have a database or a live-store link.
test ! -e "$EVAL_WORKTREE/.beads" && test ! -L "$EVAL_WORKTREE/.beads"
(cd "$EVAL_SCRATCH" && bd init --proxied-server --prefix atm --non-interactive --skip-hooks --skip-agents)
ln -s "$BEADS_DIR" "$EVAL_WORKTREE/.beads"
(cd "$EVAL_WORKTREE" && bd info --json)
```

   Stop unless `bd info` identifies this exact scratch database; never link to
   or import into the live store. Copy `$EVAL_ROOT/phase-z.toml` to the new
   worktree's `.atm-bd/phase-z.toml` only if that file is absent. Run once from
   `EVAL_WORKTREE`: `npm ci --prefix .claude/skills/sprint-report/renderer`.
   If setup fails, report the exact command and error; do not run the cell.
   Copy the index to scratch: `cp "$EVAL_ROOT/plan-index.jsonl" "$EVAL_SCRATCH/plan-index.jsonl"`.
   Import the fixture with `bd import -i "$EVAL_ROOT/fixture-plan.jsonl"`.
2. Read `.claude/skills/plan-hardening/SKILL.md`, run one iteration and the
   final formula. For every step, use one background general-purpose subagent at the cell model; the planner fix steps also use subagents. Each subagent claims and closes its step bead and runs no ATM task or command. Set the shipped step-template vars `beads_dir` to
   the absolute `$BEADS_DIR`, `workdir` to `$EVAL_WORKTREE`, and `plan_index`
   to `$EVAL_SCRATCH/plan-index.jsonl` on every step. These rendered instructions
   carry cwd and database to agents; do not prepend or alter the rendered prompt.
   Pass `--index "$EVAL_SCRATCH/plan-index.jsonl"` to validate-plan and sprint-review.
   Save their full output and exit status: nonzero means the step fails and is
   reported, never a passing result. Record the wisp IDs.
3. Before squashing, run `"$EVAL_ROOT/check.sh" atm-eval-phase-z subagent` and
   capture its complete output and exit status. A failure is a failed cell.
4. After saving evidence, squash the evaluation wisps. Do not run `bd delete`.
   Remove only the phase-z.toml you copied, stop this cell's Dolt server with
   `BEADS_DIR="$BEADS_DIR" bd dolt stop`, and delete only the private database
   directory `$EVAL_SCRATCH/.beads` after unlinking the worktree symlink and confirming it is beneath the exact
   `mktemp` directory you created. Preserve outputs and digest IDs in scratch.
5. Tell the caller the check exit status, output and cleanup result. Remain
   available for the caller's post-run questions; do not answer them early.

## Post-run questions

The runner asks the same agent after the run closes, using SendMessage:

1. Which instruction was unclear?
2. Where did you guess?
3. Which instruction did you skip or reinterpret, and why?
4. What did you need but not have?
5. What would you change?
