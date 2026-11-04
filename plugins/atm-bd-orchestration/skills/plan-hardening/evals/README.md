# Plan hardening live evaluations

Run cells sequentially: all four use the same isolated `eval-phase-z` fixture in
the current repository's bead database. Check that none of the five fixture IDs
already exists before importing; never overwrite an existing plan. Coordinate
ownership of the fixture with the other runner before starting a cell.

| Cell | Agent | Runner | Run by |
| --- | --- | --- | --- |
| 1 | haiku | subagent | fenix |
| 2 | haiku | teammate | fenix |
| 3 | luna | subagent | arch-ctm, else solar |
| 4 | luna | teammate | arch-ctm, else solar |

Use `subagent.md` or `teammate.md` as the runner prompt. The agent under test
must not read `planted.json` before it finishes its review. Capture `check.sh`
output and the same agent's answers to all five post-run questions in the PR;
a debrief is evidence and never substitutes for a passing check.

Before fixture cleanup, the prompt runs `evals/check.sh eval-phase-z <runner>`.
The check is read-only and may be rerun. It requires every planted bead to have
a fix bead, six completed step verdicts, and the runner's ATM task lifecycle.
Do not squash the iteration or final wisp until after this check: squashing
removes the step beads the checker reads.

Only the runner prompt burns the fixture. After capturing the check and
squashing the evaluation wisps, identify and remove only plan-fix beads created
under this fixture, then delete the five fixture IDs together:

```sh
bd delete --force eval-phase-z eval-z-1 eval-z-2 eval-z-3 eval-z-4
```

Do not use `--cascade`. Before deleting, ensure no unrelated bead is linked to
the fixture; stop and report any unexpected dependency. The prompt must not
burn a failed run before its evidence is captured.
