# planner

**ID Range:** REQ-PLAN-0001 through REQ-PLAN-0058  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-26  
**Owner:** Rand Lee  

---

## REQ-PLAN-0001: Start

**Status:** Draft  
### Requirement Statement

Check `bd`, `atm`, `sc-compose`, `jq` at the skill's minimum versions; missing or old: stop, tell the user which and its install line; never work around it.


### Rationale

atm-beads SKILL.md Step 1 and references/installation-and-troubleshooting.md make the CLI check the first action and say a missing or old CLI stops the work with its install line, because every later plan step shells out to those tools.

### Success Criteria

**Acceptance Criteria:**

- [ ] Running the Step 1 loop in `atm-beads/SKILL.md` prints `ok` or `MISSING` for each of `bd`, `atm`, `sc-compose` and `jq`, and `bd version` reports 1.3.0 or newer.
- [ ] When a listed CLI is missing or below its minimum, the planner's report names that CLI and its install line from `references/installation-and-troubleshooting.md`, and no bead write follows.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0002: Start

**Status:** Draft  
### Requirement Statement

`ATM_IDENTITY` must equal `BEADS_ACTOR` (bare pane name); otherwise no bead writes until fixed; pass `--actor "$ATM_IDENTITY"` on every `bd` write.


### Rationale

resources/troubleshooting.md (Identity) says a `BEADS_ACTOR` that differs from `ATM_IDENTITY` is a stale or hand-set value and that bd would otherwise record the git `user.name` as the actor.

### Success Criteria

**Acceptance Criteria:**

- [ ] Before the first bead write, `echo "$ATM_IDENTITY" "$BEADS_ACTOR"` prints two identical bare pane names (no alias such as `<prefix>-lead`, no model class).
- [ ] Every `bd` write in the planner's session carries `--actor "$ATM_IDENTITY"`, and with differing values no `bd create`, `bd update` or `bd close` is issued.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0003: Start

**Status:** Draft  
### Requirement Statement

`bd doctor` error: stop, report to the lead.


### Rationale

planning.md 'Writing The Plan' step 1 and importing-md-plan.md step 0 stop the plan on a doctor error so nothing is imported into a database that doctor rejects.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd doctor --json` is run before the first render, and when any check has `"status": "error"` the planner writes no bead and sends the error to the lead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0004: Start

**Status:** Draft  
### Requirement Statement

Keep scratch (vars, renders, `plan.jsonl`) outside the repository; take repository values from `.claude/project/atm-bd-orchestration.yaml`, a missing file or key is an error, never a default.


### Rationale

atm-beads SKILL.md and planning.md ('Keep `<scratch>` outside the repository') keep rendered scratch out of the tree, and the atm-bd-orchestration 'Repository configuration' section makes a missing file or key a named error because scripts must never guess a repository value. CHANGELOG records the sprint-report and plan scripts reading the same file.

### Success Criteria

**Acceptance Criteria:**

- [ ] No vars file, rendered bead JSON or `plan.jsonl` produced during planning is under the repository working tree (`git status --porcelain` lists none).
- [ ] `repo_config.load` on a repository without `.claude/project/atm-bd-orchestration.yaml` raises `ConfigNotFound` naming the path, and reading an absent key raises `ConfigKeyMissing` naming the key; neither returns a default.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_repo_config.py::LoadTests::test_missing_key_is_a_named_error`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_repo_config.py::LoadTests::test_missing_file_is_a_named_error`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0005: Shape the plan

**Status:** Draft  
### Requirement Statement

Write the boundary map into the root's design first (crates/manifests changed, contract change, allowed edges); cut sprints from it.


### Rationale

atm-beads-plan-guidelines.md 'Plan From The Boundary Map' says sprints are cut from the boundary map, never from the feature list, because feature cuts force every sprint through the same crate stack and a serial chain.

### Success Criteria

**Acceptance Criteria:**

- [ ] The phase root bead's `design` contains a boundary map listing each crate or manifest changed, the contract change at each, and the allowed edges between them.
- [ ] Every sprint's `target_boundary` and `owned_paths` appear in that map.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0006: Shape the plan

**Status:** Draft  
### Requirement Statement

Cut for the shortest critical path with the fewest sprints; concurrent sprints have disjoint `owned_paths`; sprints sharing a path are ordered.


### Rationale

atm-beads-plan-guidelines.md opens with the objective of the shortest critical path with the fewest sprints and says sprints whose owned paths do not intersect run at the same time; sprints sharing a path must be ordered.

### Success Criteria

**Acceptance Criteria:**

- [ ] For every pair of sprints with no ordering between them, the `owned_paths` globs of the two beads match no common file.
- [ ] For every pair of sprints whose `owned_paths` intersect, one sprint's `.group-sanity` bead is in the other's blocker closure.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0007: Shape the plan

**Status:** Draft  
### Requirement Statement

Cross-boundary track: contract sprint, parallel layer sprints, one integration sprint per track; no phase-wide integration checkpoint.


### Rationale

atm-beads-plan-guidelines.md 'Plan From The Boundary Map' and 'Tracks And Balance' define the three-kind track and call one phase-wide integration checkpoint at the end an `OVER-SPLIT` finding.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each cross-boundary track in the plan has one contract sprint, layer sprints that depend only on it, and one integration sprint.
- [ ] No sprint is the single integration sprint depending on the integration or layer sprints of unrelated tracks.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0008: Shape the plan

**Status:** Draft  
### Requirement Statement

Cut by layer only when it creates parallel work; a thin contract with one implementer and one consumer is one sprint with `vertical_rationale`.


### Rationale

atm-beads-plan-guidelines.md 'Tracks And Balance' says to cut by layer only when two or more layer sprints can occupy separate developers, and that a thin contract with one implementer and one consumer is cheaper and correct as one sprint with `vertical_rationale`.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every sprint whose `target_boundary` spans two boundaries carries `vertical_rationale` in its bead, and a layer cut exists only where two or more layer sprints can run concurrently.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0009: Shape the plan

**Status:** Draft  
### Requirement Statement

No thin sprints: fold pass-through edits into the adjacent sprint's `owned_paths`.


### Rationale

atm-beads-plan-guidelines.md 'No thin sprints' states each sprint costs a worktree, a PR, a QA pass and a CI run, so pass-through edits are folded into the adjacent sprint.

### Success Criteria

**Acceptance Criteria:**

- [ ] No sprint bead exists whose only deliverable is a re-export, a threaded field or a few dozen lines; each such edit is listed in the `owned_paths` of the sprint that needs it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0010: Shape the plan

**Status:** Draft  
### Requirement Statement

One `closure_type` (`contract`, `boundary`, `integration`, `docs`) and one `target_boundary` per sprint; split mixed closure, >1 boundary without `vertical_rationale`, doubtful or twice-planned deliverables.


### Rationale

atm-beads-plan-guidelines.md 'Closure Types' and 'Split Early' require one closure type and one boundary per sprint and list the conditions that force a split, since acceptance criteria that mix closures let a deliverable slip while the sprint claims success.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each sprint bead's metadata has exactly one `closure_type` from `contract`, `boundary`, `integration`, `docs` and exactly one `target_boundary`.
- [ ] A sprint that owns more than one boundary has a `vertical_rationale`; otherwise the plan has split it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0011: Shape the plan

**Status:** Draft  
### Requirement Statement

List behaviour through other crates under "This Sprint Does Not Close", naming the integration sprint that owns it.


### Rationale

atm-beads-plan-guidelines.md 'Closure Types' and 'Production-Ready Expectation' say a boundary sprint does not claim behaviour passing through another crate and that open reach is not false closure when an integration sprint owns it.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each boundary sprint's description has a 'This Sprint Does Not Close' section naming every behaviour that passes through another crate.
- [ ] Each such entry names an integration sprint present in the plan.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0012: Shape the plan

**Status:** Draft  
### Requirement Statement

Contract/boundary criteria rooted at the boundary or ADR; `req:<ID>` criteria only in integration sprints; each feature-level criterion in exactly one integration sprint.


### Rationale

atm-beads-plan-guidelines.md 'Closure Types' says criteria rooted at a requirement id belong to an integration sprint and that a change in one crate must not reopen criteria owned by another crate's sprint; 'Tracks' adds that each feature-level criterion lives in an integration sprint exactly once.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every acceptance criterion in a `contract` or `boundary` sprint is rooted at `boundary:<id>` or an ADR section.
- [ ] Every `req:<ID>` criterion appears only in an `integration` sprint, and each feature-level criterion appears in exactly one such sprint.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0013: Shape the plan

**Status:** Draft  
### Requirement Statement

`must_follow` only for a named, unhoistable contract artifact; never for a shared file (re-cut); default `parallel_safe`.


### Rationale

atm-beads-plan-guidelines.md 'Ownership And Dependency Relations' says a shared file is a split defect, not a `must_follow` rationale, and that `parallel_safe` is the default; the CHANGELOG records the plan file as the minimum set of sprint edges.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each `must_follow` relation in the plan names one contract artifact (type, trait method, schema object or wire field) that the parent produces and that cannot move to the contract sprint.
- [ ] No `must_follow` rationale cites two sprints editing the same file.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0014: Shape the plan

**Status:** Draft  
### Requirement Statement

Publish the wave table in the root design (tracks, waves, `target_boundary`, `owned_paths`, critical path, width, count); justify every edge past a critical path of three.


### Rationale

atm-beads-plan-guidelines.md 'Ownership And Dependency Relations' requires the root's design to publish a wave table with critical path, width and sprint count, and a recorded reason for every edge that lengthens the critical path past three.

### Success Criteria

**Acceptance Criteria:**

- [ ] The phase root's `design` contains a wave table with, per track, sprints by wave, `target_boundary` and `owned_paths`, plus the numbers critical path, width and sprint count.
- [ ] Each `must_follow` edge on a chain longer than three sprints has a recorded reason.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0015: Shape the plan

**Status:** Draft  
### Requirement Statement

Add a process artifact only with its consumer, gated capability, observed defect and retirement.


### Rationale

CLAUDE.md 'Honest Work, No Ceremony' and atm-beads-plan-guidelines.md 'Process Artifacts' set the same four-part test; the CHANGELOG records `ceremony-qa` running over every sprint container and the root at plan review (plan-review-template 3.9.0) to enforce it.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every process artifact required by a sprint bead (manifest, inventory, ledger, receipt, matrix, docs-consistency check or new CI gate) names its consumer, the capability it gates, the observed defect and its retirement condition; an artifact missing any of the four is absent from the plan.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0016: Shape the plan

**Status:** Draft  
### Requirement Statement

Put contract code samples in the contract sprint's design; layer sprints reference them.


### Rationale

atm-beads-plan-guidelines.md 'Code Samples' says that in a phase with a contract sprint the samples live in that sprint's design and layer sprints reference them without restating, so the contract has one authoritative text.

### Success Criteria

**Acceptance Criteria:**

- [ ] In a phase with a contract sprint, each trait, enum, protocol type or boundary signature appears as a code sample in that sprint bead's `design`.
- [ ] Layer sprint beads' `design` fields reference those samples and do not repeat the code.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0017: Shape the plan

**Status:** Draft  
### Requirement Statement

Plan-time beads carry `difficulty` only, never an assignee; the lead picks the agent at dispatch.


### Rationale

atm-beads-plan-guidelines.md 'Difficulty' and atm-beads SKILL.md Identity say a planned bead carries only `difficulty` and that the assignee is set at dispatch; validate-plan warns on a plan-time assignee.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every sprint container bead has `metadata.difficulty` equal to `hard`, `normal` or `fast`, and an empty `assignee`.
- [ ] `validate-plan --file` on a plan bead with an assignee prints `warning: <id>: assignee set at plan time` on stderr.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::FilePlan::test_a_plan_bead_with_an_assignee_or_no_parent_is_a_warning`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0018: Shape the plan

**Status:** Draft  
### Requirement Statement

Naming per "Plan Naming" at `policy_path`.


### Rationale

atm-beads-plan-guidelines.md 'Naming' defers phase, sprint and branch names to one 'Plan Naming' convention per repository so that ids, labels and branches agree across beads.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each phase id, sprint id, label, branch and worktree name in the plan matches the 'Plan Naming' section of the file at `policy_path` (lower case, `a-z0-9-` slugs, sprint branch `sprint/<phase>-<n>-<slug>`, worktree directory equal to branch).

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0019: Write the beads

**Status:** Draft  
### Requirement Statement

Render one root bead (`plan-root`) and one sprint container per sprint (`sprint-bead`); the root's `integration_branch` comes from `integration_branch_pattern`.


### Rationale

planning.md 'Writing The Plan' maps the root and sprint container to the `plan-root` and `sprint-bead` templates, and the root `integration_branch` is required because validate-plan, sprint-review and every gate read the plan from that branch.

### Success Criteria

**Acceptance Criteria:**

- [ ] Rendering `plan-root.json.j2` yields a bead whose `metadata.integration_branch` equals the value derived from `integration_branch_pattern`.
- [ ] Rendering `plan-root.json.j2` without `integration_branch` fails and names that variable.
- [ ] Each sprint in the plan file has a `stage:sprint` container bead `<prefix>-<sprint>`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_plan_root.py::PlanRootTests::test_integration_branch_is_rendered_as_given`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_plan_root.py::PlanRootTests::test_integration_branch_is_required`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_missing_and_extra_sprint_beads`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0020: Write the beads

**Status:** Draft  
### Requirement Statement

Sprint description: goal, numbered `## Deliverables` from 1 (each naming its REQ/NFR), required work, non-closure, paths to delete; design: contract, types, samples, targets; acceptance: criteria + validation commands.


### Rationale

planning.md 'Sprint Container' tables fix what the description, design and acceptance_criteria fields hold; validate-plan checks the numbered deliverables and the CHANGELOG records sanity splitting a sprint by its numbered `## Deliverables`.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each sprint container's description contains a `## Deliverables` list numbered from 1, each item naming its REQ or NFR id, plus required work, a non-closure section and paths to delete.
- [ ] Its `design` holds the contract, types, samples and targets, and its `acceptance_criteria` holds the criteria and validation commands.
- [ ] A description of `none` makes `validate-plan` exit 5 with an `x-t-1: description:` problem line.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_noncontiguous_deliverables_are_a_warning`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0021: Write the beads

**Status:** Draft  
### Requirement Statement

Sprint metadata includes `owned_paths`, `closure_type`, `target_boundary`, `difficulty`, `branch`, `worktree`, `layer` and `pr_target`: the branch of the nearest `must_follow` prerequisite it builds on, never a parallel sibling; none: the root's `integration_branch`.


### Rationale

planning.md 'Sprint Container' lists the required metadata vars and defines `pr_target` as the branch of the nearest `must_follow` prerequisite so the stack lands in dependency order; validate-plan fails a container missing a required key.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each sprint container's metadata contains `owned_paths`, `closure_type`, `target_boundary`, `difficulty`, `branch`, `worktree`, `layer` and `pr_target`.
- [ ] `pr_target` is the `branch` of the nearest `must_follow` prerequisite, never a parallel sibling's, or the root's `integration_branch` when the sprint has none.
- [ ] `validate-plan` exits 5 with a `worktree:` or `difficulty:` problem line when either is missing or invalid.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0022: Write the beads

**Status:** Draft  
### Requirement Statement

Ordering is the plan file's `depends_on`; `bead-groups` blocks the dependent's dev bead on each prerequisite's sanity bead, never its dev bead.


### Rationale

planning.md 'Phase definition' says `depends_on` names hard prerequisites and `bead-groups` blocks the dependent's dev bead on the predecessor's sanity bead; validate-plan problem 5 fails a plan whose edge is missing.

### Success Criteria

**Acceptance Criteria:**

- [ ] For each `depends_on` line, the dependent's `<container>.group-dev` bead has a `blocks` edge to the prerequisite's `<pred>.group-sanity` bead.
- [ ] `validate-plan` exits 5 with `missing blocks edge to <pred>.group-sanity or <pred>` when the edge is absent, and exits 0 when the dev bead blocks on the predecessor sprint bead instead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_an_edge_to_the_predecessor_sprint_bead_also_satisfies_depends_on`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_a_missing_live_edge_is_a_problem`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_bead_pour_plan.py::PourPlanTests::test_sprint_formula_and_relations_for_every_option`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0023: Write the beads

**Status:** Draft  
### Requirement Statement

`requirements` and `adrs`: every governing id or exactly `["NONE"]`; never empty, never mixed.


### Rationale

planning.md 'Sprint Container' says `requirements` and `adrs` are never left empty because the dev reads each id before coding and QA checks the change against each one; `NONE` is an author claim plan review checks.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan` exits 5 with an `x-t-1: requirements:` problem when `metadata.requirements` is an empty list.
- [ ] `validate-plan` exits 5 with `adrs: mixes NONE with ids` when `adrs` is `["NONE", "ADR-1"]`.
- [ ] A sprint with no governing id carries exactly `["NONE"]` in that field.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0024: Write the beads

**Status:** Draft  
### Requirement Statement

A not-yet-existing id only when its document is in `owned_paths` and a deliverable says the sprint adds it.


### Rationale

planning.md 'New Ids' is the single stated exception to 'the id must exist' and says plan review, not validate-plan, checks both conditions.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every requirement or ADR id in a sprint's lists that is absent from the governing documents (`requirements_globs`, `adr_globs`) has its document in that sprint's `owned_paths`.
- [ ] A deliverable in the same sprint description names the id and says the sprint adds it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0025: Write the beads

**Status:** Draft  
### Requirement Statement

No dev, sanity or QA bead is planned: `bead-groups --phase <x>` pours each sprint's dev ← sanity ← qa group under its container after import; no assignee.


### Rationale

planning.md 'Dev Sanity Check Bead' says the sanity bead is not planned but poured by `bead-groups`, and planning.md step 5 pours every group after import; validate-plan warns on a group 'not poured yet' before import.

### Success Criteria

**Acceptance Criteria:**

- [ ] The rendered plan JSONL contains no bead labelled `stage:dev`, `stage:sanity` or `stage:qa`.
- [ ] After `bead-groups --phase <x>`, each sprint container has `.group-dev`, `.group-sanity` and `.group-qa` children with an empty `assignee`.
- [ ] `validate-plan --file` on containers whose groups are not poured exits 0 and prints `warning: <id>: not poured yet`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::FilePlan::test_a_new_plan_passes_before_its_groups_are_poured`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0026: Write the beads

**Status:** Draft  
### Requirement Statement

Stop on any render failure; never let a failed render drop a bead.


### Rationale

planning.md step 2 and importing-md-plan.md step 4 say a render piped straight into `jq` exits 0 on empty input and silently drops a bead, so the render chain `&&`-guards `jq`.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each bead is rendered with `sc-compose render --strict ... --output <file> && jq -e -c . <file> >> plan.jsonl`, and the number of JSONL lines equals the number of vars files rendered.
- [ ] A render that exits non-zero ends planning with no later bead rendered or imported.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0027: Write the beads

**Status:** Draft  
### Requirement Statement

Hand-write the plan file `<plans_dir>/phase-<x>.jsonl` (one `{"sprint", optional "depends_on"}` line per sprint). Create `.atm-bd/phase-<x>.toml` before validation or pouring with `phase-config init --phase <x> --lead <appointed-lead>`: explicit lead, repository-derived plan/root/integration branch, and seven existing installed template paths (`dev`, `dev_fix`, `fix`, `sanity`, `qa`, `plan_review`, `review`). The writer refuses to overwrite an existing phase; neither file is generated from beads, nor beads from it.


### Rationale

CHANGELOG 0.19.x records each phase file requiring its own `lead` and seven template paths with no repository or environment fallback, and planning.md 'Phase definition' says the file is never generated from beads nor beads from it.

### Success Criteria

**Acceptance Criteria:**

- [ ] `<plans_dir>/phase-<x>.jsonl` contains one JSON object per sprint with a `sprint` key and an optional `depends_on` list, and no other keys.
- [ ] `phase-config init --phase <x> --lead <name>` writes `.atm-bd/phase-<x>.toml` with that lead, `plan`, `root` and `integration_branch` derived from the repository configuration, and template paths for `dev`, `fix`, `sanity`, `qa`, `plan_review` and `review` that exist.
- [ ] `phase-config init` on an existing phase exits 2 with `already exists` and leaves the file byte-identical.
- [ ] `phase-config init` without `--lead`, with a blank lead, or with a missing installed template exits 2 and writes no file.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_phase_config.py::PhaseConfigTests::test_init_writes_explicit_lead_and_six_defaults_without_overwrite`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_phase_config.py::PhaseConfigTests::test_init_requires_lead_and_installed_templates_before_writing`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_phase_config.py::PhaseConfigTests::test_missing_lead_has_no_environment_or_repository_fallback`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0028: Write the beads

**Status:** Draft  
### Requirement Statement

`validate-plan` on the rendered plan; exit 5: fix every problem and re-render.


### Rationale

planning.md step 4 calls the validation of the rendered plan mandatory before import and says exit 5 lists every problem, so an invalid plan never reaches `bd import`.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --file <plan.jsonl> --phase <x> --index <plans_dir>/phase-<x>.jsonl` is run before `bd import` and its exit status is recorded.
- [ ] On exit 5 the planner re-renders after fixing every listed problem, and `bd import` runs only after a re-run exits 0.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_valid`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0029: Write the beads

**Status:** Draft  
### Requirement Statement

`bd import --dry-run`, then `bd import`, then `bead-groups --phase <x>`.


### Rationale

planning.md step 5 and importing-md-plan.md step 7 order the dry run before the import and the pour after it, because `bd import` upserts and `bead-groups` needs the containers present.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd import --dry-run -i <plan.jsonl>` exits 0 before `bd import -i <plan.jsonl>` is run.
- [ ] `bead-groups --phase <x>` runs after the import and before `validate-plan --phase <x>`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0030: Write the beads

**Status:** Draft  
### Requirement Statement

At once create `<root>-plan-qa` (no assignee, parent root); every sprint container blocks on it.


### Rationale

atm-bd-orchestration SKILL.md 'Plan Gate' step 1 says no dev bead is dispatched until plan review passes; the CHANGELOG (0.7.3) records the --id then `--parent` creation order because bd 1.3.1 refuses both flags together.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd show <root>-plan-qa` shows an open bead labelled `stage:plan-review`, parent `<root>`, and no assignee.
- [ ] Every sprint container has a dependency on `<root>-plan-qa`, so `bd ready -l phase-<x>` lists the plan-review bead and no dev bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0031: Write the beads

**Status:** Draft  
### Requirement Statement

Run `sprint-review --root <root>`: it writes the phase DAG HTML `<plans_dir>/phase-<x>/phase-<x>-dag.html` from the plan file in the working tree (the script never commits or pushes); no `--view` unless asked.


### Rationale

atm-beads SKILL.md and CHANGELOG record that the planner commits the phase DAG with the plan file and that `sprint-review` never commits or pushes; Wyvern opens only on `--view`.

### Success Criteria

**Acceptance Criteria:**

- [ ] After `sprint-review --root <root>`, the file `<plans_dir>/phase-<x>/phase-<x>-dag.html` exists in the working tree, `git status` shows it uncommitted, and no viewer process was started.
- [ ] The command was run without `--view` unless the user asked for a viewer.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_importing_docs.py::ImportingDocsTests::test_phase_index_instruction_is_an_import_procedure_step`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0032: Write the beads

**Status:** Draft  
### Requirement Statement

Commit the plan file, the phase file and the DAG together with the plan and push them to the `integration_branch`, then open a PR from it to the repository trunk before plan review; on a plan change, re-run `sprint-review` and commit the DAG with it, updating that PR.


### Rationale

CHANGELOG records the planner committing the DAG with the plan file and re-committing it on plan changes, and importing-md-plan.md step 9 requires the PR before plan review so reviewers read the plan from the integration branch.

### Success Criteria

**Acceptance Criteria:**

- [ ] One commit on the root's `integration_branch` contains `<plans_dir>/phase-<x>.jsonl`, `.atm-bd/phase-<x>.toml` and `phase-<x>-dag.html`, and it is pushed to `origin/<integration_branch>`.
- [ ] An open PR from `integration_branch` to the repository trunk lists those three files.
- [ ] After a plan change, the DAG file is in the same commit as the plan file change and the same PR is updated.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_importing_docs.py::ImportingDocsTests::test_phase_index_instruction_is_an_import_procedure_step`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0033: Write the beads

**Status:** Draft  
### Requirement Statement

`validate-plan --phase <x>`; exit 0 or stop and report.


### Rationale

atm-bd-orchestration SKILL.md 'Plan Gate' step 2 runs `validate-plan --phase <x>` after the push and says 'Exit 0 or stop'; the script reads the plan from the integration branch.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --phase <x>` exits 0 and prints `plan valid: <n> sprints` before the plan goes to review.
- [ ] On any other exit status the planner stops and reports the stdout and stderr to the lead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_reads_the_plan_from_the_integration_branch`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0034: Write the beads

**Status:** Draft  
### Requirement Statement

Hand to plan review; nothing is dispatched until it passes.


### Rationale

atm-bd-orchestration SKILL.md 'Plan Gate' states 'No dev bead is dispatched until the plan passes review', and the plan-review bead blocks every sprint container.

### Success Criteria

**Acceptance Criteria:**

- [ ] After the plan is handed to review, `bd ready -l phase-<x> -n 0` lists only the plan-review bead and no dev bead, and no ATM task is assigned for a dev bead until the plan-review bead closes with PASS.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0035: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Find the root; exists: no new root, import under it, report root fields missing from the phase plan.


### Rationale

importing-md-plan.md step 1 says an existing phase root is not re-rendered; the sprints are imported under it and its fields are only checked against the phase plan.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd list -l phase-<x> --type feature -n 0` (or `--type epic`) is run first; when a root exists, no `plan-root` record is in the rendered JSONL.
- [ ] The planner's report lists each root field (description, design, acceptance criteria) that is missing relative to the phase plan.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0036: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Map fields by the Mapping table (translation, never rewrite); `difficulty` from frontmatter, missing or invalid is blocking; drop merge-forward triggers, PR-completion trigger, per-sprint `base`, frontmatter `assignee`, `status`.


### Rationale

importing-md-plan.md opens with 'The import is a translation, never a rewrite' and its Mapping table lists each bead var's markdown source and the dropped markdown-only mechanics.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each sprint var file's fields come from the sources named in the Mapping table, with no text rewritten.
- [ ] A sprint doc whose `difficulty` is missing or not `hard`, `normal` or `fast` stops the import with a blocking gap.
- [ ] The rendered beads contain no merge-forward trigger, PR-completion trigger, per-sprint `base`, `assignee` or `status`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0037: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Run every Checks row except id-exists before rendering; collect all gaps; any blocking: send the plan's author one line `<doc>: <field>: <problem>` per gap, blocking first; import nothing.


### Rationale

importing-md-plan.md Checks defines blocking and warn rows and says to collect all gaps before reporting any, and CHANGELOG records that it reports gaps to the plan's author only.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every Checks row except 'Any bead id already exists' is evaluated before any render.
- [ ] When any blocking row fails, one `atm send <author>` message lists each gap as `<doc>: <field>: <problem>`, blocking first, and `bd list` shows no new bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0038: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Render and validate as 26-28; any problem stops the import.


### Rationale

importing-md-plan.md steps 4 and 5 repeat the planning render and validate steps so an import cannot bypass the strict render or the validate-plan gate.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each bead is rendered with `sc-compose render --strict` and the `&&`-guarded `jq -e` append.
- [ ] `validate-plan --file ... --index ...` is run on the JSONL, and any problem line stops the import before `bd import`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0039: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Any id already exists: stop, use `bd update`.


### Rationale

importing-md-plan.md step 6 says `bd import` upserts, so an existing id would be overwritten, and re-importing is not a way to update a bead.

### Success Criteria

**Acceptance Criteria:**

- [ ] For every `id` in the rendered JSONL, `bd show <id>` is run, and any id that exists stops the import with an `EXISTS <id>` line.
- [ ] Changes to an existing bead are made with `bd update`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0040: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Import, then append `imported from <doc path>@<short sha>` to each sprint bead's notes, then `bead-groups --phase <x>`.


### Rationale

importing-md-plan.md step 8 records the source of each imported sprint and then pours the groups.

### Success Criteria

**Acceptance Criteria:**

- [ ] After import, each imported sprint bead's notes end with `imported from <doc path>@<git short sha>`.
- [ ] `bead-groups --phase <x>` runs after the notes are appended and creates the three group beads under each container.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0041: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Plan-review bead as 30; into a running phase: `<root>-plan-qa-<n>` (next free), blocking every new sprint container.


### Rationale

importing-md-plan.md step 9 notes `<root>-plan-qa` is already closed in a running phase and so uses the next free `-<n>` number, which blocks only the new containers.

### Success Criteria

**Acceptance Criteria:**

- [ ] For a whole-phase import, `<root>-plan-qa` exists and every imported root sprint depends on it.
- [ ] For an import into a running phase, `<root>-plan-qa-<n>` uses the next unused number and each new sprint container, and no existing container, depends on it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0042: Import a markdown plan

**Status:** Draft  
### Requirement Statement

As 31-33; then `bd ready -l phase-<x> -n 0` lists the plan-review bead and no imported dev bead, and `bd ready --explain` shows the rest blocked by plan review or prerequisite sanity beads.


### Rationale

importing-md-plan.md step 10 verifies with `bd ready -l phase-<x> -n 0` and `bd ready --explain`, which proves the plan gate blocks all dev beads before review.

### Success Criteria

**Acceptance Criteria:**

- [ ] The planner ran the same file, DAG, PR and `validate-plan --phase <x>` steps as in the planning flow (REQ-PLAN-0031 to 0033).
- [ ] `bd ready -l phase-<x> -n 0` lists the plan-review bead and no imported dev bead.
- [ ] `bd ready --explain` shows each other imported dev bead blocked by plan review or by a prerequisite's sanity bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_importing_docs.py::ImportingDocsTests::test_phase_index_instruction_is_an_import_procedure_step`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0043: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Run `bd sync`.


### Rationale

importing-md-plan.md step 11 makes the Dolt remote carry the plan; the atm-bd-orchestration 'Sync' section is cited there.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd sync` is run after the import verification and exits 0.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0044: Import a markdown plan

**Status:** Draft  
### Requirement Statement

Never edit, move or delete the markdown; never run the phase from both.


### Rationale

importing-md-plan.md intro says once imported the beads are the plan, the markdown files stay as history, and 'never run the phase from both'.

### Success Criteria

**Acceptance Criteria:**

- [ ] `git status` and `git log` show no edit, move or deletion of the source markdown plan or sprint docs by the import.
- [ ] No dev task is assigned from the markdown sprint doc once its sprint bead exists.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0045: Plan review FAIL

**Status:** Draft  
### Requirement Statement

Fix the beads with `bd update`; next round with the same task id; at most three rounds.


### Rationale

atm-bd-orchestration SKILL.md 'Plan Gate' step 3 caps plan review at three rounds and has the author fix with `bd update` while the lead assigns the next round on the same task id; CHANGELOG records round 2+ running only the filing reviewers.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a FAIL, the beads change through `bd update` and the next round is assigned on the same task id with `round` incremented by one.
- [ ] No fourth plan review round is dispatched.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0046: Replanning

**Status:** Draft  
### Requirement Statement

The plan file is the minimum set of sprint edges. Fix a DAG problem only by replanning: edit the plan file in a `/sc-git-worktree` branch off the `integration_branch`, merge the plan PR into it; beads and the plan file change in one commit.


### Rationale

atm-bd-orchestration SKILL.md 'Loop' and planning.md 'Phase definition' say a plan change is one planner transaction (beads, file, commit) and a DAG problem is fixed by replanning; CHANGELOG records the plan file as the minimum set of sprint edges.

### Success Criteria

**Acceptance Criteria:**

- [ ] A replan changes the plan file only in a `/sc-git-worktree` branch cut from the root's `integration_branch` and merges through the plan PR.
- [ ] The commit that changes the plan file also contains the matching bead changes' effect (`validate-plan --phase <x>` exits 0 after the merge).

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0047: Replanning

**Status:** Draft  
### Requirement Statement

While the phase runs the sprint set is frozen; only the lead adds edges: to phase-created fix beads, and any dependency discovered in motion (sprint beads included), never a replan.


### Rationale

atm-bd-orchestration SKILL.md 'Loop' says the sprint set is frozen while the phase runs and a discovered dependency is added by the lead with `bd dep add`, never as a replan; CHANGELOG (0.6.15) records this ruling.

### Success Criteria

**Acceptance Criteria:**

- [ ] During a running phase the plan file's sprint list is unchanged.
- [ ] A discovered dependency appears as a `bd dep add <bead> --blocked-by <blocker>` edge made by the lead, and no planned edge is removed.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0048: Replanning

**Status:** Draft  
### Requirement Statement

Keep `validate-plan --root <root>` green from plan approval to phase end.


### Rationale

atm-bd-orchestration SKILL.md 'Loop' requires `validate-plan --phase <x>` after every bead write, and planning.md says it must stay green from plan approval to phase end; the dev and fix templates run it before a claim.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --phase <x>` exits 0 after each bead write between plan approval and phase end.
- [ ] On a non-zero exit the lead stops dispatching and reports the problems to the user.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_reads_the_plan_from_the_integration_branch`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0049: Never

**Status:** Draft  
### Requirement Statement

Never create a gate bead or its edges without the user's explicit instruction for that gate.


### Rationale

atm-bd-orchestration SKILL.md 'Gate Beads' says a gate and its edges are created only on the user's explicit instruction for that gate, because a gate holds work and an unrequested one stalls the phase.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every `bd gate` bead in the phase and every edge to it is recorded with the user's explicit agreement for that gate on the gate bead or phase root; a phase with no such instruction has no gate bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0050: Never

**Status:** Draft  
### Requirement Statement

Never repair the graph with `bd dep` or `--parent`, beyond adding a dependency discovered in motion.


### Rationale

atm-bd-orchestration SKILL.md 'Loop' says to stop dispatching and report a graph problem, never repairing it with `bd dep` or `--parent` beyond a discovered dependency, so validate-plan problems are not silently masked.

### Success Criteria

**Acceptance Criteria:**

- [ ] The planner's and lead's shell history contains no `bd dep` or `bd update --parent` that changes a planned edge or planned parent after import, other than `bd dep add` for a discovered dependency.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0051: Never

**Status:** Draft  
### Requirement Statement

Never re-import to update a bead.


### Rationale

importing-md-plan.md step 6 states 're-importing is not a way to update a bead' because `bd import` upserts and overwrites an existing id.

### Success Criteria

**Acceptance Criteria:**

- [ ] No second `bd import` is run on a JSONL containing an id that already exists; bead changes after import are `bd update` calls.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0052: Never

**Status:** Draft  
### Requirement Statement

Never put findings, fixes, QA, tasks, branches or gates in the plan file.


### Rationale

planning.md 'Phase definition' says the plan file holds sprint ids and `depends_on` only and 'No finding, fix, QA, task, branch, or runtime gate appears in this file'; validate-plan rejects a line off that schema.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every line of the plan file parses as `{"sprint": <name>, "depends_on"?: [...]}` and has no other key.
- [ ] `validate-plan` exits 5 with `:<n>: each line is` for a line with an extra key such as `after`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_plan_file_schema`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0053: Never

**Status:** Draft  
### Requirement Statement

Never mark an unimplemented sprint bead `closed`.


### Rationale

atm-beads-plan-guidelines.md 'Process Artifacts' says bead `status` describes the sprint, not the plan, so an unimplemented sprint bead is `open`, never `closed`.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every sprint container whose dev bead is not closed has `status` `open` in `bd show`.
- [ ] Sprint containers closed during planning exist only as 'folded into ...' sprints.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0054: Never

**Status:** Draft  
### Requirement Statement

Never edit the script, the plan or the graph to make validation pass.


### Rationale

validate-plan's header says 'Report problems to the lead; never edit this script, the plan or the graph to make it pass', and CLAUDE.md names gate self-weakening as a pathology.

### Success Criteria

**Acceptance Criteria:**

- [ ] `git diff` of `scripts/validate-plan` and `bead_schema.py` is empty for the planning commits.
- [ ] A validate-plan problem is resolved by correcting the offending bead or plan line the problem names, or is reported to the lead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0055: Never

**Status:** Draft  
### Requirement Statement

Root children: only the sprint containers, `stage:plan*` beads, gate beads, folded sprints and important or minor finding beads.


### Rationale

planning.md 'Hierarchy' lists exactly what may be a child of the root, so that the sprint walk and validate-plan's extra-container check see a closed set.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd children <root>` lists only the sprint containers, `stage:plan*` beads, gate beads, folded sprints and important or minor finding beads.
- [ ] `validate-plan` exits 5 with `stage:sprint bead of phase-<x> that the plan file does not list` for a container not in the plan file.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_missing_and_extra_sprint_beads`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0056: Scripts

**Status:** Draft  
### Requirement Statement

`validate-plan` problems (exit 5), and nothing else: a plan file line off the schema or a `depends_on` naming an unknown sprint, a sprint container failing SprintBead or a poured sanity bead failing SanityBead; a plan sprint without its container; a `stage:sprint` container the plan does not list; the phase file's `integration_branch` differing from the root's; a `depends_on` with no `blocks` edge from the dependent's dev bead (or container) to the predecessor's sanity bead or container. Everything else is a stderr warning (`bd doctor` errors, open non-epic top-level beads since the root, a plan-time assignee in `--file`, a sanity `dev_bead` that is not its group's dev bead, a group not poured yet).


### Rationale

validate-plan's header lists problems (exit 5) and 'nothing else', so everything outside that list is a stderr warning that cannot block a valid plan.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each listed condition makes `validate-plan` exit 5 with one problem line: an off-schema plan line, an unknown `depends_on` sprint, a missing container, an extra container, an `integration_branch` mismatch, and a missing `blocks` edge.
- [ ] A top-level non-epic bead, a plan-time assignee, a sanity `dev_bead` that is not its group's dev bead and an unpoured group each print a `warning:` line on stderr and leave the exit status 0.
- [ ] A `bd doctor` error is printed as a warning and does not change the exit status.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_each_problem`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_plan_file_schema`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_missing_and_extra_sprint_beads`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_everything_else_warns`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_doctor_problems_are_warnings`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0057: Scripts

**Status:** Draft  
### Requirement Statement

`validate-plan` reads the plan file from `origin/<integration_branch>` as the phase file names it (or `--index`); exit 0 valid, 5 problems, 2 cannot run (no phase file, fetch failure, plan file missing); `--phase` or `--root` required.


### Rationale

validate-plan's header says the plan file is read from `origin/<integration_branch>` and defines exit 0, 5 and 2, so a reader can tell invalid from unable to run.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --phase <x>` reads `<plan>` from `origin/<integration_branch>` and exits 0 when valid.
- [ ] It exits 2 with `origin/<branch>:<plan> is missing` when the plan is absent from that branch, and exits 2 when `.atm-bd/phase-<x>.toml` is absent.
- [ ] It exits 2 when invoked with `--ci` and `--phase` together, and does not run `bd`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_reads_the_plan_from_the_integration_branch`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_plan_missing_on_the_branch_cannot_run`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_cannot_run`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::CiCheck::test_ci_takes_no_other_option`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## REQ-PLAN-0058: Scripts

**Status:** Draft  
### Requirement Statement

Not scripted, checked by plan review: ids exist and govern the work, disjoint `owned_paths`, `relation`/`layer`/`pr_target` agree.


### Rationale

planning.md 'Checks' and validate-plan's header say governing ids, disjoint `owned_paths` and relation/layer/pr_target agreement are checked by plan review, not by the script.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plan-review` verifies that each listed requirement and ADR id exists and governs the work, that concurrent sprints' `owned_paths` are disjoint, and that each sprint's `relation`, `layer` and `pr_target` agree, and records each failure as a finding.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

## Unresolved

None.
