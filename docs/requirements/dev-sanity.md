# dev-sanity

Sources: `agents/{dev-sanity,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-create-findings,assignment-gates.py}`, `assets/scripts/jev_client.py`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## Requirements

### Role
1. Run as the one team-unique member `resolve-role dev-sanity` names; never a dev or fix agent.
2. Answer only "is each numbered deliverable written"; never review code or judge quality.
3. Own the verdict: the selected result alone sets PASS/FAIL and creates finding children.
4. Make every `bd`/`atm` write; pass `--actor "$ATM_IDENTITY"` on each `bd` write.
5. Keep scratch and vars outside the repo; leave nothing in it; never commit `.sc/sanity-log/`.
6. Never edit code, commit, push or mutate a stack.

### Startup
7. At session start and on credential change, run `scripts/jev_client.py --startup --lead <lead>`.
8. Exit 2: keep taking tasks, dispatch no JEV child, give every JEV slot a coordinator `SANITY.JEV_UNAVAILABLE` envelope until a probe passes; stderr asks: send stdout to the lead. Persistent reviewer outage (no tokens or quota, missing or invalid key, retry budget exhausted, probe exit 2): announce it once per outage to each ATM escalation recipient (`atm escalation list --team "$ATM_TEAM" --json`, else `atm escalation list --json`, `.recipients`), else the lead.

### Per assignment (task id = sanity bead id)
9. Start every open sanity task at once (`bd update --claim` all, `atm task start` the active one); close each when its verdict arrives.
10. Not ready (`bd ready -n 0 --json` omits it): do not claim or start; find the root cause; report bead, why, who must move to the task assigner; wait.
11. Refuse `SANITY.PR_REQUIRED` without `pr_number` and `pr_url`.
12. PR head must equal `commit`, the PR must be in an open stack of `gh api repos/{owner}/{repo}/stacks` (GitHub's stacks, never local `gh stack` tracking) with its base the `head.ref` of the open PR before it (the stack's `base.ref` for its first open PR), and that base must be the checked bead's `pr_target` or a descendant of it, else refuse `SANITY.NOT_STACKED`; `git fetch origin` before the descendant check; a `pr_target` gone from origin holds when a merged PR of it has its merge commit in `origin/<base>`.
13. Refuse `SANITY.ZERO_DELTA` when `origin/<base>..<commit>` is empty, and `SANITY.NOT_REBASED` when `origin/<base>` is not an ancestor of `<commit>`.
14. Refuse `SANITY.DIRTY_TREE` on tracked changes beyond the ignored paths.
15. Refuse `SANITY_FROZEN` when `bd history <task>` records a prior PASS.
16. PR targeting neither `develop` nor `integrate/*`: check it with `gh-stack-view`; refuse an unregistered or unmergeable stack.
17. Any refusal: append evidence to the workflow class bead for that failure signature and cite it, else report the signature to the task assigner and cite that; no per-task bead; no history row.
18. Claim and `atm task start`; iteration = completed events in `atm task events <task> --all --json` + 1.
19. Run `sanity-split` exactly once, with `--layer-pr <n>` for each PR of the task's `layer_prs` (after a dev-fix: the sprint's own layer ranges, the checked PR last, whose head must be the sha); save the manifest; its run_id, sha, reviewers, operational_reviewer apply to the whole run.
20. Split failure: refuse with its actual code before dispatch; `SANITY.PLAN_INVALID`: tell the task assigner planning failed for that bead.
21. Dispatch every deliverable's assignment unchanged as fenced JSON to one `sc-sanity-llm` and one `sc-sanity-jev` child, both families before waiting; record each family's `started_at` before its dispatch.
22. Keep each fenced reply text unchanged, as a JSON string, in its own reviewer's array (`sanity-merge` parses the fence); never mix arrays.
23. Record each family's `completed_at` when its last reply or timeout arrives, before merge or lint wait.
24. Stop a child silent 30 minutes and keep its failure envelope; a failed child is yours: fix its assignment or context and rerun it; the rerun reply replaces the failed envelope in that reviewer's array before its merge; the replaced envelope goes in notes.
25. Rerun fails, dispatch fails or the Jev probe has not passed: coordinator `success:false, data:null` envelope with `code, message, recoverable, suggested_action, deliverable`; say that reviewer could not run; never substitute one reviewer for the other in that slot; one failed reviewer is not a blocker or CANNOT_RUN.
26. Merge each family with `sanity-merge --reviewer sanity-llm|sanity-jev --started-at --completed-at` as it finishes; append no history yet.
27. Triage per deliverable into `selection.json`: exact LLM/JEV statuses, `selected` (`llm`, `jev` or `rerun`), a reason for every disagreement or rerun, `checker_defect`, both reply hashes; record selected start and completion epochs; one reviewer failed: select the other's valid reply with the failure as reason; neither valid: CANNOT_RUN.
28. Rerun: the manifest's assignment with `context` set to the nonempty repo-relative missing-context `{path, why}` objects (`jq`), sent to one child; put its unchanged reply and reviewer in `rerun`.
29. Checker defect: only on a selected undone reply, with a reason; creates no child.
30. Merge `--reviewer sanity-selected --llm-vars --jev-vars --selection`.
31. Merge exit 4: retry with the same times, never rerun lint; exit 0: PASS/FAIL; exit 1/3 with a report: CANNOT_RUN, keep error and raw results; no report: coordinator error, never PASS.
32. After the selected merge, append exactly two history rows, `sanity-llm` then `sanity-jev`, each with its own completion time, the same iteration and the selected verdict as `--final-verdict`; selection or selected merge cannot run: `CANNOT_RUN`, still append both; a reviewer merge with no report has no row: report it to the task assigner.
33. Copy only SEL vars to `<scratch>/sanity-<task>-vars.json`.
34. Each checker defect: append the selection entry to the matching workflow class bead (or report to the task assigner); cite it in notes.
35. PASS: `bd close <task> --reason "PASS at <sha>"`; `atm task close completed --template dev-sanity-complete.md.j2`.
36. FAIL: `sanity-create-findings --reviewer sc-sanity-selected`; never edit the parent; then `bd reopen <checked bead> --reason "sanity FAIL at <sha>: <n> findings"`; `bd update <task> --status open --assignee "" --append-notes "FAIL at <sha>: <n> findings"`; task `completed`, same template.
37. Finding handoff failure is cannot-run, not FAIL.
38. Cannot run (unsplittable plan, missing worktree, unpushed commit, timeout, rejected twice): workflow class bead or task-assigner report as in 17; bead open, no assignee, note; task `refused` with `task-refused.md.j2`.
39. Second FAIL on the same checked bead: report `SANITY.ROUND_CAP` with undone deliverable numbers to the task assigner; no third round without a ruling.
40. Keep LLM, JEV, selection and rerun evidence in completion notes.
41. After the selected task closes, render the last ten runs: `set -o pipefail; test -s "$log" && tail -n 20 "$log" | jq -s '{runs: .}' | sc-compose render --strict --file sanity-run-table.md.j2 --var-file /dev/stdin`, `$log` being the path `sanity-run-history` printed.
42. Put the whole table (`S | PR | R | Find | Result | Match | Done | Iter`; `Match` = reviewer verdict equals final verdict; rows of other reviewers are skipped) in the user-visible reply before reading ATM again; never rewrite the ledger.
43. Ledger or render failure: report `SANITY.STATUS_TABLE_UNAVAILABLE`; never change a verdict.
44. Read ATM again.

### Subagents (sc-sanity-llm, sc-sanity-jev)
45. Judge only `deliverable.text` from deliverable text, owned paths, changed files, `context` paths and pinned commit; never request more.
46. Missing input field: `VALIDATION.INPUT`.
47. Read only with `git diff <base_sha>...<commit>` and `git show <commit>:<path>`; never the working tree; unreadable: `SANITY.TARGET_UNREADABLE`.
48. Existing code may satisfy a deliverable; PR, QA, linking, merging are not judged.
49. Not done: exactly one `skipped` finding at a real relative file and line; missing file: line 1 of the nearest file that should reference it.
50. JEV: confirm an undone conclusion with Jev through `python3 scripts/jev_client.py --request <file>` (one Choice question `written`, `yes`/`no`, at most 24000 bytes); Jev unavailable, timed out or invalid: failure envelope with the client's `SANITY.JEV_*`/`VALIDATION.INPUT` error and `deliverable`, never an unaided result labelled Jev.
51. Return fenced JSON `{success, data:{sanity_bead, dev_bead, deliverable, commit_checked=commit, findings}, error}`; failure: `data:null`, `error:{code, message, recoverable, suggested_action, deliverable}`.
52. Never edit, commit, push, build, test, lint or run `bd`/`atm`; empty findings is success.

### Scripts
53. `assignment-gates.py sanity`: READY, PR_REQUIRED, NOT_STACKED, ZERO_DELTA, NOT_REBASED, DIRTY_TREE (ignores `.beads.gate.lock`, `.sc-compose/`), SANITY_FROZEN or GATE_CANNOT_RUN.
54. `sanity-split`: one top-level `1.`..`N.` list under `## Deliverables` (else exit 2 `PLAN_INVALID`); exit 3 `TARGET_UNREADABLE`; exit 4 `COMMIT_MISMATCH` (HEAD, branch, any `git status` output, origin not at sha); exit 5 `RENDER_FAILED`; one assignment per deliverable with `context: []`; reviewers `[sanity-llm, sanity-jev, sanity-selected]`, operational `sanity-selected`; lint once, detached, 1800 s timeout.
55. `sanity-merge`: replies are envelopes or fenced JSON strings; one valid result per deliverable at the pinned sha, at most one `skipped` each; worktree still at sha, branch, clean; exit 4 while lint runs; lint timeout/cancelled/error is `SANITY.LINT_UNAVAILABLE`; lint diagnostics fold in as `lint` findings; PASS only with no findings and lint exit 0; `--completed-at` finite, >= start, <= now+5 s.
56. `sanity-merge` selected mode: verifies reply hashes, statuses, reasons, rerun context files at sha; accepts a reviewer's CANNOT_RUN vars; rejects a failure envelope selected over a valid reply; a selected failure envelope is cannot-run; checker-defect deliverables count done; findings carry their selected reviewer.
57. `sanity-run-history`: reviewer only `sanity-llm` or `sanity-jev`; CANNOT_RUN needs null findings and an error, never PASS/FAIL; strict render of `sanity-run-record.json.j2`, typed validation, UTC timestamps; locked compact append to `<primary checkout>/.sc/sanity-log/phase-<phase>.jsonl` (phase from the checked bead's `metadata.phase`, else the sprint); prints the ledger path; identical retry (ignoring `completed_local`) no-op, differing run/reviewer duplicate fails; commit, task, sprint, PR, iteration and `--final-verdict` equal across a run.
58. `sanity-create-findings`: FAIL vars only; run reports only with `sanity-selected` provenance; one open `bug` child per `skipped` finding (none for lint) with provenance and `sanity_finding`, labels `phase-<p>`, `stage:finding`, `stack:<s>`; blocking priority `clamp(parent-1, P1, P4)`; `blocks` only between its own children; idempotent per task/commit/finding_ref; writes `finding_bead_ids` to the vars; failure: `SANITY.FINDING_HANDOFF_FAILED`.
59. `jev_client.py --startup` requires `--lead`; failure sends the lead an ATM message and exits 2; missing `TYPESAFE_API_KEY` is `SANITY.JEV_UNAVAILABLE`.

## Unresolved

1. Clean tree: `assignment-gates.py` ignores untracked files and `.beads.gate.lock`/`.sc-compose/`; `sanity-split` and `sanity-merge` fail `COMMIT_MISMATCH` on any `git status --porcelain` output.
