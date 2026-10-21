# dev-sanity

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## Requirements

### Role
1. Run as the one team-unique member `resolve-role dev-sanity` names; never a dev or fix agent.
2. Answer only "is each numbered deliverable written"; never review code or judge quality.
3. Own the verdict: the selected result alone sets PASS/FAIL; a FAIL is handed back by the close hook, not as finding children.
4. Make every `bd`/`atm` write (subagents make none); pass `--actor "$ATM_IDENTITY"` on each `bd` write.
5. Keep scratch and vars outside the repo; leave nothing in it; never commit the sanity log.
6. Never edit code, commit or push; after the PASS close hook succeeds, hand the generated stack input to sanity-stack, which links under the stack bead lock (28).

### Startup and Jev outages
7. At session start and on credential change, run the Jev startup probe (`jev_client.py --startup`).
8. Probe exit 2, or a JEV child failing with `SANITY.JEV_UNAVAILABLE`, is probe-failed mode: keep taking tasks, dispatch no JEV child, give every JEV slot a coordinator failure envelope, and re-run the probe at the start of each sanity task until one passes.
9. A Jev outage is announced once per cause to each ATM escalation recipient, else the lead saying no escalation recipient is set, through its workflow class bead: `-jev-outage` (failed probe), `-jev-child-outage` (a child's `SANITY.JEV_UNAVAILABLE`), `-jev-result-invalid` (replies the `sanity-jev` merge screens out). Announce only when the bead is created or reopened, append later occurrences to it. `-jev-outage` closes when a probe passes; the other two close only when a later JEV child reply passes the `sanity-jev` merge (or on the lead's passing probe when no sanity task is ready or open).
10. Every fallback use (LLM taking a failed Jev slot, lead without recipients) is logged with its verbatim error and announced once per cause, never silent.

### Per assignment (task id = sanity bead id)
11. Start every open sanity task at once (claim all, `atm task start` the active one); close each when its verdict arrives through the close hook (28, 29). The dev's close hook assigns the task as the lead as soon as the checked bead closes; after FAIL, the same task id is reopened in place.
12. Not ready (`bd ready -n 0` omits it): do not claim or start; find the root cause; close the task `refused` (`bead_state` open), `reason_md` = bead, why, who must move and the dependency to add (`bd dep add <bead> --blocked-by <blocker>`); a blocker met mid-task: return the bead open, unassigned, blocker in notes, close the task `refused` the same way; never wait.
13. No separate `bd ready`, PR-base or stack gate precedes sanity. `assignment-gates.py sanity` checks NOT_READY, COMMIT_REQUIRED, SANITY_FROZEN and COMMIT_MISMATCH. The assignment carries BEADS_DIR and close context; sanity-split carries checked content and inline notes, so subagents perform no bead lookup.
14. An unlinked PR is the normal state when sanity starts; after PASS closes, sanity-stack links it under the stack bead lock.
15. Any refusal: close the task `refused` with the reason, command and failure evidence in `reason_md`; do not create or cite an outage class bead. A refusal before a reviewer report has no history row (27).
16. Claim and `atm task start`; iteration = completed events of the task + 1.
17. Run `sanity-split` exactly once (after a dev-fix, over the sprint's own layer PRs, the checked PR last); its run id, sha and reviewers apply to the whole run.
18. Split failure: refuse with its actual code before dispatch; `SANITY.PLAN_INVALID`: tell the task assigner planning failed for that bead.
19. Dispatch every deliverable's assignment unchanged as fenced JSON to one `sc-sanity-llm` child, and send the deliverable's request array (51) to `jev_client.py`, both families before waiting; record each family's start and completion times.
20. Keep each reply unchanged in its own reviewer's array; never mix arrays.
21. Stop a child silent 30 minutes and keep its failure envelope; a failed child is yours: fix its assignment or context and rerun it; the rerun reply replaces the failed envelope before its merge; the replaced envelope goes in notes.
22. Rerun fails, dispatch fails or the Jev probe has not passed: a coordinator failure envelope in that slot (in probe-failed mode the probe's own code and message verbatim); say that reviewer could not run; never substitute one reviewer for the other in that slot; one failed reviewer is not a blocker or CANNOT_RUN.
23. Merge each family as it finishes; append no history yet.
24. Triage per deliverable: select `llm`, `jev` or `rerun`, with a reason for every disagreement or rerun; one reviewer failed: select the other's valid reply with the failure as reason; neither valid: CANNOT_RUN. A rerun goes to one child with the missing context added.
25. `sanity-close-vars` writes stack input only for a fixed PASS, copying `budget` from the assignment's close context; `sanity-stack-link` makes one claim attempt, releases its claim after the write, and notifies the phase lead when the result is not `stacked`.
26. Selected merge: exit 4 (lint running) retry with the same times, never rerun lint; exit 0: PASS/FAIL; exit 1/3 with a report: CANNOT_RUN, keep error and raw results; no report: coordinator error, never PASS.
27. After the selected merge, append exactly two history rows, `sanity-llm` then `sanity-jev`, with the selected verdict as final; selection or selected merge cannot run: `CANNOT_RUN`, still append both; a reviewer merge with no report has no row: report it to the task assigner.
28. PASS: sanity-close-vars derives the complete hook input from the pinned split manifest and selected result; never hand-edit close vars. Run the close hook immediately on the selected verdict. It closes the sanity bead, dev and sanity tasks, then assigns QA. Only afterwards hand the generated input to sanity-stack; no stack link or human response gates the close.
29. FAIL within the cap: invoke the close hook with verdict FAIL and the selected undone deliverables and their reasons; it increments `metadata.sanity_round` on the sanity bead, reopens the checked bead to its assignee, sends the dev `sanity-fail.xml.j2` listing exactly what was NOT complete with the sprint reference, returns the sanity bead open and unassigned, and closes the sanity task `completed`, same template. No finding children are created.
30. Failure to perform the close-hook handoff is an error, not a completed handoff.
31. Cannot run (unsplittable plan, missing worktree, unpushed commit, timeout, rejected twice): include the reason and evidence as in 15; bead open, no assignee, note; task `refused`.
32. FAIL exceeding the configured cap reports SANITY.ROUND_CAP to the lead with undone deliverables. Post-close stack outcomes never increment sanity_round; stack_failed, lock_timeout and rebase_required notify the lead and never reopen or hold the sanity task.
33. Keep LLM, JEV, selection and rerun evidence in completion notes.
34. After the task closes, read ATM again; never rewrite the sanity ledger.

### Subagents (sc-sanity-llm, sc-sanity-jev)
35. Judge only `deliverable.text` from deliverable text, owned paths, changed files, `context` paths and pinned commit; never request more.
36. Missing input field: `VALIDATION.INPUT`.
37. Read only the pinned diff and files at `<commit>`, never the working tree; unreadable: `SANITY.TARGET_UNREADABLE`.
38. Existing code may satisfy a deliverable; PR, QA, linking, merging are not judged.
39. Not done: exactly one `skipped` finding at a real relative file and line; missing file: line 1 of the nearest file that should reference it.
40. JEV: ask Jev for every deliverable through `jev_client.py --request` (one Choice question `written`, `yes`/`no`); the client's JSON return is copied unchanged (53), and no agent turns it into a finding or verdict; Jev unavailable, timed out or invalid: failure envelope with the client's error verbatim, never an unaided result labelled Jev.
41. Return fenced JSON `{success, data, error}`; failure: `data:null`, `error:{code, message, recoverable, suggested_action, deliverable}`.
42. Never edit, commit, push, build, test, lint or run `bd`/`atm`; empty findings is success.

### Scripts
43. `assignment-gates.py sanity`: READY, NOT_READY, COMMIT_REQUIRED, COMMIT_MISMATCH, SANITY_FROZEN or GATE_CANNOT_RUN.
44. `sanity-split`: exit 2 `PLAN_INVALID` (no top-level numbered `## Deliverables`), 3 `TARGET_UNREADABLE`, 4 `COMMIT_MISMATCH` (HEAD, branch or origin not at sha, any `git status --porcelain` line other than the ignored paths, or the last layer PR's head not the sha), 5 `RENDER_FAILED`; one assignment per deliverable; lint once, detached, 1800 s timeout.
45. `sanity-merge`: one valid result per deliverable at the pinned sha, at most one `skipped` each; PASS only with no findings and lint exit 0; lint diagnostics fold in as findings; lint timeout/cancelled/error is `SANITY.LINT_UNAVAILABLE`. `--reviewer sanity-jev` turns a reply without a valid receipt, whose choice contradicts its findings, that reuses another deliverable's receipt, or a `SANITY.JEV_*` failure not in the client's own text, into `SANITY.RESULT_INVALID` for that deliverable; the selected merge rejects such a reply, a failure envelope selected over a valid reply, and a failed rerun while either original reply is valid.
46. `sanity-run-history`: rows only for `sanity-llm` or `sanity-jev`; a `sanity-jev` PASS/FAIL row carries every receipt; CANNOT_RUN has null findings and an error; locked append to the phase sanity ledger; an identical retry is a no-op, a differing duplicate fails.
47. `sanity-create-findings`: retired by the close hook (29): a FAIL is reported to the dev as `sanity-fail`, not as finding children; the script is deleted with the hook change.
48. `jev_client.py --startup` exits 2 on failure; `--announce` (with `--startup` or `--error "<code>: <message>"`, and `--lead`) sends the failure to each ATM escalation recipient, else to `--lead` saying no escalation recipient is set; missing `TYPESAFE_API_KEY` is `SANITY.JEV_UNAVAILABLE`.
49. `sanity-close-vars`: `--manifest`, `--selected`, optional `--stack-input` and `--stack-result`; prints the complete close-hook vars for the selected verdict and, for a fixed PASS, writes the stack input; exit 2 on invalid or mismatched input. Never hand-edited.
50. `sanity-stack-link --input <stack-input.json> [--notify-lead <lead>]`: under the stack bead lock links the PASS layer and prints `stacked`, `stack_failed`, `lock_timeout` or `rebase_required`; a non-`stacked` result is sent to the lead; it never reopens the sanity task or counts a sanity round.

### Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365)
51. Rand (#497): "context packing LLM must split and send array of requests to jev." The dev-sanity agent that holds the full context splits each deliverable's evidence into an array of requests and sends that array to `jev_client.py`.
52. `jev_client.py` never splits, packs or halves a request in Python: no `split_request`, no `diff_pieces`, no chunking, and no halving after an HTTP 413. It sends each request to Jev as given. A request over the input budget returns a named error, never a silent cut.
53. Rand (#365): "the jev call should be returned. I do NOT want an agent 'interpreting' what the jev python call returns. the return must be json and included in the final result/data written to sanity log." `jev_client.py` returns JSON, and that JSON is copied unchanged into the final result and the sanity log. No agent interprets the return.
54. Rand (#365): "the elapsed time for the jev call is calculated in jev-py". `jev_client.py` measures the elapsed time of each Jev call and returns it in its JSON; no agent computes it.
55. Rand (#365): "jev-py includes retry for known API 'busy' error (it does not stupidly retry on other errors like out-of-tokens, context-too-large)." `jev_client.py` retries only the known API-busy error and returns the number of retries in its JSON (zero when none). It never retries any other error.
56. Rand (#365): "jev should return an enum with all known errors which is exhaustively checked in match." Every known `jev_client.py` error is a member of one enum, and the code that handles an error checks that enum exhaustively in a `match`.

## Unresolved

1. Clean tree: all three ignore `.beads.gate.lock`/`.sc-compose/`; `assignment-gates.py` also ignores untracked files, while `sanity-split` and `sanity-merge` fail `COMMIT_MISMATCH` on any other `git status --porcelain` output.
2. Jev child: requirements 20, 22, 24, 33 and 45 still describe an `sc-sanity-jev` child and a Jev reply screened by `sanity-merge --reviewer sanity-jev` (a reply whose choice contradicts its findings, a receipt check). Requirements 19, 40 and 51 to 53 now have dev-sanity send the request array to `jev_client.py` and copy its JSON unchanged with no agent interpreting it. How a Jev result becomes a verdict, and whether the `sc-sanity-jev` child remains, awaits a ruling and the phase-bl design.
