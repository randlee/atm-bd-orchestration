# team-lead

**ID Range:** REQ-TL-0001 through REQ-TL-0059  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-26  
**Owner:** Rand Lee  

---

## REQ-TL-0001: Sequencer / Startup

**Status:** Draft  
### Requirement Statement

Verify `bd`, `atm`, `sc-compose`, `jq`, `gh` + `gh stack` at the skill's minimum versions; missing or old: stop, tell the user the install line; never work around it.


### Rationale

SKILL.md runs this check as Step 1, before anything else, and the atm-beads installation reference lists a stale `bd` first on PATH as the cause of `bd version` below 1.3.0. Declared minimums (`bd >= 1.3.0` in the skill `requires` and `manifest.yaml`) only protect a phase if the lead stops instead of improvising.

### Success Criteria

**Acceptance Criteria:**

- [ ] SKILL.md Step 1 runs `command -v` for `bd`, `atm`, `sc-compose`, `jq` and `gh`, `bd version` and `gh stack --version`.
- [ ] With one of those tools missing or `bd` below 1.3.0, the lead's next output is the install line from `references/installation-and-troubleshooting.md`, and no `bd`, `atm` or `gh` write command follows in the session.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0002: Sequencer / Startup

**Status:** Draft  
### Requirement Statement

Check `ATM_IDENTITY` = `BEADS_ACTOR` (bare identity); mismatch or wrong value: no bead writes until fixed; pass `--actor "$ATM_IDENTITY"` on every `bd` write.


### Rationale

The SKILL.md "ATM Limits Today" table records that ATM does not carry the bd actor, so every `bd` write must pass `--actor "$ATM_IDENTITY"` explicitly. A mismatched `BEADS_ACTOR` would attribute bead writes to the wrong identity.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `ATM_IDENTITY` unset, or different from `BEADS_ACTOR`, or not a bare identity, the lead performs no `bd` write until the values agree.
- [ ] Every `bd create`, `bd update`, `bd close` and `bd import` the lead runs in a phase carries `--actor "$ATM_IDENTITY"`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::DevAssignmentTests::test_a1_fires_on_not_ready_and_every_bd_write_has_an_actor`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0003: Sequencer / Startup

**Status:** Draft  
### Requirement Statement

Fill every repository value from `.claude/project/atm-bd-orchestration.yaml`; never default one.


### Rationale

SKILL.md "Repository configuration" states that repository values live in `.claude/project/atm-bd-orchestration.yaml` and that a missing file or key is a named error, never a default; the 0.19 templates declare these values as required variables with no defaults so a missing one fails the render.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each repository value the lead puts in a vars file equals the value of the same key in `.claude/project/atm-bd-orchestration.yaml`.
- [ ] When a key is absent from that file, the lead stops with the missing key named and does not substitute a value.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_repo_config.py::LoadTests::test_missing_key_is_a_named_error`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_repo_config.py::LoadTests::test_missing_file_is_a_named_error`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::ConfigVariableTests::test_each_config_variable_is_required`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::ConfigVariableTests::test_no_repository_default_is_built_in`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0004: Sequencer / Startup

**Status:** Draft  
### Requirement Statement

Resolve each role member with `resolve-role <role>` (exit 2: role unmapped) and put each long-running agent under its role prompt (`roles/quality-mgr.md`, `.claude/agents/dev-sanity.md`).


### Rationale

SKILL.md "Roles" maps every role other than the lead to a team member through `roles:` in `.claude/agents/registry.yaml`, resolved by `resolve-role`, and a long-running agent has to be told which prompt to operate under or it runs without its role contract.

### Success Criteria

**Acceptance Criteria:**

- [ ] `.claude/skills/atm-beads/scripts/resolve-role <role>` is run for each role member and exit status 2 is reported as an unmapped role.
- [ ] Each long-running agent (quality-mgr, dev-sanity) has received the `atm send` message "Operate under <prompt> ..." naming `roles/quality-mgr.md` or `.claude/agents/dev-sanity.md`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0005: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

`bd doctor` error: report it; never import into or dispatch from that database.


### Rationale

SKILL.md Loop makes `bd ready` the only answer to what is ready, so dispatching from a database that `bd doctor` reports as broken would hand out work from a graph the lead cannot trust; `validate-plan` likewise treats doctor problems as a warning only for the proxy case (CHANGELOG 0.19.15, #811).

### Success Criteria

**Acceptance Criteria:**

- [ ] When `bd doctor` prints an error, the lead's report to the user contains that error text.
- [ ] After such an error, the lead runs no `bd import` into that database and no `atm task assign` for a bead from it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0006: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

Import gaps go to the plan's author; when that is you, supply the branch or status rulings asked for; nothing imports on a blocking gap.


### Rationale

The plan is written by a planner and the lead is only its importer (SKILL.md Plan Gate; atm-beads `importing-md-plan.md`); a plan with an unresolved gap would put an invalid graph into beads, so gaps are returned to the author.

### Success Criteria

**Acceptance Criteria:**

- [ ] A gap reported by the import procedure is sent to the plan's author; when the lead is that author, the lead states the requested branch or status ruling.
- [ ] While a blocking gap is open, `bd list -l phase-<x>` shows none of the plan's sprint beads.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0007: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

Right after import and the pour, create `<root>-plan-qa` with no assignee; every sprint container blocks on it (running phase: `<root>-plan-qa-<n>`, blocking only the new containers).


### Rationale

SKILL.md Plan Gate step 1 creates the plan-review bead "right after the import and the pour" and blocks every sprint container on it so that `bd ready` cannot list a dev bead before the plan passes; a running phase uses `<root>-plan-qa-<n>` to block only the new containers.

### Success Criteria

**Acceptance Criteria:**

- [ ] After import and pour, `bd show <root>-plan-qa` exists with label `stage:plan-review`, parent `<root>` and no assignee.
- [ ] Every sprint container has `<root>-plan-qa` among its blockers (for a running phase, `<root>-plan-qa-<n>` blocks only the newly imported containers).

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::FilePlan::test_a_plan_bead_with_an_assignee_or_no_parent_is_a_warning`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0008: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

The plan file and the phase file are committed by hand on origin `integration_branch`, never exported from beads; the phase DAG HTML (`sprint-review`) is committed with them by the planner (the script never commits or pushes), opened only with `--view`.


### Rationale

SKILL.md Plan Gate step 2 and the 0.19.8 CHANGELOG entry make the planner commit the DAG with the plan and phase file and state that `sprint-review` never commits or pushes; `validate-plan` reads the plan from the `integration_branch`, so a plan that exists only in beads or a working tree cannot be validated.

### Success Criteria

**Acceptance Criteria:**

- [ ] `<plans_dir>/phase-<x>.jsonl`, `.atm-bd/phase-<x>.toml` and `<plans_dir>/phase-<x>/phase-<x>-dag.html` are committed together on origin `integration_branch` by the planner.
- [ ] `git log` for those paths shows hand-made commits, and the `sprint-review` run leaves the working tree uncommitted unless `--view` was requested, in which case only the viewer opens.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_reads_the_plan_from_the_integration_branch`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0009: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

`validate-plan --phase <x>` exits 0 or stop; then `bd ready` lists the plan-review bead and no dev bead.


### Rationale

SKILL.md Plan Gate step 2 says to run `validate-plan --phase <x>` from the repository root and "Exit 0 or stop"; the gate is only meaningful if no dev bead is ready until the graph validates.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --phase <x>` exits 0 before plan review is dispatched; any other exit stops the lead.
- [ ] After exit 0, `bd ready -l phase-<x> -n 0 --json` lists the plan-review bead and lists no `stage:dev` bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_cannot_run`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0010: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

Dispatch plan review to quality-mgr; no dev bead before it passes.


### Rationale

SKILL.md Plan Gate opens with "No dev bead is dispatched until the plan passes review" and routes plan review to quality-mgr through `templates.plan_review`; requirements and ADRs are checked at this gate so dev beads carry governing ids before coding starts.

### Success Criteria

**Acceptance Criteria:**

- [ ] The plan-review bead's task is assigned to quality-mgr with the phase file's `templates.plan_review`.
- [ ] No `atm task assign` for a `stage:dev` bead is issued while `<root>-plan-qa` is open.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0011: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

PASS closed: nothing. PASS handed back open with minor findings: fix each with `bd update`, then close `<root>-plan-qa`.


### Rationale

SKILL.md Plan Gate step 3 and the Loop close table: a PASS closed by quality-mgr releases the root sprints, while a PASS handed back open with minor findings leaves the plan-review bead as the only gate on the sprints until the lead fixes the listed beads.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a plan-review PASS that closed the bead, the lead makes no `bd update` or `bd close` on `<root>-plan-qa`.
- [ ] After a PASS handed back open with minor findings, each listed finding has a `bd update` on its bead and then `bd show <root>-plan-qa` is closed with reason "minor fixes applied".

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0012: Sequencer / Plan gate

**Status:** Draft  
### Requirement Statement

FAIL: the author fixes the listed beads; rerun `validate-plan`; dispatch round+1, same task id, `carry_forward` = open finding lines; three rounds max.


### Rationale

SKILL.md Plan Gate caps plan review at three rounds and runs a fix round on only each carried finding's filing reviewer; the CHANGELOG ("Plan-review fix rounds are filing-reviewer-only too (ruling 2026-10-03)") records that ruling.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a FAIL, the author's `bd update` fixes are followed by a `validate-plan --phase <x>` run before the next dispatch.
- [ ] The next dispatch reuses the same task id with `round` incremented by 1 and `carry_forward` holding the open finding lines.
- [ ] No plan-review dispatch with `round` greater than 3 is issued.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::PlanFixRoundTests::test_fix_round_dispatches_only_filing_reviewers`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0013: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Before the first dispatch, create the root's `integration_branch` from the base branch and push it.


### Rationale

SKILL.md Dispatch requires the root's `integration_branch` to exist before the first dispatch because every dev and finding branch is cut from the top of a stack that bottoms out on it, and `validate-plan` reads the plan from that branch.

### Success Criteria

**Acceptance Criteria:**

- [ ] `git ls-remote origin <integration_branch>` returns a ref before the first `atm task assign` of the phase.
- [ ] That ref's history starts at the base branch's head at the time of creation.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0014: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Run `bd ready -n 0` after every close, before any other work, and dispatch every ready bead; assign a bead only while `bd ready` lists it; order and hold work only with bead edges, gates and `atm task move`, never by telling an agent not to run a task in its queue; never cache it; never dispatch the phase root. The lead may step in at critical points, preferably through a background developer subagent; lead work is never part of the original plan.


### Rationale

SKILL.md Loop: `bd ready` is the only answer to what is ready; the lead never decides, caches or orders work by telling agents what to skip. The 0.6.x CHANGELOG entries add that lead work is never part of the original plan and records the stalled-assignee and blocker handling that rely on bead edges rather than instructions.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd ready -l phase-<x> -n 0 --json` is run after every task close, before any other action, and every bead it lists is dispatched.
- [ ] No `atm task assign` is issued for a bead absent from the most recent `bd ready` output, and the phase root is never assigned.
- [ ] Holding or ordering work is done only by `bd dep add`, a gate or `atm task move`, and no message tells an agent to skip a queued task.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0015: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Route: plan review and QA to quality-mgr; dev to the member you pick for its `difficulty` (a minimum: a dev at that tier, or one tier up when none is idle, e.g. fast to terra/sonnet; never far above it, e.g. fast to a frontier model); sanity to `resolve-role dev-sanity`; finding to the member you pick; a sanity finding is never dispatched alone: its checked bead goes to that bead's assignee with `dev-fix.xml.j2`; a quick-fix finding with `fix-assignment.xml.j2`, no sanity bead, to an idle dev you pick for its `difficulty`, never as an ordinary finding; review to the phase-end reviewer.


### Rationale

SKILL.md Loop table fixes the template and recipient for each ready bead; the 0.19.x CHANGELOG records that `sprint-report --dispatch` lists only idle `dev` members at the bead's tier or one up, and a quick-fix finding has its own row so it is never dispatched as an ordinary finding.

### Success Criteria

**Acceptance Criteria:**

- [ ] Plan review and QA beads are assigned to quality-mgr, sanity beads to the output of `resolve-role dev-sanity`, and review beads to the phase-end reviewer.
- [ ] A dev or fix bead goes to an idle `dev` member at its `difficulty` tier or one tier up, never to a frontier model for `fast` work.
- [ ] A sanity finding is dispatched to the checked bead's assignee with `dev-fix.xml.j2`, and a quick-fix finding with `fix-assignment.xml.j2` with no sanity bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/sprint-report/tests/test_sprint_report.py::SprintReportTests::test_dispatch_recommends_dev_members_at_the_tier_then_one_up`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0016: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Important or minor finding: when you assign it, create its sanity bead and its QA bead (QA blocked by sanity, both under the finding's parent) in one `bd import`; a minor finding left in the backlog gets neither until it is assigned.


### Rationale

SKILL.md Loop table and the 0.6.x CHANGELOG entry say the lead creates an important or minor finding's sanity and QA beads when it assigns the finding, in one `bd import`, so the finding <- sanity <- QA chain exists before the finding is worked and a backlog minor finding carries no unused beads.

### Success Criteria

**Acceptance Criteria:**

- [ ] On assigning an important or minor finding, one `bd import` creates its sanity bead and its QA bead, both with `parent` = the finding's parent, and the QA bead is blocked by the sanity bead.
- [ ] A minor finding left in the backlog has no sanity bead and no QA bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0017: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Dev or finding bead: cut its branch and worktree from the current top of its stack (its `pr_target` or a descendant), passed as the assignment's `pr_target`.


### Rationale

SKILL.md Stack Discipline: every PR lands on the top of its stack and a dev or fix branch is cut from that top; cutting from a lower layer forks the stack, which sanity refuses.

### Success Criteria

**Acceptance Criteria:**

- [ ] The dev or finding branch's merge base with `origin/<top>` equals `origin/<top>`'s head, where `<top>` is the `pr_target` or a descendant of it.
- [ ] The assignment vars file sets `pr_target` to that branch.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::DevAssignmentTests::test_every_dev_lands_its_pr_on_the_current_stack_top`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0018: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Set the bead's assignee to the recipient before `atm task assign <agent> --task-id <bead>` with the template; vars from the bead, kept outside the repo; preview with `atm compose`, never render and paste a body.


### Rationale

SKILL.md Dispatch states that a claim fails when the bead is assigned to anyone else, so the lead sets the assignee before `atm task assign`; it also forbids pasting a rendered body so the template, not the lead, stays the contract, and keeps vars files outside the repository.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd show <bead> --json` shows the recipient as assignee before the `atm task assign <agent> --task-id <bead> --template ... --vars ...` command runs.
- [ ] `atm compose --template <t> --vars <file>` was run for the preview, and the assign command passes `--template`, not a rendered body.
- [ ] The vars file path is outside the repository worktree.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0019: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Assignee by priority: frontier dev for blocking and dev, fast agent for important and minor (usual case, not a rule).


### Rationale

SKILL.md Priority: the finding template derives priority from severity and "the usual case is a frontier dev for blocking and dev work and a fast agent for important and minor"; the text calls it a usual case, which is why it is not a checkable rule.

### Success Criteria

**Acceptance Criteria:**

- [ ] Blocking-finding and planned dev beads are assigned to a frontier-tier dev when one is idle.
- [ ] Important and minor finding beads are assigned to a fast-tier dev when one is idle.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0020: Sequencer / Dispatch

**Status:** Draft  
### Requirement Statement

Dispatch the next sprint once its sanity blockers PASS; never wait on QA.


### Rationale

SKILL.md Stack Discipline and the Loop state that sprint work does not wait for QA; dev waits only on its prerequisites' sanity checks, with QA and fixes interleaved by priority. Waiting on QA would serialize every sprint behind its review.

### Success Criteria

**Acceptance Criteria:**

- [ ] The next sprint's dev bead is assigned when its prerequisites' sanity beads are closed PASS, while their QA beads are still open.
- [ ] `bd show` for the next sprint's dev bead shows no blocker on a QA bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0021: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

dev-complete: verify the dev's PR, record the layer PR in the checked bead's notes, and assign sanity without linking; the sanity close hook closes first, then the sanity side links under the stack bead lock. Never message or re-dispatch the dev for stacking. After a dev-fix, `layer_prs` is the sprint's own layer PRs with the checked PR last.


### Rationale

SKILL.md dev-complete row and the 0.19.x CHANGELOG ("Sanity closes on its selected verdict before handing off stacking") move linking after the sanity PASS close hook, so a failed link never blocks sanity and the dev is never re-dispatched for stacking.

### Success Criteria

**Acceptance Criteria:**

- [ ] After dev-complete the lead has run `bd update <bead> --append-notes "layer PR #<n> <url>"` and assigned the sanity bead, and has run no `gh stack link`.
- [ ] No message or task re-dispatch to the dev concerns stacking.
- [ ] For a reopened dev bead, `layer_prs` lists the sprint's own layer PRs with the checked PR last.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_three_passes_link_in_verdict_order`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_agent_prompts.py::test_sanity_prompts_close_before_ordered_stack_handoff`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::DevAssignmentTests::test_after_sanity_fail_reopens_dev_bead_sanity_and_qa_diff_only_own_layer_prs`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0022: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

Sanity PASS: after the close hook succeeds, verify the PR base is `pr_target` or a descendant of it; dispatch the group's QA bead with `base` = the PR base (after a dev-fix, also `layer_prs`; for a fix bead, `carry_forward` = the fix bead and `round` + 1; for an important or minor finding, `carry_forward` = the finding).


### Rationale

SKILL.md sanity-PASS row: QA diffs must cover only the sprint's own layers, so `base`, `layer_prs`, `carry_forward` and `round` are set from the checked and fix beads instead of defaults; a fix bead's QA carries the fix bead for its own requirements and ADRs.

### Success Criteria

**Acceptance Criteria:**

- [ ] After the close hook succeeds, `gh pr view <pr> --json baseRefName` shows a base equal to `pr_target` or a descendant of it.
- [ ] The QA assignment sets `base` to the PR base, and for a fix bead sets `carry_forward` to the fix bead and `round` to its `metadata.round` + 1.
- [ ] For an important or minor finding, `carry_forward` equals the finding id.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::DevAssignmentTests::test_after_sanity_fail_reopens_dev_bead_sanity_and_qa_diff_only_own_layer_prs`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0023: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

Sanity FAIL (first): verify children against the branch; close with reason any that judge correctness or quality; overrule, amend, split or reassign, never recreate; dev-sanity has reopened the checked bead; assign `dev-fix.xml.j2` on a new layer cut from the current top of the stack, with the sprint's first layer's branch recorded as the checked bead's `pr_target` (a later dev-fix keeps it); never rebase or re-target a linked layer.


### Rationale

SKILL.md sanity-FAIL row and the CHANGELOG entry "dev sanity ... no child finding is created": a sanity FAIL is a deliverable-readiness result that reopens the checked bead for the dev, so findings are neither recreated nor split off, and a linked layer is never rebased or re-targeted.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a first sanity FAIL, children that judge correctness or quality are closed with a reason and the checked bead is reopened; no replacement bead is created.
- [ ] The `dev-fix.xml.j2` assignment is cut from the current top of the stack, with the sprint's first layer's branch as the checked bead's `pr_target`.
- [ ] A later dev-fix leaves `pr_target` unchanged, and no `gh stack rebase` is run on a linked layer.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::TemplateContractTests::test_sanity_fail_report_explains_handoff_without_finding_beads`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0024: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

Sanity FAIL (second, `SANITY.ROUND_CAP`): diff flagged files vs last PASS, check the base for foreign commits, then rule; no third round without it.


### Rationale

SKILL.md sanity-FAIL row and the git history entry "fix(atm-bd-orchestration): escalate round cap to team-lead once": at the sanity round cap the loop stops itself and a person rules, because another round has already failed to converge.

### Success Criteria

**Acceptance Criteria:**

- [ ] On `SANITY.ROUND_CAP` the lead's output includes the diff of flagged files against the last PASS and the check of the base for foreign commits.
- [ ] No third sanity assignment for the bead is issued before the lead records a ruling.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0025: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

`SANITY.PLAN_INVALID`: planning failed for that bead.


### Rationale

`sanity-split` exits 2 with `SANITY.PLAN_INVALID` when the checked bead has no numbered `## Deliverables` list ("planning failed"), so the defect is in the bead the planner wrote and not in the dev's work.

### Success Criteria

**Acceptance Criteria:**

- [ ] On `SANITY.PLAN_INVALID` the lead's report states that planning failed for that bead.
- [ ] The lead does not treat it as a dev defect: no `dev-fix.xml.j2` assignment is issued for it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0026: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

qa-complete: nothing to pour (quality-mgr poured the fix groups), except a failed quick-fix QA, which pours none: file each blocking finding in its `findings_md` as a finding bead and dispatch it (45); reopen a ceremony closure you disagree with; pick the member for each finding; close the sprint container once nothing under it is open.


### Rationale

SKILL.md qa-complete row: quality-mgr pours the fix groups before closing the QA bead, so the lead has nothing to pour; the exception is a failed quick-fix QA, which pours none (the 0.6.x CHANGELOG entries on quick-fix QA).

### Success Criteria

**Acceptance Criteria:**

- [ ] After qa-complete the lead pours no fix group, except for a failed quick-fix QA, where it files each blocking finding in `findings_md` with `finding-bead.json.j2` and dispatches it.
- [ ] A ceremony closure the lead disagrees with is reopened with `bd update --status open`.
- [ ] The sprint container is closed with `bd close` only when `bd children <sprint> --json` shows every child closed.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0027: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

QA `ROUND_CAP` (FAIL at round 2): no further fix round.


### Rationale

SKILL.md and `transitions.py` define a QA FAIL at round 2 as `ROUND_CAP`; fix rounds are limited so a sprint cannot loop on review indefinitely.

### Success Criteria

**Acceptance Criteria:**

- [ ] For a QA bead closed FAIL with `metadata.round` 2, the lead pours no further fix round.
- [ ] `next_transition` returns `ROUND_CAP` for that state.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_transitions.py::TransitionTests::test_json_transition_fixtures`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0028: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

fix-complete `fixed`: verify the dev's PR, record the layer PR in the fix bead's notes, and let the sanity PASS handoff link it after the close hook; fix a stack problem yourself only if the handoff reports one. A poured fix bead or an important or minor finding needs nothing more: the group's sanity bead is now ready. `not_reproducible`: close the group's sanity bead, then its QA bead, with reason `not_reproducible: <fix bead>`. A quick-fix finding, either outcome: once every finding from that QA has closed, one more quick-fix QA bead.


### Rationale

SKILL.md fix-complete rows: stack linking follows the sanity PASS close hook, and a `not_reproducible` result must close the group's sanity then QA beads so the group does not wait forever; the 0.6.18 CHANGELOG entry adds one more quick-fix QA bead per failed QA, not per finding.

### Success Criteria

**Acceptance Criteria:**

- [ ] For outcome `fixed`, the layer PR is recorded with `bd update <bead> --append-notes`, and the lead links nothing itself unless the handoff reported a stack problem.
- [ ] For `not_reproducible`, the group's sanity bead and then its QA bead are each closed with reason `not_reproducible: <fix bead>`.
- [ ] For a quick-fix finding, one quick-fix QA bead is created once every finding from that QA is closed.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::DevAssignmentTests::test_not_reproducible_needs_no_commit_but_fixed_does`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0029: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

review-complete: file each finding as a finding bead (`qa_bead` = review bead; provenance from the cited dev bead, the root with the union of real ids when it spans sprints; `found_at_commit` = reviewed commit).


### Rationale

SKILL.md Phase-End Review defines how the lead files review findings: provenance (`sprint_bead`, `requirements`, `adrs`, `found_on_layer`) comes from the cited dev bead so later fix rounds and `bead-groups` can route and verify them; `found_on_layer` must be an integer or `bead-groups` refuses it.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each review finding is a bead created with `finding-bead.json.j2` and `qa_bead` = the review bead.
- [ ] `sprint_bead`, `requirements` and `adrs` equal the cited dev bead's values; for a cross-sprint finding `sprint_bead` is the root and the lists are the union of the sprints' real ids with `NONE` dropped.
- [ ] `found_at_commit` equals the reviewed commit.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0030: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

task-refused: read reason and bead state; reassign only once `bd ready` lists the bead (a blocker refusal: as 31), split or force-close with a reason; a `blocked` bead is set open with its new assignee before re-dispatch. Sanity checks deliverable readiness and the pinned commit; stack linking runs after PASS close. `REVIEW_PENDING_JEV`: file the code findings in its notes, re-dispatch only after the Jev outage clears, reusing the prior run IDs.


### Rationale

SKILL.md task-refused row and the 0.6.x CHANGELOG: a refused task leaves the bead `open`, a `blocked` bead is never in `bd ready`, and `REVIEW_PENDING_JEV` means Jev was down during review, so re-dispatch waits for the outage and reuses the prior run ids.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a task-refused close the lead has read the close reason and `bd show <bead>` status before re-assigning.
- [ ] A `blocked` bead is set open with `bd update <bead> --status open --assignee <new agent>` before re-dispatch.
- [ ] For `REVIEW_PENDING_JEV`, each code finding is filed with `finding-bead.json.j2` and the review is re-dispatched only after the Jev outage bead is closed, with the prior `post_mortem_jev` run ids in its notes.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::BlockedRefusalTests::test_the_not_ready_step_refuses_and_leaves_the_bead_open`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0031: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

Not-ready or blocker refusal (task `refused`, bead open): fix the named cause (a blocker that is not a bead, such as an unfiled fix, first gets a finding bead), add the recommended dependency (or the right one) so `bd ready` holds the bead; when bd refuses it (one edge type per bead pair, no parent-child edge), add the edge to an open bead the blocker's work goes through instead, unless it already blocks the bead (a QA bead whose checked bead changes after its sanity PASS: the change is a new fix bead, and its sanity bead holds the QA bead; a passed sanity is never reopened), never removing an edge; re-assign the same task id, template and vars only once `bd ready` lists it; never answer it with "wait"; unwanted work: close the bead with a reason. An assignee silent past the re-nudge: announce it (Lead Role), set the bead open with a new assignee, re-assign the same task id with the same template and vars.


### Rationale

The 0.6.x CHANGELOG entries "A blocked task is refused, never held" and "Review of the blocked-task refusal" record that an assignee who waits on a blocker stalls the loop; bd allows one edge type per bead pair, so the lead's edge must go on another open bead.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a not-ready or blocker refusal, `bd ready` does not list the bead until the named dependency has been added with `bd dep add <bead> --blocked-by <blocker>` (or on an open bead the blocker's work goes through).
- [ ] No edge is removed, and the same task id, template and vars are re-assigned only after `bd ready` lists the bead.
- [ ] For a silent assignee, the lead announces it, sets the bead open with a new assignee and re-assigns the same task id with the same template and vars.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::BlockedRefusalTests::test_the_not_ready_step_refuses_and_leaves_the_bead_open`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::BlockedRefusalTests::test_a_mid_task_blocker_returns_the_bead_open_and_refuses`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0032: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

After every bead write, `validate-plan --phase <x>`; any problem: stop dispatching, report to the user; never repair the graph (`bd dep`, `--parent`) beyond adding a dependency discovered in motion.


### Rationale

SKILL.md Loop: `validate-plan` is the graph's only validator, so it runs after every bead write; the lead does not repair the graph (`bd dep`, `--parent`) itself because that would change the plan the validator checks.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --phase <x>` is run after each bead write the lead makes.
- [ ] On any reported problem the lead issues no further `atm task assign` and reports the problem to the user.
- [ ] The only graph edit the lead makes in motion is `bd dep add` for a dependency discovered in motion.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0033: Sequencer / On each close

**Status:** Draft  
### Requirement Statement

The plan file is the minimum set of sprint edges. A DAG problem is fixed only by a replan PR off the root's `integration_branch`, merged into it; in motion the sprint set is frozen and the lead only adds dependencies: to fix beads, and any dependency discovered in motion (sprint beads included), never a replan; a planned edge is never removed.


### Rationale

SKILL.md Loop and the 0.6.15 CHANGELOG entry: "A dependency discovered in motion ... is added by the lead with `bd dep add`, sprint beads included, never a replan; the sprint set stays frozen and no planned edge is removed."

### Success Criteria

**Acceptance Criteria:**

- [ ] A DAG problem is fixed by a plan PR off `integration_branch`, merged into it.
- [ ] During the phase the number of sprint beads is unchanged and every edge in the plan file is still present in `bd show` output.
- [ ] Edges the lead adds in motion are `bd dep add` on fix beads or on dependencies named by a blocker refusal.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_a_missing_live_edge_is_a_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0034: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Check a "blocking" finding's scope (requirement, code, ownership) before its priority; out-of-phase issues go to the owner's backlog with evidence.


### Rationale

`blocking-findings-guidelines.md` "Check scope before priority": a severity label or QA discovery does not add work to the plan, and its example (an sc-lint pin change exposed by a validation run) shows how an out-of-phase issue would otherwise expand a phase.

### Success Criteria

**Acceptance Criteria:**

- [ ] For each blocking finding the lead's ruling states whether the requirement, the code and the ownership belong to the approved sprint.
- [ ] A finding judged out of phase is recorded in the owner's backlog with its evidence and no bead in this phase depends on it.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0035: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Read the cited code at the reported commit and current head; separate defect from remedy; correct an overbroad remedy on the finding, keeping its evidence.


### Rationale

`blocking-findings-guidelines.md` "Check the finding against the contract": a valid defect can have an overbroad remedy, so the lead reads the code and the contract before the reviewer's fix is dispatched.

### Success Criteria

**Acceptance Criteria:**

- [ ] The lead's note on the finding cites the code at the reported commit and at the current head.
- [ ] When the remedy is corrected, the correction is recorded on the finding and the original evidence text is still present.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0036: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Reject process-artifact remedies lacking consumer, gate, defect and retirement condition; keep the real defect.


### Rationale

`blocking-findings-guidelines.md` "Reject unnecessary process remedies" requires a consumer, a gate, an observed defect and a retirement condition for any process artifact; the repository CLAUDE.md applies the same rule to its own ceremony.

### Success Criteria

**Acceptance Criteria:**

- [ ] A finding remedy that adds a certificate, ledger, matrix, report or check without all four is not dispatched as written.
- [ ] The real defect named in that finding is still dispatched with its remedy reduced to the code or test change.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0037: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Unresolved decision: create a `decision` bead (question, options, contract, affected beads, cost of being wrong, provisional choice) for the user or their delegate; it blocks phase closure, never development.


### Rationale

`blocking-findings-guidelines.md` "Record and scope the decision": waiting for an answer must not idle independent work, so an unresolved question becomes a `decision` bead that blocks only phase closure.

### Success Criteria

**Acceptance Criteria:**

- [ ] A `decision` bead exists for the question and lists the options, governing contract, affected beads, cost of choosing wrong and the provisional choice, with the user or their delegate as assignee.
- [ ] The decision bead is a child that blocks phase closure and has no `blocks` edge to any dev, fix, sanity or QA bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0038: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Take conservative reversible provisional choices; hold only work that depends on a significant decision.


### Rationale

`blocking-findings-guidelines.md` "Keep development moving conservatively" gives the example of using an existing crate rather than a new one while a decision is open, so the cost of a wrong guess stays low.

### Success Criteria

**Acceptance Criteria:**

- [ ] The provisional choice recorded on a decision bead is reversible and consistent with the existing architecture, with no new crate or forbidden dependency added to avoid waiting.
- [ ] Only beads whose work depends on the open decision are held; independent beads remain dispatchable in `bd ready`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0039: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Never close an unresolved finding or claim PASS to release a queue; silence or elapsed time is not approval.


### Rationale

`blocking-findings-guidelines.md` states "An unanswered question or elapsed time is not approval"; closing a finding or claiming PASS to release a queue would hide an unresolved defect.

### Success Criteria

**Acceptance Criteria:**

- [ ] No finding bead is closed without a recorded fix or an explicitly authorized non-fix reason.
- [ ] No QA or review verdict of PASS is written while a blocking finding is open, and no time-based rule closes a decision bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0040: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

Create a `bd gate` and its edges only on the user's explicit instruction; human gates need recorded user agreement.


### Rationale

SKILL.md "Gate Beads": `bd gate` holds work for CI, a timer or a person, and the section states a gate and its edges are created only on the user's explicit instruction, with human gates needing recorded user agreement.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every `bd gate` bead in the phase has a recorded user instruction naming that gate.
- [ ] A human gate bead or the phase root carries a note recording the user's agreement.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0041: Sequencer / Findings and decisions

**Status:** Draft  
### Requirement Statement

A serious infrastructure failure is announced once per cause to the ATM escalation recipients, else the task assigner saying none is set; a fallback is used so work moves, never silently: each use is logged with its verbatim error and announced the same way. For an infrastructure outage tracked by the Loop's re-test and re-dispatch hold, use one outage class bead; while it is open, re-test its cause each Loop pass and close it on success, releasing held re-dispatches. Refusals carry their reason in the ATM message and do not create or cite a class bead.


### Rationale

SKILL.md "Lead Role" and the 0.6.x CHANGELOG ("Serious failures are announced once per cause"): an agent cannot fix a missing API key or an exhausted quota itself, so the announcement path and the escalation-recipient lookup are fixed in one place; a silent fallback would hide the outage.

### Success Criteria

**Acceptance Criteria:**

- [ ] A serious infrastructure failure is sent once per cause with `atm send <recipient> --stdin` to each recipient from `atm escalation list --team "$ATM_TEAM" --json` (else the team-less list, else the task assigner with a statement that no recipient is set).
- [ ] Each fallback use appears in the log or evidence with its verbatim error and the same announcement.
- [ ] An infrastructure outage held by the Loop has one outage class bead; it is re-tested each Loop pass and closed on success. A refusal creates and cites no class bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::TemplateContractTests::test_refusal_assignments_do_not_require_workflow_class_beads_or_citations`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::TemplateContractTests::test_workflow_issue_template_exists`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0042: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

Own stack maintenance (`gh stack unstack/sync/rebase/merge`) and direct links for quick fixes without a sanity check. The sanity side alone links a layer after its PASS close hook, under the stack bead claim. Rebasing is done before sanity or QA is assigned and is the dev's, at dev-complete; the lead fixes only what the dev could not, or another stack problem, before dispatching sanity or QA, in its own worktree, and dispatches with the new `commit`, `base`, `branch`, `pr_number` and `worktree_path`. A layer that has passed QA, or has layers above it, is never rebased, and a rebase never re-dispatches QA or sanity on any other layer.


### Rationale

SKILL.md Stack Discipline names the lead as the only stack writer, and the 0.19.x CHANGELOG records that a layer rebased after its sanity PASS invalidated QA and sanity on other layers; the rule keeps a QA-passed or covered layer frozen.

### Success Criteria

**Acceptance Criteria:**

- [ ] `gh stack unstack`, `sync`, `rebase` and `merge` are run only by the lead (or its work-orchestrator), one writer at a time, and only in the lead's own worktree.
- [ ] A rebase happens before sanity or QA is assigned, and the dispatch carries the new `commit`, `base`, `branch`, `pr_number` and `worktree_path`.
- [ ] No layer that passed QA or has a layer above it is rebased, and a rebase triggers no sanity or QA re-dispatch on any other layer.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_rebase_required_names_rebase_options`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_orchestrating_docs.py::OrchestratingDocsTests::test_stack_bead_section_defines_layer_order_authority`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0043: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

Link layers in sanity-PASS completion order; record each bead's actual `layer` at link time; `pr_target` changes only at a dev-fix (23). The lead does not link layers: after a PASS close the sanity side links the layer (sanity-stack-link, dev-sanity 50); the first stack from layers 0 and 1 is created there, and the lead acts only on `stack_failed`, `lock_timeout` and `rebase_required`.


### Rationale

SKILL.md Stack Discipline and the stack bead's `layers` list make the stack ledger the only record of layer order; the 0.19.x CHANGELOG moved linking to the sanity side so the lead acts only on the three failure results.

### Success Criteria

**Acceptance Criteria:**

- [ ] The stack bead's `layers` list is in sanity-PASS completion order, each entry records its actual `layer`, and `pr_target` changes only at a dev-fix.
- [ ] The lead runs no `gh stack link`; after a PASS close the sanity-stack-link result is `stacked` or one of `stack_failed`, `lock_timeout`, `rebase_required`, and the lead acts only on the latter three.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_three_passes_link_in_verdict_order`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_rebase_required_names_rebase_options`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0044: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

Parallel quick fix: pick its `pr_target`, the lowest branch holding what the change needs; the finder (or a background developer subagent when every roster agent is busy) cuts `fix/<thing>` from the stack top as a new layer; link it, then one QA round on a quick-fix QA bead (no sanity check).


### Rationale

SKILL.md "Parallel Quick Fix" describes the failure it prevents: a shared signature or critical bug fixed in the finder's layer breaks every other branch until that layer merges and creates cross-fence edits at each restack.

### Success Criteria

**Acceptance Criteria:**

- [ ] The quick fix's `pr_target` is the lowest branch that already holds what the change needs, and `fix/<thing>` is cut from the stack's current top as a new layer.
- [ ] A quick-fix QA bead exists with `quick_fix` true and `pr_target` set; no sanity bead exists for it.
- [ ] When every roster agent is busy, a background developer subagent cuts the branch.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::ConfigVariableTests::test_qa_bead_marks_a_quick_fix_explicitly`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_a_quick_fix_qa_skips_only_the_sanity_pass_check`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_a_quick_fix_layer_on_the_stack_top_passes_its_lower_bound`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0045: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

A failed quick-fix QA: file each blocking finding as a finding bead and dispatch it with `fix-assignment.xml.j2` to an idle roster agent (the finder when idle; when all are busy and its `difficulty` suits the lead, to the lead itself, which runs the template's gate, claim, start and close steps and acts on the subagent's report while a background developer subagent does the fix steps; else it stays in `bd ready` for the first suitable agent to go idle), no sanity bead, on the same branch when nothing is linked above it, else a new layer cut from the stack top; once every finding from that QA has closed, one more quick-fix QA bead.


### Rationale

The 0.6.x CHANGELOG ("Review round 2", "A failed quick-fix QA's finding beads go to an idle roster agent") records that a failed quick-fix QA pours nothing, and that a mid-task finder must not have the fix queued behind its current task.

### Success Criteria

**Acceptance Criteria:**

- [ ] For each blocking finding in the failed quick-fix QA's `findings_md`, a finding bead exists with `qa_bead` = the quick-fix QA bead, assigned with `fix-assignment.xml.j2` and no sanity bead.
- [ ] The fix is on the same branch when no layer is linked above it and on a new layer cut from the stack top otherwise.
- [ ] One further quick-fix QA bead is created only after every finding from that QA has closed.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_a_quick_fix_qa_skips_only_the_sanity_pass_check`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0046: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

The quick fix lands with the stack; others rebase onto the top at dev-complete; tell each owner the base moved; record the fix branch and PR in the finder's and every touched bead's notes.


### Rationale

SKILL.md Parallel Quick Fix steps 4 and 5: once the fix is in the base it leaves every rebased branch's diff, so the lead must tell each owner the base moved and record the fix branch and PR on the beads whose fences it touched.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each other branch rebases onto the stack top at its dev-complete and each owner has received a message that the base moved.
- [ ] The finder's bead notes and the notes of every touched bead contain the fix branch and PR.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0047: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

Merge no PR into the integration branch or a stack layer without QA.


### Rationale

SKILL.md Parallel Quick Fix step 4 states "No PR merges without QA"; the 0.6.x CHANGELOG added a quick-fix QA bead exactly so a quick fix, which has no sanity, still gets a review before it lands.

### Success Criteria

**Acceptance Criteria:**

- [ ] For every PR merged into `integration_branch` or a stack layer, a QA bead for its head commit exists and is closed PASS.
- [ ] No `gh pr merge` or `gh stack merge` is run on a PR without such a QA bead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0048: Sequencer / Stack

**Status:** Draft  
### Requirement Statement

Verify branches read-only; never run a state-changing command in an assignee's worktree.


### Rationale

SKILL.md Loop: "Verify branches read-only (`git -C <worktree> log`, `git diff`, `gh pr view`); never run a state-changing command in an assignee's worktree" — a lead write there would race the assignee and dirty the tree that dev-sanity checks.

### Success Criteria

**Acceptance Criteria:**

- [ ] The lead's commands against an assignee's worktree are limited to `git -C <worktree> log`, `git diff`, `gh pr view` and other read-only forms.
- [ ] After the lead's inspection `git -C <worktree> status --porcelain` shows no change the lead made.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0049: Sequencer / Sync

**Status:** Draft  
### Requirement Statement

`bd sync` after import, after each close before the next `bd ready`, at phase end before landing: 0 continue; 1 report, keep working, retry next close; 2 or 4 stop dispatching, report; 3 retry next close.


### Rationale

SKILL.md "Sync" explains `bd sync` exists only for the Dolt remote and is owned by the lead so agents do not race the push (exit 3); its exit-code table fixes the action per code.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd sync` is run after the import, after each close handled in the Loop and before landing at phase end.
- [ ] Exit 0 continues; exit 1 is reported and work continues with a retry at the next close; exit 2 or 4 stops dispatching and is reported; exit 3 is retried at the next close.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0050: Sequencer / Phase end

**Status:** Draft  
### Requirement Statement

When only the root is open, land the stack on the root's `integration_branch`.


### Rationale

SKILL.md Loop: the phase stack is landed on `integration_branch` only after every sprint and finding bead is closed, because the post-mortem is run on that landed head.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd list -l phase-<x> --status open,in_progress,blocked -n 0 --json` lists only the phase root before the stack is landed.
- [ ] After landing, the integration branch head contains the stack's top commit.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0051: Sequencer / Phase end

**Status:** Draft  
### Requirement Statement

Create `<root>-review`; dispatch `review-template.xml.j2` with `branch` = `integration_branch`, `commit` = its fetched pinned head.


### Rationale

SKILL.md "Phase-End Review" and `references/post-mortem.md`: reviewing a stack tip does not satisfy the gate, so the review is pinned to the fetched integration head.

### Success Criteria

**Acceptance Criteria:**

- [ ] `bd show <root>-review` exists with label `stage:review` and parent `<root>`.
- [ ] The `review-template.xml.j2` assignment sets `branch` to `integration_branch` and `commit` to the full SHA of `git rev-parse origin/<integration_branch>` after `git fetch`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0052: Sequencer / Phase end

**Status:** Draft  
### Requirement Statement

Land review-finding fixes on the integration branch; filing reviewers verify there; no full re-sweep.


### Rationale

SKILL.md Phase-End Review: after review findings are filed, "Do not restart a full code sweep for this verification pass"; the filing reviewers verify only the findings they filed.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each review-finding fix is a commit on `integration_branch`.
- [ ] The verification dispatch lists only the filing reviewers and the carried finding ids, and no baseline reviewer set is run again.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::PlanFixRoundTests::test_fix_round_dispatches_only_filing_reviewers`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0053: Sequencer / Phase end

**Status:** Draft  
### Requirement Statement

Route open, regressed or unverified findings from the reconciliation back to their owners.


### Rationale

`references/post-mortem.md` "Verify every resolution": a closed finding is not proof its fix landed, and an open, regressed or unverified finding must go to its owner rather than be closed by the reviewer.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each finding the reconciliation reports as open, regressed, absent or unverified has a message or task assignment to its owning agent naming the bead id.
- [ ] None of those findings is closed by the lead without evidence at the integration SHA.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0054: Sequencer / Phase end

**Status:** Draft  
### Requirement Statement

Confirm the report says `integration_review_passed` and its SHA equals the integration head; then close the root, merge to the base branch, `bd sync`.


### Rationale

SKILL.md Phase-End Review and `references/post-mortem.md` "Report and closure": a stale commit, unverified finding or inventory gap cannot authorize closure, and `check-review-completion.py` enforces the consistency checks that can be checked by script.

### Success Criteria

**Acceptance Criteria:**

- [ ] The review report contains `integration_review_passed` and its `integration_commit` equals `git rev-parse origin/<integration_branch>`.
- [ ] Only then is `bd close <root>` run, followed by the merge to the base branch and `bd sync`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::TemplateContractTests::test_integration_completion_requires_audit_evidence`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0055: Sequencer / Phase end

**Status:** Draft  
### Requirement Statement

Handover: send the incoming lead open task ids, open PRs and the stack number; announce the new lead; in-flight tasks keep their assigner.


### Rationale

SKILL.md "Lead Role": the role can move mid-phase by editing `lead` in `.atm-bd/phase-<x>.toml`; since a close returns to the task's assigner, in-flight tasks keep their assigner and the incoming lead needs the open work, PRs and stack to continue.

### Success Criteria

**Acceptance Criteria:**

- [ ] The outgoing lead's message to the incoming lead contains the open task ids, the open PRs and the stack number.
- [ ] The new lead is announced and `.atm-bd/phase-<x>.toml` names it, while `atm task list` shows in-flight tasks still assigned by the outgoing lead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0056: Sequencer / Reports

**Status:** Draft  
### Requirement Statement

Status: `sprint-report`; rows are never hand-typed.


### Rationale

`sprint-report/SKILL.md` states "Rows are never hand-typed" and the report is the single place sprint status is computed from beads, so a hand-typed row can contradict bead state.

### Success Criteria

**Acceptance Criteria:**

- [ ] A status reply to the user quotes the output of `sprint-report`.
- [ ] Each row in that reply matches a row in the script output.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/sprint-report/tests/test_sprint_report.py::SprintReportTests::test_report_template_and_skill_keep_current_usage_text`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0057: Sequencer / Reports

**Status:** Draft  
### Requirement Statement

QA metrics: `/qa-report`, both QA log tables in the reply, timestamps converted to local.


### Rationale

`qa-report/SKILL.md` makes `/qa-report` read-only and specifies converting the UTC `snapshot_at` and `completed_at` values to local time for display, because the two logs record UTC and a reader compares them to local events.

### Success Criteria

**Acceptance Criteria:**

- [ ] The `/qa-report` reply contains the Log A table (`snapshot_local`, `tot`, `open`, `blk`, `imp`, `min`, `trigger_task`) and the Log B table (`completed_local`, `task`, `sprint`, `tested`, `iteration`, `verdict`, `blk`, `imp`, `min`, `fnd`, `duration`, `pr_number`).
- [ ] The time columns are in local time and the `.sc/qa-log/` files are unchanged.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0058: Sequencer / Scripts

**Status:** Draft  
### Requirement Statement

`validate-plan`: exit 0 valid, 5 problems, 2 cannot run; never edit it, the plan or the graph to pass.


### Rationale

The `validate-plan` header and the atm-beads tests define its exit codes (0 valid, 5 problems, 2 cannot run), and editing the validator, plan or graph to turn a red result green would defeat the gate.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan` exits 0 when the plan is valid, 5 when it reports problems and 2 when it cannot run.
- [ ] No commit or `bd` write by the lead modifies `validate-plan`, the plan file or the graph for the purpose of changing an exit 5 or exit 2 to exit 0.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::ValidatePlan::test_cannot_run`
- `plugins/atm-bd-orchestration/skills/atm-beads/tests/test_validate_plan.py::LivePlan::test_a_missing_live_edge_is_a_problem`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## REQ-TL-0059: Sequencer / Scripts

**Status:** Draft  
### Requirement Statement

`transitions.py` `next_transition`: sanity PASS without QA → create QA bead; QA PASS with only minor open → PASS with backlog; QA FAIL round>=2 → ROUND_CAP; FAIL with blocking/important → one fix round; else wait.


### Rationale

`transitions.py` `next_transition` is the pure decision table the orchestration fixtures use to check the Loop's sanity, QA and fix-round rules without reading bead state.

### Success Criteria

**Acceptance Criteria:**

- [ ] `next_transition` returns `create QA bead` for a closed sanity bead with reason starting `PASS` and no QA bead.
- [ ] It returns `PASS with backlog` for a QA bead closed PASS with only minor findings open, and `ROUND_CAP` for a QA bead closed FAIL with `metadata.round` of 2 or more.
- [ ] It returns `one fix round` for a round-1 FAIL with an open blocking or important finding, and `wait` otherwise.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_transitions.py::TransitionTests::test_json_transition_fixtures`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `skills/atm-bd-orchestration/{SKILL.md, blocking-findings-guidelines.md, formulas/README.md, references/post-mortem.md, roles/quality-mgr.md, scripts/transitions.py}`, `agents/dev-sanity.md` (lead-facing parts), `skills/atm-beads/{SKILL.md, resources/{orchestrating,planning,importing-md-plan,troubleshooting}.md, references/installation-and-troubleshooting.md, scripts/{validate-plan,resolve-role}}`, `skills/sprint-review/SKILL.md`, `skills/sprint-report/SKILL.md`, `skills/qa-report/SKILL.md`.

## Swarm-master

None in the package.

## Unresolved

1. Plan Gate order: `SKILL.md`, `planning.md` run `sprint-review` then `validate-plan` vs `importing-md-plan.md` step 9 the reverse.
2. Integration branch timing: `SKILL.md` Dispatch creates it "before the first dispatch" vs Plan Gate, `sprint-review/SKILL.md`, `validate-plan` needing it on origin before plan review.
