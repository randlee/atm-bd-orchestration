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
17. Run `bd ready -l phase-<x> -n 0 --json` after every close, before any other work, and dispatch every ready bead; assign a bead only while `bd ready` lists it; order and hold work only with bead edges, gates and `atm task move`, never by telling an agent not to run a task in its queue; never cache it; never dispatch the phase root. The lead may step in at critical points, preferably through a background developer subagent; lead work is never part of the original plan.
18. Route: plan review and QA to quality-mgr; dev to the member you pick for its `difficulty`; sanity to `resolve-role dev-sanity`; finding to the member you pick; a sanity finding (`metadata.sanity_finding`) is never dispatched alone: its checked bead goes to that bead's assignee with `dev-fix.xml.j2`; review to the phase-end reviewer.
19. Important or minor finding: when you assign it, create its sanity bead (`dev-sanity-bead.json.j2`, `dev_bead` = the finding) and its QA bead (`qa-bead.json.j2`, `checked_bead` = the finding, `blocked_by` = the sanity bead), each with `parent` = the finding's parent, in one `bd import`; a minor finding left in the backlog gets neither until it is assigned. Dev or finding bead: `git fetch origin && git worktree add -b <branch> <worktree> origin/<top>`, the current top of its stack (its `pr_target` or a descendant), passed as the assignment's `pr_target`.
20. `bd update <bead> --assignee <agent>` before assigning.
21. Build vars from the template's `required_variables`, `task_id` = bead id, rest from bead metadata; vars files outside the repo.
22. Preview with `atm compose`; never render and paste a body.
23. `atm task assign <agent> --task-id <bead> --template <t> --vars <file>`.
24. Assignee by priority: frontier dev for blocking and dev, fast agent for important and minor (usual case, not a rule).
25. Dispatch the next sprint once its sanity blockers PASS; never wait on QA.

#### On each close
26. dev-complete: verify the dev's PR and link it on top of the phase stack (`/sc-gh-stack`), run `/sc-gh-stack-view` and fix any stack problem yourself; append `layer PR #<n> <url>` to the checked bead's notes; never message or re-dispatch the dev for stacking; then assign the sanity check (after a dev-fix with `layer_prs` = the sprint's layer PRs, its first layer's (`gh pr view <metadata.pr_target> --json number`) first and the checked PR last).
27. Sanity PASS: verify the PR base is `pr_target` or a descendant of it; dispatch the group's poured QA bead (`checked_bead`, `sprint_bead` from its metadata; `base` = the PR base; after a dev-fix also `layer_prs` = the sprint's layer PRs, its first layer's (`gh pr view <metadata.pr_target> --json number`) first and the checked PR last; for a fix bead also `carry_forward` = the fix bead, `round` = its `metadata.round` + 1). Important or minor finding: the group's QA bead is now ready; dispatch it with `checked_bead` and `carry_forward` = the finding.
28. Sanity FAIL (first): verify children against the branch; close with reason any that judge correctness or quality; overrule, amend, split or reassign, never recreate; dev-sanity has reopened the checked bead; assign `dev-fix.xml.j2` on a new layer: cut its branch and worktree from the current top of the stack, record the sprint's first layer's branch as the checked bead's `metadata.pr_target` (`bd update <bead> --set-metadata pr_target=<branch>`; a later dev-fix keeps it) and pass it as `pr_target`; never rebase or re-target a linked layer.
29. Sanity FAIL (second, `SANITY.ROUND_CAP`): diff flagged files vs last PASS, check the base for foreign commits, then rule; no third round without it.
30. `SANITY.PLAN_INVALID`: planning failed for that bead.
31. qa-complete: nothing to file or pour (quality-mgr poured the fix groups); reopen a ceremony closure you disagree with (`bd reopen`); pick the member for each finding.
32. QA `ROUND_CAP` (FAIL at round 2): no further fix round.
33. fix-complete `fixed`: verify the dev's PR and link it on top of the phase stack, fixing any stack problem yourself, and append `layer PR #<n> <url>` to the fix bead's notes; then a poured fix bead or an important or minor finding bead needs nothing more: the group's sanity bead is now ready. `not_reproducible`: close a poured fix bead's or an important or minor finding bead's group sanity bead, then its QA bead, with reason `not_reproducible: <fix bead>`.
34. review-complete: file each finding with `finding-bead.json.j2` (`qa_bead` = review bead; sprint, layer, requirements, adrs from the cited dev bead, root + union minus `NONE` when it spans sprints; `found_at_commit` = reviewed commit; `screen` = `keep` unless screened; `finding_ref` = `R-n`).
35. task-refused: read reason and bead state; reassign only once `bd ready` lists the bead (a blocker refusal: as 36), split or `bd close --force --reason`; `blocked` bead: `bd update --status open --assignee <new>` before re-dispatch. A sanity refusal for no PR, not stacked or not rebased is the lead's as stack writer: open, link or rebase by a new layer as `sc-gh-stack` prescribes and re-dispatch the sanity check, without interrupting or messaging the dev. A cannot-run caused by an announced outage (its workflow class bead open) is not re-dispatched until that bead closes; never force-close meanwhile. `REVIEW_PENDING_JEV`: file the code findings in its notes, re-dispatch only after the Jev outage clears, reusing the prior run IDs.
36. not-ready or blocker refusal (task `refused`, bead open): fix the named cause (a blocker that is not a bead, such as an unfiled fix, first gets a finding bead or workflow class bead, whichever fits), add the recommended dependency (or the right one) so `bd ready` holds the bead; when bd refuses it (one edge type per bead pair, no parent-child edge), add the edge to an open bead the blocker's work goes through instead, unless it already blocks the bead (a QA bead whose checked bead reopened: its sanity bead, reopened if closed), never removing an edge; re-assign the same task id, template and vars only once `bd ready` lists it; never answer it with "wait"; unwanted work: close the bead with a reason. An assignee silent past the re-nudge: announce it (Lead Role), `bd update <bead> --status open --assignee <new>`, re-assign the same task id with the same template and vars.
37. After every bead write, `validate-plan --root <root>`; any problem: stop dispatching, report to the user; never repair the graph (`bd dep`, `--parent`) beyond adding a dependency discovered in motion.
38. DAG change: replan PR off the root's `integration_branch`, merged into it; in motion only added dependencies change: to fix beads, and any dependency discovered in motion (sprint beads included, `bd dep add <bead> --blocked-by <blocker>`), never a replan.

#### Findings and decisions
39. Check a "blocking" finding's scope (requirement, code, ownership) before its priority; out-of-phase issues go to the owner's backlog with evidence.
40. Read the cited code at the reported commit and current head; separate defect from remedy; correct an overbroad remedy on the finding, keeping its evidence.
41. Reject process-artifact remedies lacking consumer, gate, defect and retirement condition; keep the real defect.
42. Unresolved decision: create a `decision` bead (question, options, contract, affected beads, cost of being wrong, provisional choice) for the user or their delegate; it blocks phase closure, never development.
43. Take conservative reversible provisional choices; hold only work that depends on a significant decision.
44. Never close an unresolved finding or claim PASS to release a queue; silence or elapsed time is not approval.
45. Create a `bd gate` and its edges only on the user's explicit instruction; human gates need recorded user agreement.

#### Stack
46. Be the only stack writer (`gh stack link/unstack/sync/rebase/merge`). Rebasing is done before sanity or QA is assigned and is the dev's, at dev-complete; the lead fixes only what the dev could not, or another stack problem, before dispatching sanity or QA, in its own worktree, and dispatches with the new `commit`, `base`, `pr_number` and `worktree_path`. A layer that has passed QA, or has layers above it, is never rebased, and a rebase never re-dispatches QA or sanity on any other layer.
47. Link layers in completion order; record each bead's actual `layer` at link time; `pr_target` changes only at a dev-fix (28).
48. Parallel quick fix: pick its `pr_target`, the lowest branch holding what the change needs; finder (or a background developer subagent when all are busy) cuts `fix/<thing>` from the stack top as a new layer; one QA round (`checked_bead` = finder's bead, `layer` = its layer, QA bead from `qa-bead.json.j2` with `quick_fix` true: no sanity check, and that `pr_target`); a failed QA: file each blocking finding in its `findings_md` as a finding bead (`finding-bead.json.j2`, `qa_bead` = the quick-fix QA bead) and dispatch it with `fix-assignment.xml.j2` to an idle roster agent (the finder when idle; a background developer subagent when all are busy), no sanity bead, on the same branch when nothing is linked above it, else a new layer cut from the stack top, then one more quick-fix QA bead; lands with the stack; others rebase onto the top at dev-complete; tell each owner the base moved; record fix branch/PR in the finder's and every touched bead's notes.
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
