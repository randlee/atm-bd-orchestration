# lite

**ID Range:** REQ-LITE-0001 through REQ-LITE-0023  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-11-07  
**Last Updated:** 2026-11-07  
**Owner:** Rand Lee  

---

## REQ-LITE-0001: Lite profile has dev QA land stages

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite profile manifest `profile.toml` MUST declare the name `lite` and the stages `dev`, `qa` and `land` in that order.
- The lite profile manifest MUST register the hooks `task.assign`, `task.start` and `task.close` and a cron script.

**MUST NOT statements:**

- The lite profile MUST NOT define a sanity stage.


### Rationale

Intent of phase bo (atm-core `docs/plans/phase-bo/intent.md`): "dev → QA, no sanity stage; one agent can run a phase."

### Success Criteria

**Acceptance Criteria:**

- [ ] `load_profile` on `profile.toml` returns name `lite`, stages `[dev, qa, land]` and the three hooks.
- [ ] No template, hook or policy key in the profile mentions a sanity stage.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_profile.py::test_shipped_lite_profile_loads`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/profile.toml:1-17`, `plugins/atm-bd-orchestration/skills/atm-bd-lite/SKILL.md:7-11`. State: implemented (plugins/atm-bd-orchestration/skills/atm-bd-lite/profile.toml:2-10; test_shipped_lite_profile_loads).

## REQ-LITE-0002: Lite owns three separate hook files

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite profile MUST implement `task.assign`, `task.start` and `task.close` as three separate files under `skills/atm-bd-lite/scripts/`.
- Each lite hook file MUST import only `sys` and `atm_bd_types`.
- Each lite hook file MUST be at most 100 lines including header and docstring.


### Rationale

ANC-048 (Rand, 2026-11-01): "I want all three to be independent files and independently tested by jev against the state transition diagrams." ANC-070: each hook file at most 100 lines.

### Success Criteria

**Acceptance Criteria:**

- [ ] `wc -l` on each of the three hook files is at most 100.
- [ ] The boundary test passes for all four scripts.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_boundary.py::test_plugin_files_exist`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py` (51 lines), `atm-bd-task-start-hook.py` (49), `atm-bd-task-hook.py` (100). State: implemented (those files; test_plugin_files_exist).

## REQ-LITE-0003: Lite assign caller must be phase lead

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.assign hook MUST refuse with ASSIGN_NOT_LEAD a caller other than the `lead` named in the phase file.


### Rationale

Hook spec `task-assign.md`, Errors table row ASSIGN_NOT_LEAD: "Only the lead (<lead>) assigns. Ask the lead."

### Success Criteria

**Acceptance Criteria:**

- [ ] An assign by `dev` while the phase file names `lead` is refused ASSIGN_NOT_LEAD with no write.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_caller_not_lead`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:24-25`, `plugins/atm-bd-orchestration/skills/atm-bd-lite/hooks/task-assign.md:14-15`. State: implemented (those lines; test_caller_not_lead). Conflict to resolve with the core records on assigner routing: after a lead change mid-phase the phase file's lead is stale, so a check against the phase file refuses the new lead; the owner may replace this gate with a check against the task's assigner.

## REQ-LITE-0004: Lite assign refuses closed or unready beads

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.assign hook MUST refuse a closed bead with BEAD_CLOSED.
- The lite task.assign hook MUST refuse a blocked or deferred bead with BEAD_NOT_READY.
- The lite task.assign hook MUST refuse a missing assignee with REQUEST_INVALID.
- The lite task.assign hook MUST refuse a bead that is not found with BEAD_NOT_FOUND.

**MUST NOT statements:**

- The lite task.assign hook MUST NOT write in any of these cases.


### Rationale

Hook spec `task-assign.md` transitions T-ASSIGN-03 and T-ASSIGN-04 and its Errors table.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each case returns the named error id and zero writes.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_t_assign_03_closed`
- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_t_assign_04_blocked_and_deferred`
- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_missing_assignee_is_request_invalid`
- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_missing_bead_is_bead_not_found`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:20-37`. State: implemented (those lines; tests).

## REQ-LITE-0005: Lite assign reassigns open or active beads

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.assign hook MUST write the new assignee when the bead is open or in progress and assigned to another agent or to nobody.
- The lite task.assign hook MUST pass through without a write when the bead is already assigned to the named agent.


### Rationale

Hook spec `task-assign.md` transitions T-ASSIGN-01 and T-ASSIGN-02.

### Success Criteria

**Acceptance Criteria:**

- [ ] An in-progress bead assigned to `other` and assigned to `dev` records one assign write by the lead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_t_assign_02_in_progress_other_agent_reassigns`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:29-33`. State: implemented (those lines; test).

## REQ-LITE-0006: Lite start transitions by bead status

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.start hook MUST write in_progress, guarded, for an open bead.
- The lite task.start hook MUST pass through without a write for a bead already in progress.
- The lite task.start hook MUST refuse a closed bead with BEAD_CLOSED.
- The lite task.start hook MUST refuse a blocked or deferred bead with BEAD_NOT_READY.

**MUST NOT statements:**

- The lite task.start hook MUST NOT read the stack ledger.


### Rationale

Hook spec `task-start.md` transitions T-START-01 to T-START-04; its header says it does not read the ledger.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each status yields the transition's reply and the stated number of writes.
- [ ] A start succeeds when the stack bead is absent from the store.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_t_start_01_open_writes_one_start`
- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_t_start_02_in_progress_passes_through`
- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_t_start_03_closed`
- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_t_start_04_blocked_and_deferred`
- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_start_never_reads_the_ledger`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-start-hook.py:27-39`. State: implemented (those lines; tests).

## REQ-LITE-0007: Lite close requires started bead and valid outcome

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST refuse an outcome other than completed, refused or cancelled with REQUEST_INVALID.
- The lite task.close hook MUST refuse a bead that is neither in progress nor closed with BEAD_NOT_READY.
- The lite task.close hook MUST refuse an unknown bead with BEAD_NOT_FOUND.


### Rationale

Hook spec `task-close.md`, flowchart nodes G and S and its Errors table.

### Success Criteria

**Acceptance Criteria:**

- [ ] A close of an open, blocked or deferred bead is refused BEAD_NOT_READY with no write.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_not_started`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_invalid_outcome_is_request_invalid`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_missing_bead`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:20-26`. State: implemented (those lines; tests).

## REQ-LITE-0008: Lite give-back reopens the bead

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST reopen the bead (open, no assignee, guarded) on outcome refused or cancelled.
- The lite task.close hook MUST return the `refuse` template with the reason as its variable.
- The lite task.close hook MUST refuse an empty reason with CLOSE_REASON_EMPTY.
- The lite task.close hook MUST refuse a give-back of a closed bead with BEAD_CLOSED.


### Rationale

Intent of phase bo: "Dev, on refusal: `atm task close refused` with a reason. Hook: reopen the bead (open, unassigned)". Hook spec `task-close.md` T-CLOSE-01.

### Success Criteria

**Acceptance Criteria:**

- [ ] A refused close writes one reopen and returns template `refuse.md` with `{reason}`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_01_refused_reopens_and_returns_refuse_template`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_01_cancelled_same_as_refused`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_01_missing_reason`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_closed_bead_cannot_be_given_back`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:28-34`. State: implemented (those lines; tests).

## REQ-LITE-0009: Lite dev close needs report and recorded layer

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST refuse a dev or fix close without an inline report with CLOSE_REPORT_NOT_INLINE.
- The lite task.close hook MUST refuse a dev or fix close whose branch has no layer on the stack ledger with STACK_NOT_RECORDED.
- The lite task.close hook MUST close the bead with the layer (branch, head, pr, base) as evidence and return the `dev-close` template.


### Rationale

Intent of phase bo: "Hook: check the report is present and the ledger holds the dev's layer; close the bead with that evidence."

### Success Criteria

**Acceptance Criteria:**

- [ ] A completed dev close with a recorded layer writes one close with the layer and returns `dev-close.md` with branch, head, pr and base.
- [ ] A fix-stage bead behaves the same.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_02_layer_recorded_closes_with_layer_evidence`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_02_report_missing`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_02_layer_not_on_ledger`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_02_fix_stage_is_work_close`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:35-42`. State: implemented (those lines; tests).

## REQ-LITE-0010: Lite QA pass needs the target head

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST refuse a QA close whose verdict block is invalid with QA_VERDICT.
- The lite task.close hook MUST refuse a QA close whose bead has no `checked_bead` with QA_NOTHING_TO_REVIEW.
- The lite task.close hook MUST refuse a PASS whose sha differs from the head of the checked bead's recorded layer with QA_NOT_ON_STACK.
- The lite task.close hook MUST close a valid PASS with the sha as evidence and return the `qa-pass` template.


### Rationale

Intent of phase bo: "QA, on pass: ... Hook: verdict sha is the target layer's head; close with that evidence."

### Success Criteria

**Acceptance Criteria:**

- [ ] A PASS at the recorded head closes with one write; a PASS at another sha is refused with no write.
- [ ] A QA bead without `checked_bead` never selects a closed work bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_03_pass_closes_with_sha`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_03_sha_differs`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_03_no_target`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_03_invalid_verdict`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_qa_without_checked_bead_does_not_select_a_closed_work_bead`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:43-56`. State: implemented (those lines; tests).

## REQ-LITE-0011: Lite QA findings must be poured first

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST refresh the finding beads, the sprint bead and, when any finding is non-blocking, the phase bead once before it checks them.
- The lite task.close hook MUST refuse a FINDINGS close with FINDINGS_NOT_POURED when a blocking finding's bead does not block the sprint bead.
- The lite task.close hook MUST refuse a FINDINGS close with FINDINGS_NOT_POURED when a non-blocking finding's bead does not block the phase bead.
- The lite task.close hook MUST close a valid FINDINGS verdict with the sha and finding ids and return the `qa-findings` template.


### Rationale

Intent of phase bo: "pour each finding ... (blocking findings block the sprint bead; non-blocking block the phase bead) ... The QA bead cannot close until blocking findings are poured."

### Success Criteria

**Acceptance Criteria:**

- [ ] A blocking finding that blocks the sprint closes; one that does not is refused.
- [ ] A finding id with no bead is refused.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_04_poured_findings_close_qa`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_04_blocking_finding_not_blocking_sprint`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_04_non_blocking_finding_must_block_phase`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_04_finding_bead_missing`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_04_sha_differs`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:57-80`. State: implemented (those lines; tests).

## REQ-LITE-0012: Lite land close needs the merged sha

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST close a land task only when the report holds one fenced JSON block with a 40-hex `merged` sha.
- The lite task.close hook MUST refuse any other land report with LAND_EVIDENCE.
- The lite task.close hook MUST return the `land-close` template with the sha.


### Rationale

Hook spec `task-close.md` T-CLOSE-05.

### Success Criteria

**Acceptance Criteria:**

- [ ] A report with `{"merged":"<40 hex>"}` closes with that sha; "no sha" is refused.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_land_close_requires_merge_sha`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:81-84`. State: implemented (those lines; test).

## REQ-LITE-0013: Lite repeated close replays without writing

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite task.close hook MUST return the same validated close action for a completed close of an already closed bead.
- The lite task.close hook MUST validate the transition again before it returns that action.

**MUST NOT statements:**

- The lite task.close hook MUST NOT write a bead when the bead is already closed.


### Rationale

Hook spec `task-close.md` header: a completed re-close revalidates the transition and returns only its close action, without a bead write.

### Success Criteria

**Acceptance Criteria:**

- [ ] A closed dev bead and a closed QA bead each replay their template with zero writes.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_closed_bead_replays_only_the_close_action`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_closed_qa_replays_validated_pass_without_a_write`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:86-87`. State: implemented (those lines; tests).

## REQ-LITE-0014: Lite cron assigns ready dev beads

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite cron decision MUST assign each ready, open dev bead that has no ATM task to the agent named by policy param `dev_agent` using the template named by `dev_template`.
- The lite cron decision MUST decide nothing when the ATM task list is unavailable.


### Rationale

ANC-074 (Rand, 2026-11-01): "wait, lite will have cron. / yes, initial cron script will assign 'bdc ready' qa tasks and run a set of checks similar to atm-bd-orchestration".

### Success Criteria

**Acceptance Criteria:**

- [ ] A ready open dev bead without a task yields one Assign.
- [ ] A failed task read yields no actions.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_no_assignment_when_task_read_fails_or_task_already_exists`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py:12-19,38-41`. State: implemented (those lines; test). The fixed agent names come from `policy.toml:2` and conflict with the core record that the planning assignee is a class.

## REQ-LITE-0015: Lite cron assigns ready QA beads

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite cron decision MUST assign each ready, open QA bead that has no ATM task to the agent named by `qa_agent` with a review target of repo, PR number, branch and head commit.
- The lite cron decision MUST report `cron:review:<bead>` to the lead when the repo, the checked dev bead or the recorded layer's branch, PR or head is missing.

**MUST NOT statements:**

- The lite cron decision MUST NOT assign a QA bead whose checked dev bead already has an ATM task.


### Rationale

ANC-074 (2026-11-01) and phase-bo design: the QA bead is blocked by its dev bead and, when the dev bead closes, is assigned by the existing `atm task assign` path.

### Success Criteria

**Acceptance Criteria:**

- [ ] The QA assignment carries repo, pr_number, branch and commit from the recorded layer.
- [ ] A QA bead without `checked_bead` yields a Report, not an Assign.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_qa_assignment_has_recorded_target`
- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_qa_without_checked_bead_reports_instead_of_choosing_closed_work`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py:19-20,27-50,61-63`. State: implemented (those lines; tests). QA task assignment uses the lead as assigner today (see the core assigner record).

## REQ-LITE-0016: Lite cron lands after QA and green CI

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite cron decision MUST assign a ready land bead only after no QA task of the same sprint remains in the ATM task list.
- The lite cron decision MUST assign a land bead only when CI is passing on the head of the top recorded layer.
- The lite cron decision MUST report `cron:ci:<bead>` to the lead when CI on that head is failing.

**MUST NOT statements:**

- The lite cron decision MUST NOT assign a land bead while CI is pending, absent, or collected for a different head.


### Rationale

Commit 6205cfe14 (Wait for passing CI before assigning lite landing).

### Success Criteria

**Acceptance Criteria:**

- [ ] Pending, none, other-head and unknown CI yield no action; failing yields a Report; passing yields an Assign.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_land_waits_for_open_qa_task_in_same_sprint`
- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_land_requires_passing_ci_on_exact_head`
- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_land_missing_branch_or_pr_reports`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py:21-26,51-60`. State: implemented (those lines; tests).

## REQ-LITE-0017: Lite policy names no default lead

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite `policy.toml` MUST name the agent that receives the land task as a value read from the phase file's `lead`.

**MUST NOT statements:**

- The lite `policy.toml` MUST NOT set `lead = "team-lead"`.


### Rationale

Rand (2026-11-07): "The phase lead is defined in the phase file and never defaults to team-lead."

### Success Criteria

**Acceptance Criteria:**

- [ ] `policy.toml` contains no `team-lead`; a land Assign targets the phase file's lead.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/policy.toml:6`, `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py:32`. State: not yet implemented (`policy.toml:6` sets `lead = "team-lead"` and `atm-bd-cron.py:32` assigns the land task to that param).

## REQ-LITE-0018: Lite cron reports missing policy params

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite cron decision MUST report `cron:params:<bead>` to the lead when the agent or template param for the bead's stage is empty.


### Rationale

`atm-bd-cron.py` reports instead of assigning with a missing param.

### Success Criteria

**Acceptance Criteria:**

- [ ] A policy without `qa_template` yields a config Report once, then a row on the next tick.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_missing_params_report_goes_to_the_lead_once_then_stays_a_row`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py:33-37`. State: implemented (those lines; test).

## REQ-LITE-0019: Lite dev template carries the stack block

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite dev template MUST contain a setup block that locks the stack bead, creates an isolated worktree on the stack top and releases the lock on exit.
- The lite dev template MUST contain a stack block that locks the stack bead, rebases onto the top, pushes, creates the pull request with the provider command and records the layer (branch, head, pr, base) on the stack bead.
- The lite dev template MUST tell the dev to close only with `atm task close <task> completed --stdin` and an inline report.

**MUST NOT statements:**

- The lite dev template MUST NOT instruct the dev to write its own task bead.


### Rationale

Intent of phase bo: "The stack bead is an atomic ledger. Its assignee is the lock ... in one fenced block in the dev template. No script, no hook writes the ledger." ANC-067.

### Success Criteria

**Acceptance Criteria:**

- [ ] The template has two fenced bash blocks whose lines are, in order, lock, rebase, push, record.
- [ ] The template contains the close instruction.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/templates/dev.xml.j2:21-69`. State: implemented (those lines); no test asserts the block order. Claim lines use `$ATM_IDENTITY` without `--actor` (see the core claim-actor record) and call `bd` directly although ANC-063 requires bd_cache_rs.

## REQ-LITE-0020: Lite QA template carries the pour block

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite QA template MUST contain a fenced block that creates each finding bead and adds its blocking edge to the sprint bead (blocking) or the phase bead (non-blocking).
- The lite QA template MUST require the close report to end with one fenced JSON verdict holding `verdict`, `sha` and, for FINDINGS, each poured `id` with its `blocking` flag.
- The lite QA template MUST direct QA to verify the exact layer head and report evidence for every criterion.


### Rationale

Intent of phase bo: pour each finding in a fenced block, then close with the report listing the poured ids.

### Success Criteria

**Acceptance Criteria:**

- [ ] The template contains `bd dep add` to `$SPRINT` or `$ROOT` per the blocking flag and the verdict shape.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/templates/qa.xml.j2:14-49`. State: implemented (those lines); only the strict-render test covers it.

## REQ-LITE-0021: Lite land template merges only the assigned head

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite land template MUST compare the pull request head with the assigned commit and require all checks passing before merge.
- The lite land template MUST close the task refused when the head changed or checks are not passing.
- The lite land template MUST merge with a merge commit and close completed with a JSON block holding the merged sha.

**MUST NOT statements:**

- The lite land template MUST NOT merge a second time when the task close failed.


### Rationale

Project rule: always merge with a merge commit; the close hook requires the merged sha (T-CLOSE-05).

### Success Criteria

**Acceptance Criteria:**

- [ ] The template's block exits after a refused close when the head differs and uses `gh pr merge --merge`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/templates/land.xml.j2:13-32`. State: implemented (those lines); only the strict-render test covers it.

## REQ-LITE-0022: Lite close reports render from evidence

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The `dev-close` template MUST render branch, head, pr and base.
- The `qa-pass` template MUST render sha.
- The `qa-findings` template MUST render sha and ids.
- The `land-close` template MUST render sha.
- The `refuse` template MUST render reason.


### Rationale

Each template declares `required_variables` matching the evidence the close hook returns.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each template's `required_variables` equals the variable set the hook supplies.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_02_layer_recorded_closes_with_layer_evidence`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/templates/dev-close.md.j2`, `qa-pass.md.j2`, `qa-findings.md.j2`, `land-close.md.j2`, `refuse.md.j2`. State: implemented (those files).

## REQ-LITE-0023: Lite roles get startup instructions

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The lite profile MUST declare startup messages for the `dev_agent`, `qa_agent` and `lead` roles through `[startup]` mapped to policy params.
- Each lite startup message MUST tell the agent to work only from the assigned template and to use `atm task start` and `atm task close` as the only task transitions.

**MUST NOT statements:**

- Each lite startup message MUST NOT permit the agent to write its own task bead or run cache commands.


### Rationale

Commit 807625ab0 (Install lite role startup instructions).

### Success Criteria

**Acceptance Criteria:**

- [ ] `profile.toml` `[startup]` maps three roles to existing policy params; the installer writes them to `.atm.toml`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/install/test_profile_install.py::test_startup_uses_arbitrary_declared_policy_parameters`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/profile.toml:19-22`, `plugins/atm-bd-orchestration/skills/atm-bd-lite/policy.toml:9-11`. State: implemented (those lines; test).
