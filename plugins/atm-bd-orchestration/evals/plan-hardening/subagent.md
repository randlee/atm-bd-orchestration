# Plan-hardening evaluation: subagent

Run the shipped plan-hardening skill in **planner with subagents** mode on the
seeded plan. The dispatcher supplies absolute paths `EVAL_ROOT` (the source
an immutable per-cell copy of `plugins/atm-bd-orchestration/evals/plan-hardening`) and `EVAL_WORKTREE`
(an independent disposable atm-core clone with the skill under test installed), and
`EVAL_PLANNER` and `EVAL_DISPATCHER` (the actual identities taking those roles),
`EVAL_LEAD` (the planner in planner mode), and `EVAL_MODEL` (the cell model: `haiku` or `gpt-6-luna`). Use that exact model
for every step subagent; do not silently substitute a model. Run all steps from
`EVAL_WORKTREE`. Do not inspect `$EVAL_ROOT/planted.json` before review ends.
Never push or mutate another plan. `EVAL_WORKTREE` must be an independent
clone, not a linked Git worktree: compare `git rev-parse --git-common-dir`
with the clone's own `.git` and stop if it resolves to the live checkout.
The clone and its cache must be under a dispatcher-owned scratch directory.

1. Create a private database for this cell, not the live team database:

```bash
set -euo pipefail
EVAL_SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/atm-plan-eval.XXXXXXXX")
export BEADS_DIR="$EVAL_SCRATCH/.beads"
printf '%s\n%s\n' "$EVAL_SCRATCH" "$BEADS_DIR" > "$EVAL_WORKTREE/.atm-plan-eval-context"
# The isolated worktree must not already have a database or a live-store link.
test ! -e "$EVAL_WORKTREE/.beads" && test ! -L "$EVAL_WORKTREE/.beads"
(cd "$EVAL_WORKTREE" && git config beads.role maintainer)
python3 "$EVAL_ROOT/db-server.py" start "$EVAL_SCRATCH"
ln -s "$BEADS_DIR" "$EVAL_WORKTREE/.beads"
(cd "$EVAL_WORKTREE" && bd info --json)
```

   Stop unless the realpath of `bd info` database_path is within `$BEADS_DIR`
   and the socket and data paths in `$EVAL_SCRATCH/server.json` and
   `$BEADS_DIR/metadata.json` resolve inside that same scratch directory
   (macOS may spell `/tmp` as `/private/tmp`). The context file
   records the exact scratch and database paths on separate lines; read it in
   every new shell rather than assuming variables persist. Never link to or
   import into the live store. Copy `$EVAL_ROOT/phase-qx.toml` to the new
   worktree's `.atm-bd/phase-qx.toml` only if that file is absent. Set its
   `lead` field to the supplied `EVAL_LEAD` (the fixture default is arch-ctm). Run once from
   `EVAL_WORKTREE`: `npm ci --prefix .claude/skills/sprint-report/renderer`.
   If setup fails, report the exact command and error; do not run the cell.
   Copy the index to scratch: `cp "$EVAL_ROOT/plan-index.jsonl" "$EVAL_SCRATCH/plan-index.jsonl"`.
   If `$EVAL_WORKTREE/docs/plans/phase-qx.jsonl` exists or is a symlink, stop.
   Otherwise link that path to the scratch index; `bead-groups --phase qx`
   reads the plan path from phase-qx.toml when the planner adds a sprint.
   Import only the fixture containers with `bd import -i "$EVAL_ROOT/fixture-plan.jsonl"`.
   Do not pour groups until the final formula passes.
2. Read `.claude/skills/plan-hardening/SKILL.md`, run exactly one iteration (`iteration=1`, `iterations=1`) and the
   final formula. Use the supplied planner, dispatcher and lead identities. For every step, use one background general-purpose subagent at the cell model; the planner fix steps also use subagents. Each subagent claims and closes its step bead and runs no ATM task or command. Set the shipped step-template vars `beads_dir` to
   the absolute `$BEADS_DIR`, `workdir` to `$EVAL_WORKTREE`, and `plan_index`
   to `$EVAL_SCRATCH/plan-index.jsonl` on every step. Also set `plan_pr`
   to `none`, `scratch_dir` to `$EVAL_SCRATCH`, and `cache_path` to
   `$EVAL_WORKTREE/.atm-bd/atm.bd-cache.sqlite3` on every step. Set
   `policy_path` to the absolute path under `$EVAL_WORKTREE` named by
   `policy_path` in its `.claude/project/atm-bd-orchestration.yaml`. These rendered instructions
   carry cwd and database to agents. Never hand-write or alter the rendered file;
   dispatch the fixed line from SKILL.md with its absolute path and, for a retry,
   the named attached-evidence path. The runner reads it and stops if missing.
   Pass `--index "$EVAL_SCRATCH/plan-index.jsonl"` to validate-plan.
   Do not run sprint-review in a fix step.
   If validate-plan reports `proxy.doctor.unsupported`, use the rendered step
   template's one-time `--no-doctor` fallback and retain the original error
   (atm-bd-orchestration#807); do not skip any other failure.
   Save their full output and exit status immediately after each command. Nonzero
   means the step fails and is reported, never a passing result. If any step (review, fix, or verify) fails recoverably, stop the runner and re-dispatch that same
   step once to a fresh runner with its failed return and evidence. If the
   retry fails, stop with `EXECUTION.STEP_FAILED`; do not run the final formula: capture the failed checker result and
   report the blocking error. Record the wisp IDs.
3. If the final formula passes, run `bead-groups --phase qx` to pour
   all groups, then `sprint-review --root atm-phase-qx --index
   "$EVAL_SCRATCH/plan-index.jsonl"`. Capture both outputs and exit codes; a
   failed pour or render fails the cell even if the checker passes. If the
   formula did not pass, skip the pour and render. In either case, before
   squashing, run `"$EVAL_ROOT/check.sh" atm-phase-qx subagent` and
   capture its complete output and exit status. A failure is a failed cell.
4. Only if the final formula completes AND check.sh exits 0, squash the
   evaluation wisps. On an aborted run or failed check, reopen any failed fix bead before stopping
   the server. Do not squash or delete the scratch database: stop the private server with `python3 "$EVAL_ROOT/db-server.py" stop "$EVAL_SCRATCH"`, retain the database and context file as evidence, and
   report their exact paths. Do not run `bd delete`.
   On a completed run with check exit 0, unlink the worktree plan-index symlink, remove only
   the phase-qx.toml and context file you copied, stop this cell's server with `python3 "$EVAL_ROOT/db-server.py" stop "$EVAL_SCRATCH"`,
   retain `$EVAL_SCRATCH/.beads` and `$EVAL_SCRATCH/data` through the post-run
   debrief. After answering the questions, delete only those two directories,
   after unlinking the worktree symlink and confirming both are beneath the
   exact `mktemp` directory you created. Preserve outputs and digest IDs in scratch.
5. Tell the caller the check exit status, output and retained evidence paths.
   Remain available for the caller's post-run questions; do not answer them early.
   After answering, perform the successful-run cleanup above and report its result.

## Post-run questions

The runner asks the same agent after the run closes, using SendMessage:

1. Which instruction was unclear?
2. Where did you guess?
3. Which instruction did you skip or reinterpret, and why?
4. What did you need but not have?
5. What would you change?
