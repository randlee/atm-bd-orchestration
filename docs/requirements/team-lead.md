# team-lead

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## Requirements

### Sequencer

#### Startup
1. Verify `bd` (>=1.3.0), `atm`, `sc-compose`, `jq`, `gh` + `gh stack`; missing or old: stop, tell the user the install line; never work around it.
2. Check `ATM_IDENTITY` = `BEADS_ACTOR` (bare identity); mismatch or wrong value: no bead writes until fixed; empty: pass `--actor "$ATM_IDENTITY"` on every write.
3. Fill every repository value from `.claude/project/atm-bd-orchestration.yaml` (start vars from `repo_config.py json`); never default one.
4. Resolve each role member with `resolve-role <role>`; exit 2: role unmapped.
5. Put each long-running agent under its role: `atm send <agent> "Operate under <prompt> ..."` (`roles/quality-mgr.md`, `.claude/agents/dev-sanity.md`).

#### Plan gate
6. `bd doctor` error: report it; never import into or dispatch from that database.
7. Import gaps reported to you: supply the branch or status rulings asked for; nothing imports on a blocking gap.
8. Right after import and the pour, create `<root>-plan-qa` with no assignee; every sprint container blocks on it (running phase: `<root>-plan-qa-<n>`, blocking only the new containers).
9. Plan on origin `integration_branch`: the plan file `<plans_dir>/phase-<x>.jsonl` and `.atm-bd/phase-<x>.toml` committed by hand, never exported from beads; `sprint-review --root <root>` writes `phase-<x>-dag.html` locally, never committed or pushed; no viewer without `--view`.
10. Run `validate-plan --phase <x>` from the repo root; exit 0 or stop.
11. Check `bd ready -l phase-<x> -n 0` lists the plan-review bead and no dev bead; `bd ready --explain` shows the rest blocked.
12. `bd sync`.
13. Dispatch plan review (`plan-review-template.xml.j2`) to quality-mgr; no dev bead before it passes.
14. PASS closed: nothing. PASS handed back open with minor findings: fix each with `bd update`, then `bd close <root>-plan-qa --reason "minor fixes applied"`.
15. FAIL: author fixes the listed beads; rerun `validate-plan`; dispatch round+1, same task id, `carry_forward` = open finding lines; three rounds max.

#### Dispatch
16. Before the first dispatch, create the root's `integration_branch` from the base branch and push it.
17. Run `bd ready -l phase-<x> -n 0 --json` after every close; never cache it; never dispatch the phase root.
18. Route: plan review and QA to quality-mgr; dev to the member you pick for its `difficulty`; sanity to `resolve-role dev-sanity`; finding to the member you pick; a sanity finding (`metadata.sanity_finding`) is never dispatched alone: its checked bead goes to that bead's assignee with `dev-fix.xml.j2`; review to the phase-end reviewer.
19. Dev or finding bead: `git fetch origin && git worktree add -b <branch> <worktree> origin/<pr_target>`.
20. `bd update <bead> --assignee <agent>` before assigning.
21. Build vars from the template's `required_variables`, `task_id` = bead id, rest from bead metadata; vars files outside the repo.
22. Preview with `atm compose`; never render and paste a body.
23. `atm task assign <agent> --task-id <bead> --template <t> --vars <file>`.
24. Assignee by priority: frontier dev for blocking and dev, fast agent for important and minor (usual case, not a rule).
25. Dispatch the next sprint once its sanity blockers PASS; never wait on QA.

#### On each close
26. dev-complete: open the PR against `pr_target` and link it on the phase stack, then assign the sanity check.
27. Sanity PASS: verify branch base = `pr_target`; dispatch the group's poured QA bead (`checked_bead`, `sprint_bead` from its metadata; for a fix bead also `carry_forward` = the fix bead, `round` = its `metadata.round` + 1). Important or minor finding: create its QA bead from `qa-bead.json.j2` with `checked_bead` and `carry_forward` = the finding.
28. Sanity FAIL (first): verify children against the branch; close with reason any that judge correctness or quality; overrule, amend, split or reassign, never recreate; dev-sanity has reopened the checked bead; assign `dev-fix.xml.j2`.
29. Sanity FAIL (second, `SANITY.ROUND_CAP`): diff flagged files vs last PASS, check the base for foreign commits, then rule; no third round without it.
30. `SANITY.PLAN_INVALID`: planning failed for that bead.
31. qa-complete: nothing to file or pour (quality-mgr poured the fix groups); reopen a ceremony closure you disagree with (`bd reopen`); pick the member for each finding.
32. QA `ROUND_CAP` (FAIL at round 2): no further fix round.
33. fix-complete `fixed`: a poured fix bead needs nothing; for an important or minor finding bead create its sanity bead (`dev-sanity-bead.json.j2`, `dev_bead` and `parent` = the finding). `not_reproducible`: nothing.
34. review-complete: file each finding with `finding-bead.json.j2` (`qa_bead` = review bead; sprint, layer, requirements, adrs from the cited dev bead, root + union minus `NONE` when it spans sprints; `found_at_commit` = reviewed commit; `screen` = `keep` unless screened; `finding_ref` = `R-n`).
35. task-refused: read reason and bead state; reassign, split or `bd close --force --reason`; `blocked` bead: `bd update --status open --assignee <new>` before re-dispatch.
36. not-ready report: fix the named cause, tell the assignee to re-check; unwanted work: close the task `cancelled` with `task-refused.md.j2`.
37. After every bead write, `validate-plan --root <root>`; any problem: stop dispatching, report to the user; never repair the graph (`bd dep`, `--parent`).
38. DAG change: replan PR off the root's `integration_branch`, merged into it; in motion only fix-bead dependencies change.

#### Findings and decisions
39. Check a "blocking" finding's scope (requirement, code, ownership) before its priority; out-of-phase issues go to the owner's backlog with evidence.
40. Read the cited code at the reported commit and current head; separate defect from remedy; correct an overbroad remedy on the finding, keeping its evidence.
41. Reject process-artifact remedies lacking consumer, gate, defect and retirement condition; keep the real defect.
42. Unresolved decision: create a `decision` bead (question, options, contract, affected beads, cost of being wrong, provisional choice) for the user or their delegate; it blocks phase closure, never development.
43. Take conservative reversible provisional choices; hold only work that depends on a significant decision.
44. Never close an unresolved finding or claim PASS to release a queue; silence or elapsed time is not approval.
45. Create a `bd gate` and its edges only on the user's explicit instruction; human gates need recorded user agreement.

#### Stack
46. Be the only stack writer (`gh stack link/unstack/sync/rebase/merge`).
47. Link layers in completion order; record each bead's actual `layer` and `pr_target` at link time.
48. Parallel quick fix: pick the lowest base holding what the change needs; finder (or a background developer subagent when all are busy) cuts `fix/<thing>` from it; one QA round (`checked_bead` = finder's bead, `layer` = base); merge on PASS; tell each owner the base moved; record fix branch/PR in the finder's and every touched bead's notes.
49. Merge no PR into the integration branch or a stack layer without QA.
50. Verify branches read-only; never run a state-changing command in an assignee's worktree.

#### Sync
51. `bd sync` after import, after each close before the next `bd ready`, at phase end before landing: 0 continue; 1 report, keep working, retry next close; 2 or 4 stop dispatching, report; 3 retry next close.

#### Phase end
52. When only the root is open, land the stack on the root's `integration_branch`.
53. Create `<root>-review`; dispatch `review-template.xml.j2` with `branch` = `integration_branch`, `commit` = its fetched pinned head.
54. Land review-finding fixes on the integration branch; filing reviewers verify there; no full re-sweep.
55. Route open, regressed or unverified findings from the reconciliation back to their owners.
56. Confirm the report says `integration_review_passed` and its SHA equals the integration head; then close the root, merge to the base branch, `bd sync`.
57. Handover: send the incoming lead open task ids, open PRs and the stack number; announce the new lead.

#### Reports
58. Status: `sprint-report --table` (or `--detailed`); rows are never hand-typed.
59. DAG refresh: `sprint-review` (writes the HTML locally; never commits or pushes); Wyvern only with `--view`.
60. QA metrics: `/qa-report [N|--all]`, both `.sc/qa-log/` tables in the reply, timestamps converted to local.

#### Scripts
61. `validate-plan`: checks per its header; exit 0 valid, 5 problems, 2 cannot run; never edit it, the plan or the graph to pass.
62. `resolve-role <role>`: prints the role's member; exit 2 unmapped.
63. `transitions.py` `next_transition`: sanity PASS without QA → create QA bead; QA PASS with only minor open → PASS with backlog; QA FAIL round>=2 → ROUND_CAP; FAIL with blocking/important → one fix round; else wait.

### Swarm-master

None in the package.

## Unresolved

1. Plan Gate order: `SKILL.md`, `planning.md` run `sprint-review` then `validate-plan` vs `importing-md-plan.md` step 9 the reverse.
2. Integration branch timing: `SKILL.md` Dispatch creates it "before the first dispatch" vs Plan Gate, `sprint-review/SKILL.md`, `validate-plan` needing it on origin before plan review.
