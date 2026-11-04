# Plan hardening live evaluations

Every cell runs in its own disposable worktree and `BEADS_DIR` scratch database.
Never connect the fixture to the live team store. The dispatcher supplies the
absolute source evaluation directory as `EVAL_ROOT`, the worktree as
`EVAL_WORKTREE`, and the cell's model as `EVAL_MODEL`. Before launching a cell,
the dispatcher must prepare that disposable worktree with no `.beads` path or
symlink; move only worktree-owned setup files aside, never the live database.

| Cell | Agent | Runner | Run by |
| --- | --- | --- | --- |
| 1 | haiku | subagent | fenix |
| 2 | haiku | teammate | fenix |
| 3 | gpt-6-luna | subagent | arch-ctm, else solar |
| 4 | gpt-6-luna | teammate | arch-ctm, else solar |

Give the selected `subagent.md` or `teammate.md` to the agent under test.
Keep `planted.json` out of its installed skill and do not expose it before its
review. Save the checker output and that same agent's five debrief answers in
the PR. Debrief never substitutes for a passing check.

The prompt creates a scratch database, imports the fixture, runs the checker
before squashing, then stops its database and removes only that scratch
`.beads` directory after a completed final formula. For an aborted run it
stops Dolt and retains the unsquashed scratch database as evidence. Never use `bd delete` or connect this fixture to the live
team database. If setup or cleanup cannot be proven safe, stop and report it.
