# Plan hardening live evaluations

Every cell runs in its own independent disposable clone and `BEADS_DIR`
scratch database with a private Dolt server and socket.
Never connect the fixture to the live team store. The dispatcher supplies the
absolute path of an immutable per-cell `git archive` copy of the evaluation
assets from the pushed candidate commit as `EVAL_ROOT` (record the commit and
checker hash), the independent clone as
`EVAL_WORKTREE`, and the cell's model as `EVAL_MODEL`. Before launching a cell,
the dispatcher must prepare that disposable clone with no `.beads` path or
symlink; move only clone-owned setup files aside, never the live database.
The clone may show tracked `.beads` files as deleted after setup moves them
aside and plan-hardening files as modified after the candidate skill is
installed. These changes are expected in the disposable clone.

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

The prompt creates a scratch database, imports the fixture containers and runs
the formula. After the final formula passes it pours groups and renders the
DAG, then runs the checker before squashing. Only a checker pass permits
squashing and deletion of the private `.beads` and `data` directories. For
an aborted or failed run it stops the private server and retains the
unsquashed scratch database as evidence. Never use `bd delete` or connect this fixture to the live
team database. If setup or cleanup cannot be proven safe, stop and report it.
