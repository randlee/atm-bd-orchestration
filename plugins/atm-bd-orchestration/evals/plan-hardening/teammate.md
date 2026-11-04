# Plan-hardening evaluation: teammate

Run the shipped plan-hardening skill in **planner with teammates** mode on the
seeded plan. The dispatcher supplies absolute paths `EVAL_ROOT` (the source
an immutable per-cell copy of `plugins/atm-bd-orchestration/evals/plan-hardening`) and `EVAL_WORKTREE`
(an independent disposable atm-core clone with the skill under test installed), and
`EVAL_PLANNER` and `EVAL_DISPATCHER` (the actual identities taking those roles),
`EVAL_LEAD` (the planner in planner mode), and `EVAL_MODEL` (the cell model: `haiku` or `gpt-6-luna`). The agent under test uses that exact model. Review teammates run the
step themselves; they do not need to spawn step subagents. Run all steps from
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
   import into the live store. Copy `$EVAL_ROOT/phase-zzeval.toml` to the new
   worktree's `.atm-bd/phase-zzeval.toml` only if that file is absent. Run once from
   `EVAL_WORKTREE`: `npm ci --prefix .claude/skills/sprint-report/renderer`.
   If setup fails, report the exact command and error; do not run the cell.
   Copy the index to scratch: `cp "$EVAL_ROOT/plan-index.jsonl" "$EVAL_SCRATCH/plan-index.jsonl"`.
   If `$EVAL_WORKTREE/docs/plans/phase-zzeval.jsonl` exists or is a symlink, stop.
   Otherwise link that path to the scratch index; `bead-groups --phase zzeval`
   reads the plan path from phase-zzeval.toml when the planner adds a sprint.
   Import only the fixture containers with `bd import -i "$EVAL_ROOT/fixture-plan.jsonl"`.
   Do not pour groups until the final formula passes.
2. Read `.claude/skills/plan-hardening/SKILL.md`, run exactly one iteration (`iteration=1`, `iterations=1`) and the
   final formula. Use the supplied planner, dispatcher and lead identities. Assign every step as an ATM task with the shipped step template and vars. Each assigned teammate starts and closes its own task and claims and closes the step bead. The planner takes the fix steps. Use two distinct step teammates for
   parallel reviews; if only one is available, run them serially and record it.
   Run the review steps at `EVAL_MODEL`; using that cell model instead of the
   reviewers' configured models is expected in this evaluation.
   For a fix step that cannot finish, reopen the bead and close the ATM task
   refused with the template failure envelope; do not claim it completed. Set the shipped step-template vars `beads_dir` to
   the absolute `$BEADS_DIR`, `workdir` to `$EVAL_WORKTREE`, and `plan_index`
   to `$EVAL_SCRATCH/plan-index.jsonl` on every step. Also set `plan_pr`
   to `none`, `scratch_dir` to `$EVAL_SCRATCH`, and `cache_path` to
   `$EVAL_WORKTREE/.atm-bd/atm.bd-cache.sqlite3` on every step. These rendered instructions
   carry cwd and database to agents; do not prepend or alter the rendered prompt.
   Pass `--index "$EVAL_SCRATCH/plan-index.jsonl"` to validate-plan.
   Do not run sprint-review in a fix step.
   If validate-plan reports `proxy.doctor.unsupported`, use the rendered step
   template's one-time `--no-doctor` fallback and retain the original error
   (atm-bd-orchestration#807); do not skip any other failure.
   Save their full output and exit status immediately after each command. Nonzero
   means the step fails and is reported, never a passing result. If a fix step fails recoverably, stop the runner and re-dispatch that same
   step once to a fresh runner with its failed return and evidence. If the
   retry fails, stop with `EXECUTION.STEP_FAILED`; do not run the final formula: capture the failed checker result and
   report the blocking error. Record the wisp IDs.
3. If the final formula passes, run `bead-groups --phase zzeval` to pour
   all groups, then `sprint-review --root atm-eval-phase-zzeval --index
   "$EVAL_SCRATCH/plan-index.jsonl"`. Capture both outputs and exit codes; a
   failed pour or render fails the cell even if the checker passes. If the
   formula did not pass, skip the pour and render. In either case, before
   squashing, run `"$EVAL_ROOT/check.sh" atm-eval-phase-zzeval teammate` and
   capture its complete output and exit status. A failure is a failed cell.
4. Only if the final formula completes AND check.sh exits 0, squash the
   evaluation wisps. On an aborted run or failed check, reopen any failed fix bead before stopping
   the server. Do not squash or delete the scratch database: stop the private server with `python3 "$EVAL_ROOT/db-server.py" stop "$EVAL_SCRATCH"`, retain the database and context file as evidence, and
   report their exact paths. Do not run `bd delete`.
   On a completed run with check exit 0, unlink the worktree plan-index symlink, remove only
   the phase-zzeval.toml and context file you copied, stop this cell's server with `python3 "$EVAL_ROOT/db-server.py" stop "$EVAL_SCRATCH"`,
   and delete only `$EVAL_SCRATCH/.beads` and `$EVAL_SCRATCH/data` after
   unlinking the worktree symlink and confirming both are beneath the exact
   `mktemp` directory you created. Preserve outputs and digest IDs in scratch.
5. Tell the caller the check exit status, output and cleanup result. Remain
   available for the caller's post-run questions; do not answer them early.

## Post-run questions

The runner asks the same agent after the run closes, using `atm send`:

1. Which instruction was unclear?
2. Where did you guess?
3. Which instruction did you skip or reinterpret, and why?
4. What did you need but not have?
5. What would you change?
