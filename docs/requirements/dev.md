# dev

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## Requirements

### All assignments

1. The task id is the bead id; `bd show <bead>` is the assignment; the bead wins over the template and the mismatch is reported.
2. Start a task only after the previous one is closed.
3. Work only on the assigned branch and worktree; run scripts from the primary checkout.
4. Never run `gh stack link/sync/rebase/merge` or `bd sync`; `--actor "$ATM_IDENTITY"` on every `bd` write.
5. Rebase onto `origin/<pr_target>`; a conflict is part of the work.
6. Run `assignment-gates.py dev` from the worktree.
7. `READY`: `bd update <bead> --claim`, then `atm task start <bead> "<one line>"`.
8. `NOT_READY`: do not claim or start; find the blockers (`bd show`, `bd blocked --json`); report bead, cause and who must move to the task assigner; wait.
9. Any other code: reuse a matching workflow class bead (append task id, head, command, evidence) and cite it in the refusal; none matches: report the signature to the task assigner and cite that message; never create a per-task bead.
10. Commit as items land and push early (`git push -u origin <branch>` first); a push or `atm send` closes nothing.
11. Never weaken a test, skip a criterion, or leave a placeholder.
12. Run `<test_command>` (and the bead's validation commands) to zero failures.
13. Rebase onto the stack's current top (`/sc-gh-stack-view --json`: the stack whose rows contain `<pr_target>`, its last open row's `branch`, or the trunk when none is open), re-run `<test_command>`, `git push --force-with-lease origin <branch>`, then `gh pr create --base <top> --head <branch> --fill` (never `--draft`) and run `/sc-gh-stack-view`.
14. Close bead and task together with the close template; vars from its `required_variables`, `task_id`/`sprint` unchanged, `commit` = pushed head, `rebased_onto` = the top, `pr_number`/`pr_url` = the PR, `stack_view` = the verbatim `/sc-gh-stack-view` output; vars file outside the repo.
15. The task close is the report; it returns to the task assigner. No copies.
16. After the close, read ATM; only then does the next task start.

### Dev (`dev-template`)

17. Read the bead: scope, deliverables, deletion targets, validation, acceptance criteria; `metadata.owned_paths` is the fence.
18. Read every `metadata.requirements` and `metadata.adrs` id; satisfy each; `NONE` but the work touches one: tell the task assigner before coding past it.
19. Read `policy_path` and every guideline it names for the languages touched.
20. Read the complete plan and enumerate all tasks that must be completed in the primary and any child beads; create an itemized private checklist outside the tracked tree with every task identified; work through the checklist one item at a time; then go through it again one item at a time and confirm each is fully met; nothing outside the bead's scope.
21. Close: `bd close --reason "dev complete at <short sha>"` + `dev-complete.md.j2` with deliverable inventory and gate output; deletion work adds `inventory_md`.
22. Cannot complete: class bead or escalation (9); `bd update --status blocked --assignee "" --append-notes "DEV_CANNOT_COMPLETE; ..."`; never `bd close`; task `refused` with `task-refused.md.j2`. Unfinished is a failure.

### Dev-fix (`dev-fix`)

23. Not ready while `closed` means never reopened.
24. Read the complete plan and enumerate all tasks that must be completed in the primary and any child beads (`bd list --parent <bead> --status open --json`); create an itemized private checklist outside the tracked tree with every task identified; work through the checklist one item at a time, closing each child when fixed (`bd close <child> --reason "<short sha>: <fix>"`); then go through it again one item at a time and confirm each is done.
25. Re-check the whole bead; re-read its requirements and ADRs.
26. Close as Dev 21, `deliverables_md` listing each finding and its fix.
27. Cannot complete: as Dev 22.

### Fix (`fix-assignment`)

28. Read the bead, its `metadata.sprint_bead`, and the finding's requirements and ADRs (`requirements_globs`, `adr_globs`); read `policy_path` and its guidelines.
29. Confirm the defect at the cited file:line; absent: no work, close `not_reproducible` with the file:line checked.
30. Fix every in-scope occurrence of the pattern; touch only what the remedy needs.
31. Close: `bd close --reason "fixed at <short sha>"` (or `"not reproducible: <file:line>"`) + `fix-complete.md.j2`, `outcome` `fixed` or `not_reproducible`; `commit`, `rebased_onto`, `pr_number`, `pr_url` and `stack_view` required for `fixed`, omitted for `not_reproducible`.
32. Cannot fix: class bead or escalation (9); `bd update --status open --assignee "" --append-notes "FIX_CANNOT_COMPLETE; ..."`; task `refused`. Never close a finding unfixed.

### Parallel quick fix (finder)

33. A change other live branches need never goes in your layer: stop and tell the task assigner the change and the branches it breaks.
34. Cut `fix/<thing>` from `origin/<base>` the lead picks, own worktree: only the change, compiler-forced implementors/call sites, one test for a bug; test passes; push; PR into `<base>`.
35. Sprint task stays open; continue on the rebased layer.

### Scripts

36. `assignment-gates.py dev` prints one code; exit 0 `READY`, 2 `GATE_CANNOT_RUN`, 5 otherwise.
37. Checks in order: `validate-plan` (`PLAN_INVALID`), in `bd ready` (`NOT_READY`), open and unassigned or self (`UNCLAIMABLE`), `pr_target`, the sprint container's for a poured dev bead, is `--pr-target` or its ancestor (`PR_TARGET_MISMATCH`), roster model fits `difficulty` (`DIFFICULTY_MISMATCH`), `origin/<pr_target>` ancestor of HEAD (`WRONG_BASE`).
38. Difficulty models (substring): hard fable/opus/astra; normal terra/opus/sonnet; fast luna.
39. `task-refused.md.j2`: `bead_state` `open` or `blocked-failed`.

## Unresolved

1. `SKILL.md` sanity-FAIL row: a finding bead closes with `dev-complete.md.j2`; `fix-assignment` closes with `fix-complete.md.j2`.
