# planner

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop).

## Requirements

### Start
1. Check `bd` (>=1.3.0), `atm`, `sc-compose`, `jq`; missing or old: stop, tell the user which and its install line; never work around it.
2. `ATM_IDENTITY` must equal `BEADS_ACTOR` (bare pane name); otherwise no bead writes until fixed (empty: pass `--actor "$ATM_IDENTITY"`).
3. Run `bd doctor --json`; any `"status": "error"`: stop, report to the lead.
4. Keep `<scratch>` (vars, renders, `plan.jsonl`) outside the repository.
5. Take repository values from `.claude/project/atm-bd-orchestration.yaml`; a missing file or key is an error, never a default.

### Shape the plan
6. Write the boundary map into the root's design first (crates/manifests changed, contract change, allowed edges); cut sprints from it.
7. Cut for the shortest critical path with the fewest sprints; concurrent sprints have disjoint `owned_paths`; sprints sharing a path are ordered.
8. Cross-boundary track: contract sprint, parallel layer sprints, one integration sprint per track; no phase-wide integration checkpoint.
9. Cut by layer only when it creates parallel work; a thin contract with one implementer and one consumer is one sprint with `vertical_rationale`.
10. No thin sprints: fold pass-through edits into the adjacent sprint's `owned_paths`.
11. One `closure_type` (`contract`, `boundary`, `integration`, `docs`) and one `target_boundary` per sprint; split mixed closure, >1 boundary without `vertical_rationale`, doubtful or twice-planned deliverables.
12. List behaviour through other crates under "This Sprint Does Not Close", naming the integration sprint that owns it.
13. Contract/boundary criteria rooted at the boundary or ADR; `req:<ID>` criteria only in integration sprints; each feature-level criterion in exactly one integration sprint.
14. `must_follow` only for a named, unhoistable contract artifact; never for a shared file (re-cut); default `parallel_safe`.
15. Publish the wave table in the root design (tracks, waves, `target_boundary`, `owned_paths`, critical path, width, count); justify every edge past a critical path of three.
16. Add a process artifact only with its consumer, gated capability, observed defect and retirement.
17. Put contract code samples in the contract sprint's design; layer sprints reference them.
18. Assignee from the roster (`policy_path`), preferring a named member; model tier in `model_class`.
19. Naming per "Plan Naming" at `policy_path`: lower case, `a-z0-9-` slugs, same slug in title and branch, worktree = branch, no `feature/`.

### Write the beads
20. One vars file per bead: root `plan-root` (`<prefix>-phase-<x>`), sprint `sprint-bead` (`<prefix>-<x>-<n>`), sanity `dev-sanity-bead` (`<dev id>-sanity`).
21. Root vars: `title`, `description` (goal + sprint table), `design`, `acceptance_criteria`, `plan_scope` (`feature` under the Development epic or `epic`, no parent), `integration_branch` = `integration_branch_pattern` with `{phase}`.
22. Sprint description: goal, numbered `## Deliverables` from 1 (each naming its REQ/NFR), required work, non-closure, paths to delete; design: contract, types, samples, targets; acceptance: criteria + validation commands.
23. Sprint metadata: `sprint`, `stack` = `phase-<x>`, `layer` (1 = bottom), `branch`, `pr_target` (layer n-1's branch; layer 1 the root's `integration_branch`), `worktree` = `<worktree_base>/<branch>`, `relation`, `closure_type`, `target_boundary`, `owned_paths`, `difficulty` (`hard`/`normal`/`fast`), `assignee` in `atm members`, `parent` = root.
24. `blocked_by` each prerequisite's sanity bead, never its dev bead.
25. `requirements` and `adrs`: every governing id or exactly `["NONE"]`; never empty, never mixed.
26. A not-yet-existing id only when its document is in `owned_paths` and a deliverable says the sprint adds it.
27. Sanity vars: `dev_bead` = its sprint, `assignee` = `resolve-role dev-sanity`; unmapped or not a member: ask the lead.
28. Render each strictly (`--strict --output <bead>.json && jq -e -c . <bead>.json >> plan.jsonl`); stop on any failure; never pipe a render into `jq`.
29. Hand-write `<plans_dir>/phase-<x>/sprints.jsonl`: one `[sprint, sanity_bead, [prerequisite sprints]]` per sprint; never generated from beads, nor beads from it.
30. `validate-plan --file plan.jsonl --root <root> --index <sprints.jsonl>`; exit 5: fix every problem and re-render.
31. `bd import --dry-run -i plan.jsonl`, then `bd import -i plan.jsonl`.
32. At once create `<root>-plan-qa` (`stage:plan-review`, assignee `<qa_member>`, parent root) blocking every root sprint.
33. Commit `sprints.jsonl` with the plan and push it to the root's `integration_branch`.
34. `sprint-review --root <root>` renders, commits and pushes `<plans_dir>/phase-<x>/phase-<x>-dag.html` (embedded SVG); no `--view` unless asked.
35. `validate-plan --root <root>`; exit 0 or stop and report.
36. Hand to plan review; nothing is dispatched until it passes.

### Import a markdown plan
37. Find the root (`bd list -l phase-<x> --type feature|epic -n 0`); exists: no new root, import under it, report root fields missing from the phase plan.
38. Map fields by the Mapping table (translation, never rewrite); drop merge-forward triggers, PR-completion trigger, per-sprint `base`, `status`.
39. Run every Checks row before rendering; collect all gaps; any blocking: `atm send <lead> --stdin`, one line `<doc>: <field>: <problem>` per gap, blocking first; import nothing.
40. Render and validate as items 28-30; any problem stops the import.
41. `bd show` each id; any exists: stop, use `bd update`.
42. Import as item 31, then `bd update <bead> --append-notes "imported from <doc path>@<short sha>"` on each sprint bead.
43. Plan-review bead as item 32; into a running phase: `<root>-plan-qa-<n>` (next free), blocking every new dev bead.
44. Items 33-35; then `bd ready -l phase-<x> -n 0` lists the plan-review bead and no imported dev bead, and `bd ready --explain` shows the rest blocked by plan review or prerequisite sanity beads.
45. Run `bd sync`.
46. Never edit, move or delete the markdown; never run the phase from both.

### Plan review FAIL
47. Fix the beads with `bd update`; next round with the same task id; at most three rounds.

### Replanning
48. Fix a DAG problem only by replanning: edit `sprints.jsonl` in a `/sc-git-worktree` branch off the root's `integration_branch`, merge the plan PR into it; beads and `sprints.jsonl` change in one commit.
49. While the phase runs the sprint DAG is frozen; only edges to phase-created fix beads change.
50. Keep `validate-plan --root <root>` green from plan approval to phase end.

### Never
51. Never create a gate bead or its edges without the user's explicit instruction for that gate.
52. Never repair the graph with `bd dep` or `--parent`.
53. Never re-import to update a bead.
54. Never put findings, fixes, QA, tasks, branches or gates in `sprints.jsonl`.
55. Never mark an unimplemented sprint bead `closed`.
56. Never edit the script, the plan or the graph to make validation pass.
57. Root children: only the sprint pairs, `stage:plan*` beads, gate beads and folded sprints; no `validates` or `caused-by` edge to a sprint.

### Scripts
58. `validate-plan`: each dependency has a `blocks` edge to the prerequisite's sanity bead and the prerequisite is a listed sprint; sprint and sanity beads pass their schemas; sanity `dev_bead` is its sprint with a `blocks` edge to it; every listed bead exists; no open non-epic top-level bead since the root; `bd doctor` clean.
59. `validate-plan` without `--index` reads `origin/<root integration_branch>:<plans_dir>/phase-<p>/sprints.jsonl`; root lacking `integration_branch` or fetch failure: exit 2; file missing: exit 5.
60. `validate-plan` exit 0 valid, 5 problems (`<bead>: <problem>`), 2 cannot run; `--root` required.
61. `bead_schema.py`: SprintBead needs assignee, numbered `## Deliverables` from 1, acceptance criteria, `requirements`/`adrs`, `worktree`, `branch`, `pr_target`, `difficulty`; SanityBead needs assignee, `dev_bead`, `blocks` edge to it.
62. `sprint_index_common.py`: exactly 3 fields per tuple, unique sprint and sanity, sanity != dev id, no self/duplicate/unknown deps; dev id `<prefix>-<sprint>`, prefix from root id else config `bead_prefix`.
63. `check-phase-artifact --root --index`: on `origin/<integration_branch>`, `sprints.jsonl` equals the local file and the DAG HTML embeds SVG with `meta phase-root-bead` = root; exit 5 otherwise.
64. `phase-index-path --root|--phase` prints `<plans_dir>/phase-<p>/sprints.jsonl`; `resolve-role <role>` prints the member from `roles:` in `.claude/agents/registry.yaml`, exit 2 unmapped; `repo_config.py` exit 2 on a missing file or key.
65. `plan_contract.py`: sprint priority 2; difficulty `hard`/`normal`/`fast` maps to model classes; severity priority blocking 1, important 2, minor 4.
66. Not scripted, checked by plan review: ids exist and govern the work, disjoint `owned_paths`, `relation`/`layer`/`pr_target` agree, assignees are members.

## Unresolved

1. `importing-md-plan.md` step 1 passes `--root <id> --phase <x>`; `validate-plan` rejects `--phase` (exit 2).
2. `planning.md` and `importing-md-plan.md` cite "Plan Gate, step 2" for the plan-review bead; `atm-bd-orchestration/SKILL.md` creates it in step 1.
3. `planning.md` says live-root validation checks the DAG HTML on the integration branch; `validate-plan` never checks it nor calls `check-phase-artifact`.
4. `orchestrating.md` says `validate-plan` runs every check in `planning.md` "Checks"; `planning.md` "Checks" assigns those to plan review.
5. `examples/sprint-bead-vars-d-4.json` and `-d-5.json` have bulleted Deliverables; `bead_schema.py` requires a numbered list from 1.
6. `planning.md` sprint required-vars table omits `difficulty`; `sprint-bead.json.j2` and `bead_schema.py` require it.
7. `importing-md-plan.md` step 5 validates with `--index sprints.jsonl`, which its step 9 writes.
8. `orchestrating.md` gives important findings P3; `atm-bd-orchestration/SKILL.md` "Priority" and `plan_contract.py` give P2.
9. `orchestrating.md` wires QA `validates` and finding `caused-by` edges to the dev bead; `planning.md` "Hierarchy" forbids both.
