# team-lead

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## Requirements

### Sequencer

#### Startup
1. Verify `bd` (>=1.3.0), `atm`, `sc-compose`, `jq`, `gh` + `gh stack`; missing or old: stop, tell the user the install line; never work around it.
2. Check `ATM_IDENTITY` = `BEADS_ACTOR` (bare identity); mismatch or wrong value: no bead writes until fixed; empty: pass `--actor "$ATM_IDENTITY"` on every write.
3. Fill `lead`, `cc` and every repository value from `.claude/project/atm-bd-orchestration.yaml` (start vars from `repo_config.py json`); never default one.
4. Resolve each role member with `resolve-role <role>`; exit 2: role unmapped.
5. Put each long-running agent under its role: `atm send <agent> "Operate under <prompt> ..."` (`roles/quality-mgr.md`, `.claude/agents/dev-sanity.md`).

#### Plan gate
6. `bd doctor` error: report it; never import into or dispatch from that database.
7. Import gaps reported to you: supply the assignee, branch or status rulings asked for; nothing imports on a blocking gap.
8. Right after import, create `<root>-plan-qa` assigned to `<qa_member>`, blocking every root sprint (running phase: `<root>-plan-qa-<n>` blocking only the new dev beads).
9. Plan on origin `integration_branch`: `sprints.jsonl` committed by hand, never exported from beads; `sprint-review --root <root>` publishes `phase-<x>-dag.html`; no viewer without `--view`.
10. Run `validate-plan --root <root>` from the repo root; exit 0 or stop.
11. Check `bd ready -l phase-<x> -n 0` lists the plan-review bead and no dev bead; `bd ready --explain` shows the rest blocked.
12. `bd sync`.
13. Dispatch plan review (`plan-review-template.xml.j2`) to quality-mgr; no dev bead before it passes.
14. PASS closed: nothing. PASS handed back open with minor findings: fix each with `bd update`, then `bd close <root>-plan-qa --reason "minor fixes applied"`.
15. FAIL: author fixes the listed beads; rerun `validate-plan`; dispatch round+1, same task id, `carry_forward` = open finding lines; three rounds max.

#### Dispatch
16. Before the first dispatch, create the root's `integration_branch` from the base branch and push it.
17. Run `bd ready -l phase-<x> -n 0 --json` after every close; never cache it; never dispatch the phase root.
18. Route: plan review and QA to quality-mgr; dev to its assignee; sanity to `resolve-role dev-sanity`; finding to the member you pick; review to the phase-end reviewer.
19. Dev or finding bead: `git fetch origin && git worktree add -b <branch> <worktree> origin/<pr_target>`.
20. `bd update <bead> --assignee <agent>` before assigning.
21. Build vars from the template's `required_variables`, `task_id` = bead id, rest from bead metadata; vars files outside the repo.
22. Preview with `atm compose`; never render and paste a body.
23. `atm task assign <agent> --task-id <bead> --template <t> --vars <file>`.
24. Assignee by priority: frontier dev for blocking and dev, fast agent for important and minor (usual case, not a rule).
25. Dispatch the next sprint once its sanity blockers PASS; never wait on QA.
26. Re-dispatch a closed task id only if you dispatched it; after a handover the outgoing lead does.

#### On each close
27. dev-complete: nothing.
28. Sanity PASS: verify branch base = `pr_target`; open the PR against it; create the QA bead from `qa-bead.json.j2` (child of the checked bead) and dispatch it. Finding: `checked_bead` = finding, `sprint_bead` = its `metadata.sprint_bead`, `carry_forward` = finding id, `round` = discovering QA round + 1 (1 from phase-end review).
29. Sanity FAIL (first): verify children against the branch; close with reason any that judge correctness or quality; overrule, amend, split or reassign, never recreate; `bd reopen` the checked bead; assign `dev-fix.xml.j2`.
30. Sanity FAIL (second, `SANITY.ROUND_CAP`): diff flagged files vs last PASS, check the base for foreign commits, then rule; no third round without it.
31. `SANITY.PLAN_INVALID`: planning failed for that bead.
32. qa-complete: nothing to file; reopen a ceremony closure you disagree with (`bd reopen`); pick the member for each finding.
33. QA `ROUND_CAP` (FAIL at round 2): no further fix round.
34. fix-complete `fixed`: create its sanity bead (`dev-sanity-bead.json.j2`, `dev_bead` and `parent` = the finding). `not_reproducible`: nothing.
35. review-complete: file each finding with `finding-bead.json.j2` (`qa_bead` = review bead; sprint, layer, requirements, adrs from the cited dev bead, root + union minus `NONE` when it spans sprints; `found_at_commit` = reviewed commit; `screen` = `keep` unless screened; `finding_ref` = `R-n`).
36. task-refused: read reason and bead state; reassign, split or `bd close --force --reason`; `blocked` bead: `bd update --status open --assignee <new>` before re-dispatch.
37. not-ready report: fix the named cause, tell the assignee to re-check; unwanted work: close the task `cancelled` with `task-refused.md.j2`.
38. After every bead write, `validate-plan --root <root>`; any problem: stop dispatching, report to the user; never repair the graph (`bd dep`, `--parent`).
39. DAG change: replan PR off the root's `integration_branch`, merged into it; in motion only fix-bead dependencies change.

#### Findings and decisions
40. Check a "blocking" finding's scope (requirement, code, ownership) before its priority; out-of-phase issues go to the owner's backlog with evidence.
41. Read the cited code at the reported commit and current head; separate defect from remedy; correct an overbroad remedy on the finding, keeping its evidence.
42. Reject process-artifact remedies lacking consumer, gate, defect and retirement condition; keep the real defect.
43. Unresolved decision: create a `decision` bead (question, options, contract, affected beads, cost of being wrong, provisional choice) for the user or their delegate; it blocks phase closure, never development.
44. Take conservative reversible provisional choices; hold only work that depends on a significant decision.
45. Never close an unresolved finding or claim PASS to release a queue; silence or elapsed time is not approval.
46. Create a `bd gate` and its edges only on the user's explicit instruction; human gates need recorded user agreement.

#### Stack
47. Be the only stack writer (`gh stack link/unstack/sync/rebase/merge`).
48. Link layers in completion order; record each bead's actual `layer` and `pr_target` at link time.
49. Parallel quick fix: pick the lowest base holding what the change needs; finder (or a background developer subagent when all are busy) cuts `fix/<thing>` from it; one QA round (`checked_bead` = finder's bead, `layer` = base); merge on PASS; tell each owner the base moved; record fix branch/PR in the finder's and every touched bead's notes.
50. Merge no PR into the integration branch or a stack layer without QA.
51. Verify branches read-only; never run a state-changing command in an assignee's worktree.

#### Sync
52. `bd sync` after import, after each close before the next `bd ready`, at phase end before landing: 0 continue; 1 report, keep working, retry next close; 2 or 4 stop dispatching, report; 3 retry next close.

#### Phase end
53. When only the root is open, land the stack on the root's `integration_branch`.
54. Create `<root>-review`; dispatch `review-template.xml.j2` with `branch` = `integration_branch`, `commit` = its fetched pinned head.
55. Land review-finding fixes on the integration branch; filing reviewers verify there; no full re-sweep.
56. Route open, regressed or unverified findings from the reconciliation back to their owners.
57. Confirm the report says `integration_review_passed` and its SHA equals the integration head; then close the root, merge to the base branch, `bd sync`.
58. Handover: send the incoming lead open task ids, open PRs and the stack number; announce the new lead.

#### Reports
59. Status: `sprint-report --table` (or `--detailed`); rows are never hand-typed.
60. DAG refresh: `sprint-review` (pushes only the HTML on `integration_branch`; rejected push is failure; never force-push); Wyvern only with `--view`.
61. QA metrics: `/qa-report [N|--all]`, both `.sc/qa-log/` tables in the reply, timestamps converted to local.

#### Scripts
62. `validate-plan`: checks per its header; exit 0 valid, 5 problems, 2 cannot run; never edit it, the plan or the graph to pass.
63. `resolve-role <role>`: prints the role's member; exit 2 unmapped.
64. `transitions.py` `next_transition`: sanity PASS without QA → create QA bead; QA PASS with only minor open → PASS with backlog; QA FAIL round>=2 → ROUND_CAP; FAIL with blocking/important → one fix round; else wait.

### Swarm-master

None in the package.

## Unresolved

1. Important-finding priority: `atm-bd-orchestration/SKILL.md` (Stack Discipline, Priority) P2 vs `atm-beads/resources/orchestrating.md` P3.
2. QA bead parent: `SKILL.md`, `planning.md` child of the checked bead vs `orchestrating.md` parent the phase feature.
3. Finding parent/edges: `planning.md` parent = `sprint_bead`, no `caused-by` to the sprint vs `orchestrating.md` parent the phase feature, `caused-by` dev N.
4. Plan Gate order: `SKILL.md`, `planning.md` run `sprint-review` then `validate-plan` vs `importing-md-plan.md` step 9 the reverse.
5. Integration branch timing: `SKILL.md` Dispatch creates it "before the first dispatch" vs Plan Gate, `sprint-review/SKILL.md`, `validate-plan` needing it on origin before plan review.
6. Plan-review bead step: `importing-md-plan.md`, `planning.md` cite Plan Gate "step 2" vs `SKILL.md` step 1.
7. Plan-review cap: `SKILL.md` three rounds "as in quality-mgr.md" vs `roles/quality-mgr.md` stating no plan-review cap.
8. Blocking findings: `formulas/README.md` has no finding bead (a poured fix group under a sprint container the lead closes) vs `SKILL.md` Loop finding beads dispatched with `fix-assignment`; `bead-groups` not referenced from `SKILL.md`.
9. PR timing: `SKILL.md` Stack Discipline has the lead open the PR after sanity PASS; `dev-sanity-template.xml.j2` and `agents/dev-sanity.md` refuse `SANITY.PR_REQUIRED` without a PR.
