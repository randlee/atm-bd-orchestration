# quality-mgr

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## Requirements

### All tasks

1. Stay long-running; the role wins over the repo's `.claude/agents/quality-mgr.md` where they differ.
2. Run every open task at once, each with its own background reviewers; close each when its verdict is ready, in any order.
3. After task start, run `atm task list --json`; treat every open task assigned to you as live.
4. One active ATM task: for the others, claim the bead, do the work, close the task without starting it.
5. Address the template's `lead`; copy a one-line summary to `cc` with `atm send --stdin` when it differs.
6. Cannot run: reuse a workflow class bead for the failure signature (append task, head, command, evidence), else report the signature to the lead; no per-task bead; return the bead open, unassigned, and close the task `refused` with `task-refused.md.j2`.
7. Build completion vars from the template's `required_variables`, this run only, outside the repo.

### QA round (`qa-template`)

8. Before claim: PR base = `metadata.pr_target`, PR head = sanity PASS commit, worktree HEAD = PR head; else refuse `SANITY_STALE`.
9. Claim, then `atm task start`.
10. Reject an assignment not rendered from the template; read `policy_path`.
11. Pipe the checked bead (and `sprint_bead` if set) with governing requirements/ADRs into `<scratch>/<task>-sprint.md`; it is `sprint_doc`.
12. Extract every deliverable, criterion, deletion, validation item and artifact; completion `X/Y (Z%)`.
13. The change is `git diff origin/<base>...<commit>`; read content with `git show <commit>:<path>`.
14. Round 1: run `reviewers_round1` plus conditional reviewers `policy_path` requires, each with `qa_round`.
15. Fix round: `fix-round-scope owned` names each carried finding's filing reviewer; dispatch exactly those, confirmed by `fix-round-scope check`; each locked to its own `finding_ref` ids; reduce each result with `fix-round-scope filter`.
16. Spawn every reviewer in the background; never run tests, linters or broad analysis in the foreground.
17. Re-verify every cited file:line at `<commit>`; stale or missing evidence is a finding (fix round: fails that carried finding).
18. Round 1: sweep the whole commit for every repeatable pattern; pass touched symbols as `duplicate_sweep_symbols` where a template takes it.
19. Round 1: screen every finding with `ceremony-finding-screen` (background).
20. Round 1: normalize severity (`critical`/`Blocking`/`BLOCKING` → blocking, `Important` → important, `Minor`/`low` → minor).
21. Round 1: file one finding bead per finding from `finding-bead.json.j2`, id `<task>-f<n>` in report order; copy `requirements`, `adrs`, `sprint_bead` and `difficulty` from the checked bead, never default `difficulty`.
22. Priority: blocking P1, important P2, minor P4; `blocked_by` only to another finding of this round.
23. Render each finding `--strict`, gate with `jq -e -c`, append to `<task>-findings.jsonl`; on failure fix vars and re-render, never skip; then `bd import`.
24. Apply the screen: `keep`/`not_applicable` open; `concern_valid_remedy_ceremony` open with remedy rewritten to the named mechanism; `ceremony` filed then closed with `ceremony: <reason>`.
25. Verify the import added only finding children and inter-finding edges; never add a finding edge to a planned sprint.
26. Fix round: file nothing; note each confirmed fix, `bd reopen` each regressed or open carried finding.
27. Never assign findings.
28. Verdict: only-minor is PASS; blocking or important is FAIL with one fix round; a second FAIL is `ROUND_CAP`, stop dispatch, record root cause.
29. With a PR: post `qa-complete.md.j2` as a PR comment, check stack/CI with `sc-gh-stack-view` and `gh pr checks --json name,state,bucket`; never `--watch`. No PR: say so in notes.
30. Close bead and task together whatever the verdict, with `qa-complete.md.j2`.
31. After the closes (never on refusal), append one row each to `.sc/qa-log/phase-<p>.jsonl` and `phase-<p>-stats.jsonl` under the lock, computed fresh; never hand-edit; correct with a workflow-issue bead plus a correcting row; never commit the logs.

### Plan review (`plan-review-template`)

32. Check readiness, claim, start; blocked: report the blocker to the lead and wait.
33. Run `validate-plan --root <root>`: exit 5 every line blocking; exit 2 cannot-run (`PLAN_REVIEW_CANNOT_RUN`); missing DAG html or `sprints.jsonl` and `bd doctor` errors are blocking.
34. Pipe each dev bead to `<scratch>/<bead>-plan.md` and the root to `<scratch>/<root>-plan.md`.
35. Pin reviewers to `integration_branch` at `git rev-parse origin/<integration_branch>`.
36. Round 1: missing/empty/mixed, unknown (outside New Ids), non-governing or unlisted touched requirement/ADR ids are blocking; never downgraded or screened out.
37. Round 1: run `req-qa` and `arch-qa` per dev bead file, `plan-scope-reviewer` in full over all files (report its `parallelism`), plus the other plan reviewers; screen findings except validate-plan and REQ/ADR ones, list each drop with reason.
38. Fix round: only filing reviewers via `fix-round-scope --plan`, locked; `validate-plan` still runs; no screen, no new findings.
39. Report findings one line each: `<bead> <severity> <reviewer> <field>: ...`; file no finding beads.
40. PASS (no blocking/important open): no findings → close bead; minor → assign bead to lead with notes, leave open. FAIL → bead open, unassigned, notes. Fix-round PASS: every carried finding fixed and validate-plan clean.
41. PASS or FAIL: close the task with `plan-review-complete.md.j2`.

### Phase-end review (`review-template`)

42. Check readiness, claim, start; not ready: report blockers to the lead and wait.
43. Require branch = root `integration_branch`, worktree HEAD = `<commit>`; read via `git show <commit>:<path>`; plan = `bd show <phase feature>` and children.
44. JEV post-mortem per `post-mortem.md`: inventory every phase finding (closed, nested); investigate every flagged result; dedupe; append raw evaluations to the phase JSONL with UTC, SHA, run IDs.
45. Record `post_mortem_jev`; model error is not PASS; no code findings: `not_applicable`; JEV unavailable: `unavailable`, review stays pending.
46. Make no code changes.
47. Re-verify every file:line at `<commit>`; report SUMMARY, FINDINGS, EXTRACTION-READINESS, RECOMMENDED-NEXT-SPRINTS, INTEGRATION POST-MORTEM.
48. Run `check-review-completion.py` on the vars; require exit 0; close bead and task with `review-complete.md.j2`.

### Subagents

49. Reviewers: background; get pinned `branch`, `commit`, `worktree_path`, `sprint_doc` where the template takes it; never run `bd` or write ATM.
50. Render each assignment from `<reviewer>-assignment.json.j2` (else the input `.claude/agents/<reviewer>.md` names) with `--json-escape-mode auto`, gate with `jq -e .`, send as fenced JSON; no free-form prompts.
51. `review_mode`: `arch-qa`/`schema-reviewer` `sprint_review` or `phase_end`; `ruthless-boundary-qa` maps itself.
52. `carry_forward_findings_json` = the reviewer's own `finding_ref` ids; never empty string.
53. `ruthless-boundary-qa` with `qa_round` > 1 and `plan-scope-reviewer` with `round_index` > 1 fail to render without carried ids.
54. `ceremony-finding-screen` gets `worktree_path`, `sprint_doc`, `findings`; returns `keep`, `not_applicable`, `concern_valid_remedy_ceremony` or `ceremony` per finding.

### Scripts

55. `fix-round-scope owned|check|filter --carried <file> [--plan]`: filing-reviewer map; check exit 5 `FIX_ROUND_DISPATCH_MISMATCH`; filter keeps only dispositions on own ids, unreported = `fixed`.
56. `check-review-completion.py <vars>`: verdict PASS/FAIL agrees with `integration_review`; PASS needs zero blocking, important, unresolved; `integration_commit` = `commit` (40-hex); post-mortem counts sum to total; `post_mortem_md` non-empty.
57. `assignment-gates.py qa --root --bead --pr-target --pr-number [--checked-bead]`: `READY`, `PR_REQUIRED`, `PR_TARGET_MISMATCH`, `SANITY_STALE`, `QA_HEAD_MISMATCH`, `GATE_CANNOT_RUN`; exit 0/5/2.

## Unresolved

1. Only-minor round: `roles/quality-mgr.md` says PASS; `qa-template.xml.j2` step i requires no finding filed open.
2. Phase-end findings: `roles/quality-mgr.md` says quality-mgr files them; `review-template.xml.j2` step c and `SKILL.md` say the lead files them.
3. Review bead writes: `review-template.xml.j2` step c forbids writing to beads; step d requires `bd close`.
4. Pending review: `roles/quality-mgr.md`/`review-template.xml.j2` b1 leave JEV-unavailable review pending; `check-review-completion.py` accepts only passed/failed.
5. QA refusal codes: `qa-template.xml.j2` step a refuses every mismatch as `SANITY_STALE`; `assignment-gates.py` returns `PR_REQUIRED`/`PR_TARGET_MISMATCH`/`QA_HEAD_MISMATCH`, and no template invokes it.
6. Metrics counts: `qa-template.xml.j2` step j reads top-level `.screen`/`.severity`; `finding-bead.json.j2` puts them under `metadata`, so counts are always 0.
7. Plan-review cap: `SKILL.md` says three rounds "as in `quality-mgr.md`"; no package source defines it.
8. Phase-end reviewer: `roles/quality-mgr.md`/`SKILL.md` say quality-mgr owns it; `SKILL.md` assigns `<reviewer>` and `review-template.xml.j2` is a single read-only reviewer with no reviewer set.
9. `qa-template.xml.j2` passes `qa_round` to every reviewer; only `ruthless-boundary-qa-assignment.json.j2` declares it.
10. Blocking findings: `roles/quality-mgr.md` and `qa-template.xml.j2` g file one finding bead per finding from `finding-bead.json.j2`; `formulas/README.md` has quality-mgr pour a finding-group per blocking finding (`bead-groups --findings`) with no finding bead.
