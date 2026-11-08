# dev

**ID Range:** REQ-DEV-0001 through REQ-DEV-0031  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-20  
**Owner:** Rand Lee  

---

## REQ-DEV-0001: All assignments

**Status:** Draft  
### Requirement Statement

The task id is the bead id; `bd show <bead>` is the assignment; the bead wins over the template and the mismatch is reported.


### Rationale

The dispatched assignment text is rendered once, while the bead keeps changing; the dev template therefore names the bead as the authority (`bd show` is the assignment) and tells the dev to report a difference instead of coding to stale text.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` states that `bd show {{ task_id }}` is the assignment and that its description, design, acceptance criteria and metadata are authoritative.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c states that when the assignment and the bead differ the bead wins and the mismatch is reported.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` sets the task id and the bead id to the same `task_id` value (`atm-task id="{{ task_id }}"` and `bd show {{ task_id }}`).

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0002: All assignments

**Status:** Draft  
### Requirement Statement

Start a task only after the previous one is closed; after each close read ATM, and only then does the next task start.


### Rationale

A dev holds one task at a time; each template ends with an explicit step that the next queued task starts only after the close and a fresh read of ATM, so queued work is not started in parallel or from a stale inbox.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step h reads: after the close, read ATM again, and the next queued task starts only now.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step g carries the same sentence.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0003: All assignments

**Status:** Draft  
### Requirement Statement

Work only on the assigned branch and worktree. Never run `gh stack link/sync/rebase/merge` or `bd sync` (the lead is the stack writer and owns sync); `--actor "$ATM_IDENTITY"` on every `bd` write.


### Rationale

The task assigner is the only stack writer and `bd sync` is owned by the lead, so devs on concurrent branches must not link, rebase or merge a stack; `SKILL.md` records `--actor "$ATM_IDENTITY"` as the required identity on every `bd` write.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` `stack-discipline` states that work happens only on the assigned branch and that `gh stack link`, `sync`, `rebase` and `merge` are never run by the dev.
- [ ] Every `bd close` and `bd update` command in the rendered dev-template and fix-assignment steps carries `--actor "$ATM_IDENTITY"`.
- [ ] Neither rendered template contains the command `bd sync`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_a1_fires_on_not_ready_and_every_bd_write_has_an_actor`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0004: All assignments

**Status:** Draft  
### Requirement Statement

Before claiming: dev rebases onto `origin/<pr_target>` (a conflict is part of the work); dev-fix and fix only fetch (their branch was cut from the stack top). Then run `assignment-gates.py dev`; `READY`: `bd update <bead> --claim`, then `atm task start <bead> "<one line>"`.


### Rationale

A dev branch that is not based on its `pr_target` produces a layer that cannot land; the rebase-then-gate order and the `READY` handoff make the base check true before any claim. A fix branch is cut from the stack top, so it only fetches and the gate proves ancestry without moving a frozen layer.

### Success Criteria

**Acceptance Criteria:**

- [ ] In `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step a, `git fetch origin && git rebase origin/<pr_target>` appears before `assignment-gates.py dev`.
- [ ] In `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step a, `git fetch origin` appears before `assignment-gates.py dev` and the step contains no `git rebase`.
- [ ] On `READY` both templates run `bd update <bead> --claim --actor "$ATM_IDENTITY"` and then `atm task start <bead> "<one line>"`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_dev_step_a_rebases_before_the_gate`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_fix_step_a_on_a_branch_cut_from_the_top_only_checks_ancestry`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0005: All assignments

**Status:** Draft  
### Requirement Statement

`NOT_READY`: do not claim or start; find the blockers; close the task `refused` (`bead_state` open), `reason_md` = bead, cause, who must move and the dependency to add (`bd dep add <bead> --blocked-by <blocker>`). A blocker met mid-task (work another bead or agent owns that is not done; a shared change you can make yourself is a quick fix, 26, and the task continues): return the bead open, unassigned, blocker in notes, close the task `refused` the same way. Never wait.


### Rationale

A dev that claims a bead whose blocker is open, or waits for it, holds the bead and its queue; commit 672edc0c4 and 7c51a9c71 made refusal with the dependency edge the rule so `bd ready` lists the bead again only after the blocker closes.

### Success Criteria

**Acceptance Criteria:**

- [ ] In the rendered dev-template and fix-assignment, the `NOT_READY` step (a1) says not to claim or start, and closes the task `refused` with `bead_state` `open`.
- [ ] The a1 step's `reason_md` guidance names the bead, the cause, who must move and the command `bd dep add <bead> --blocked-by <blocker>`.
- [ ] The mid-task blocker text returns the bead with `--status open --assignee ""` and `BLOCKED: <blocker>`, closes the task `refused`, and says `never stay active waiting`; a shared change the dev can make itself is routed to a Parallel Quick Fix (step d1) and the task continues.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_the_not_ready_step_refuses_and_leaves_the_bead_open`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_a_mid_task_blocker_returns_the_bead_open_and_refuses`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_a_shared_change_the_dev_can_make_is_a_quick_fix_not_a_blocker`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0006: All assignments

**Status:** Draft  
### Requirement Statement

Any other gate code: close the task `refused` with the code, command and failure evidence in `reason_md`; leave the bead unchanged when the gate fails before claim.


### Rationale

On 2026-10-20 three dispatches were refused with `GATE_CANNOT_RUN` and the lead had to re-issue them (commit fc85adda5); the refusal must carry the code, command and failure evidence so the lead can tell a load timeout from a real defect, and an unclaimed bead is left unchanged so it can be re-dispatched.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step a says that on refusal before claiming the task is closed `refused` with the step g1 template, the bead is left unchanged, and `reason_md` includes the refusal code, command and failure evidence.
- [ ] `assignment-gates.py dev` prints a typed code (`PLAN_INVALID`, `UNCLAIMABLE`, `PR_TARGET_MISMATCH`, `WRONG_BASE` or `GATE_CANNOT_RUN`) and, for a command that fails, names the command on stderr.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_runner_timeouts_are_typed_and_name_command`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0007: All assignments

**Status:** Draft  
### Requirement Statement

Commit as items land and push early; a push or `atm send` closes nothing.


### Rationale

Work that exists only in a worktree is lost when the agent or host stops; the template requires early pushes and states that a push or a message closes nothing, so completion is only the task close.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d says to commit on the branch as items land and to push early with `git push -u origin <branch>`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d says a push is not a close and needs no report.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0008: All assignments

**Status:** Draft  
### Requirement Statement

Never weaken a test, skip a criterion, or leave a placeholder; run `<test_command>` and `<lint_command>` (dev and dev-fix: also the bead's validation commands) to zero failures, including lint failures inherited from a lower layer.


### Rationale

A dev that weakens a test or leaves lint red hands the failure to sanity and QA; the 0.12.1 release made `lint_command` a required variable and made a lint failure inherited from a lower layer the dev's own to fix (commit 367090bf9, changelog 0.12.1).

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step e forbids weakening a test, skipping a criterion or leaving a placeholder.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step e runs `test_command`, `lint_command` and the bead's validation commands until they pass with zero failures, and says a lint failure inherited from a lower layer is fixed on this layer.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` front matter lists `test_command` and `lint_command` as required variables.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0009: All assignments

**Status:** Draft  
### Requirement Statement

Before closing, the dev rebases onto the stack's current top (`assignment-gates.py stack-top --root <phase-root> --pr-target <pr_target> --worktree <worktree>`; any other exit is a code to refuse with, never a guess), re-runs the tests, force-pushes and opens the PR against that top (never draft; a quick-fix finding fixed on a branch that already has its PR keeps that PR), then runs `/sc-gh-stack-view`.


### Rationale

The stack top moves while a dev works; opening a PR against a stale base breaks the append-only stack, so the template reads the top from `assignment-gates.py stack-top` and refuses with `GATE_CANNOT_RUN` instead of guessing (changelog 'Stack review round 3', commit f0f4b5f13).

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step f runs `assignment-gates.py stack-top --root <phase_root> --pr-target <pr_target> --worktree <worktree>` and says any other exit than 0 is refused with `GATE_CANNOT_RUN`, never guessed.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step f runs `git rebase origin/<top>` and `git push --force-with-lease origin <branch>`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step f opens the PR with `gh pr create --base <top> --head <branch>`, never `--draft`, and uses `gh pr edit` when a PR is already open on the branch.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_every_dev_lands_its_pr_on_the_current_stack_top`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_stack_top_reads_the_phase_ledger_and_rejects_invalid_data`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0010: All assignments

**Status:** Draft  
### Requirement Statement

Close bead and task together with the close template, `bd close` first and the task only if it succeeded; the close carries the pushed head, the top rebased onto, the PR and the verbatim `/sc-gh-stack-view` output. The task close is the report.


### Rationale

A completion must be one atomic, evidenced act: commit 32e475caf moved the dev/fix close into the `atm-task-close.py` hook so the bead close, task close and report cannot diverge, and the hook derives head, PR and base from git instead of the dev typing them.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g completes only through `atm-task-close.py --role dev --vars <lead-supplied-vars-file> --result <your-result-file>` and says the hook closes the bead and then the ATM task and sends the completion report.
- [ ] The rendered `dev-complete.md.j2` report requires `rebased_onto`, `pr_url`, `deliverables_md` and `validation_md`, and carries `commit` and `pr_number` when the hook supplies them.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g says the hook derives `commit`, `pr_number`, `pr_url` and `rebased_onto` from git and the open PR, and that the dev does not type them.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`. Shared rule: REQ-CORE-0011.

## REQ-DEV-0011: Dev (`dev-template`)

**Status:** Draft  
### Requirement Statement

Read the bead: scope, deliverables, deletion targets, validation, acceptance criteria; `metadata.owned_paths` is the fence; a field the poured dev bead lacks comes from its sprint container.


### Rationale

Dev beads are poured with fields held on the sprint container; the template tells the dev where each field lives so the file fence (`owned_paths`) and deliverables are not guessed.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c says `bd show <task_id>` is authoritative for scope, deliverables, deletion targets, validation and acceptance criteria.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c names `metadata.owned_paths` as the file fence.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c says a field the poured dev bead lacks comes from `bd show <metadata.sprint_bead>`.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0012: Dev (`dev-template`)

**Status:** Draft  
### Requirement Statement

Read every `metadata.requirements` and `metadata.adrs` id; satisfy each; `NONE` but the work touches one: tell the task assigner before coding past it.


### Rationale

QA scores a change against the requirement and ADR ids in the bead; reading them before coding and reporting an undeclared touch prevents a drift QA would otherwise find after the layer is built.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c requires reading every id in `metadata.requirements` and `metadata.adrs` before coding and says the change must satisfy each.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c says that when the plan declares `NONE` but the work touches a requirement or ADR, it is reported to the task assigner before coding past it.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0013: Dev (`dev-template`)

**Status:** Draft  
### Requirement Statement

Read `policy_path` and every guideline it names for the languages touched.


### Rationale

Reviewers score against the repository QA policy and its named guidelines, so the template makes the dev read them before editing.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step c0 requires reading `policy_path` before editing and every guideline it names for the languages the task touches.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` front matter lists `policy_path` as a required variable.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0014: Dev (`dev-template`)

**Status:** Draft  
### Requirement Statement

Read the complete plan and enumerate all tasks that must be completed in the primary and any child beads; create an itemized private checklist outside the tracked tree with every task identified; work through the checklist one item at a time; then go through it again one item at a time and confirm each is fully met; nothing outside the bead's scope.


### Rationale

Commit a126d5d65 mandated a private checklist worked and verified one item at a time so no deliverable of a multi-part bead is silently skipped; the checklist stays outside the tracked tree so it is not committed.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d requires reading the whole plan, enumerating every task in the primary and child beads, and creating an itemized private checklist outside the tracked tree.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d requires working through the checklist one item at a time.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step e requires going through the checklist again one item at a time and confirming each item is fully met.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d limits the work to the bead's deliverables and acceptance criteria.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_every_dev_assignment_has_the_itemized_private_checklist`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0015: Dev (`dev-template`)

**Status:** Draft  
### Requirement Statement

Close: `bd close --reason "dev complete at <short sha>"` + `dev-complete.md.j2` with the deliverable inventory and gate output; deletion work adds a before/after inventory.


### Rationale

Sanity and QA are triggered by a dev bead's close and read its reason; the close reason `dev complete at <sha>` and the deliverable inventory give them a fixed anchor, and the hook (commit 32e475caf) now writes both.

### Success Criteria

**Acceptance Criteria:**

- [ ] `atm-task-close.py` closes a dev bead with the reason `dev complete at <commit>` (the string built at the `dev complete` branch of its close reason).
- [ ] The rendered `dev-complete.md.j2` lists `deliverables_md` with `deliverables_complete` of `deliverables_total`, and renders `inventory_md` when supplied (the deletion before/after inventory).
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g names the result field `deliverables_md` and instructs the dev to write only its own fields.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0016: Dev (`dev-template`)

**Status:** Draft  
### Requirement Statement

Cannot complete: include the reason, command and failure evidence in the task refusal's `reason_md`; `bd update --status blocked --assignee "" --append-notes "DEV_CANNOT_COMPLETE; ..."`; never `bd close` (it would release the sanity check); task `refused`. Unfinished is a failure.


### Rationale

A dev bead closed unfinished would release its sanity check on incomplete work, so the template routes a failure to a blocked bead and a refused task; 'an unfinished deliverable is a failure, not a completion'.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g1 requires the refusal's `reason_md` to include the reason, command and failure evidence.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g1 runs `bd update <task> --status blocked --assignee "" --append-notes "DEV_CANNOT_COMPLETE; <reason>" --actor "$ATM_IDENTITY"`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g1 says never `bd close` a bead that cannot be completed and closes the task `refused` with `task-refused.md.j2`.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0017: Dev-fix (`dev-fix`)

**Status:** Draft  
### Requirement Statement

Not ready while `closed` means never reopened. The fixes go on the assigned new layer cut from the stack's top; the sprint's first layer (`pr_target`) and any fix layer above it are frozen: never rebase, re-target or push them.


### Rationale

A fix attached to a frozen layer would rewrite history other reviewers already pinned; commit 858cbb88b and d935e4cb2 retired the separate dev-fix template, so the same append-only rule now lives in the fix-assignment template, which cuts each fix as a new layer from the stack top.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` `stack-discipline` states the finding is on a frozen layer and the branch is a new layer cut from `origin/<pr_target>`, the top of the stack at dispatch.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` `stack-discipline` states the dev works only on its branch and never runs `gh stack link`, `sync`, `rebase` or `merge`.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0018: Dev-fix (`dev-fix`)

**Status:** Draft  
### Requirement Statement

Read the complete plan and enumerate all tasks that must be completed in the primary and any child beads (`bd list --parent <bead> --status open --json`); create an itemized private checklist outside the tracked tree with every task identified; work through the checklist one item at a time, closing each child when fixed; then go through it again one item at a time and confirm each is done.


### Rationale

As for a dev bead, commit a126d5d65 mandated the private checklist so no item of a multi-finding fix is missed; fix beads can carry child findings.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step d requires reading the complete finding and remedy, listing every required task and creating an itemized private checklist outside the tracked tree.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step d requires working through the checklist one item at a time and then going through it again confirming each is done.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_every_dev_assignment_has_the_itemized_private_checklist`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0019: Dev-fix (`dev-fix`)

**Status:** Draft  
### Requirement Statement

Re-check the whole bead; re-read its requirements and ADRs.


### Rationale

A fix can regress the requirement it was found against; the fix template makes the fixer re-read the scope the bead came from and the finding's requirement and ADR ids before editing.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step b requires reading `bd show <task_id>`, then its `metadata.sprint_bead`, then every id in the bead's `metadata.requirements` and `metadata.adrs`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step b says the fix must keep satisfying those requirements and ADRs.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0020: Dev-fix (`dev-fix`)

**Status:** Draft  
### Requirement Statement

Close and cannot-complete as Dev 15 and 16, the deliverables listing each finding and its fix.


### Rationale

The completion contract for fix and dev is the same hook; a fix report must list what was fixed so the filing reviewer can verify each finding.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step f completes through `atm-task-close.py --role fix` with a result file that includes `deliverables_md` and `resolution_md`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step f1 gives the cannot-fix path (bead left open, `FIX_CANNOT_COMPLETE` in notes, task `refused`), matching `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step g1.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0021: Fix (`fix-assignment`)

**Status:** Draft  
### Requirement Statement

Read the bead, its `metadata.sprint_bead`, and the finding's requirements and ADRs; read `policy_path` and its guidelines.


### Rationale

A finding's fix is judged against the requirements, ADRs and QA policy of the sprint it belongs to, so the fixer reads them before editing.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step b requires reading the bead and its `metadata.sprint_bead` and the requirement and ADR ids named in the bead's metadata.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step b requires reading `policy_path` and every guideline it names for the languages the fix touches before editing.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0022: Fix (`fix-assignment`)

**Status:** Draft  
### Requirement Statement

Confirm the defect at the cited file:line; absent: no work, close `not_reproducible` with the file:line checked.


### Rationale

A finding can be stale (already fixed, superseded or the code path gone); the template forbids speculative work and requires a recorded check, so closed-as-not-reproducible is evidenced by the file:line looked at.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step c requires verifying the defect still exists at the cited file:line in the worktree.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step c says that when it does not reproduce no work is done and the bead is closed as not reproducible citing the file:line checked.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0023: Fix (`fix-assignment`)

**Status:** Draft  
### Requirement Statement

Fix every in-scope occurrence of the pattern; touch only what the remedy needs.


### Rationale

A repeatable defect fixed in one place leaves the same finding for the next QA round; the fixer is told to search for and fix every occurrence while touching only what the remedy needs.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step d says to fix every occurrence in scope, and for a repeatable pattern to search the worktree and fix each one.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step d says to touch only the files the remedy needs.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0024: Fix (`fix-assignment`)

**Status:** Draft  
### Requirement Statement

Close: `bd close --reason "fixed at <short sha>"` (or `"not reproducible: <file:line>"`) + `fix-complete.md.j2`, outcome `fixed` (with commit and PR) or `not_reproducible` (none).


### Rationale

A not-reproducible close has no commit or PR, while a fixed close must carry both; the hook's close reason and the `fix-complete` template encode that difference so sanity and QA are routed correctly.

### Success Criteria

**Acceptance Criteria:**

- [ ] `atm-task-close.py` closes a fix bead with the reason `fixed at <commit>` for outcome `fixed` and `not reproducible: <evidence>` for outcome `not_reproducible`.
- [ ] Rendering `fix-complete.md.j2` with outcome `fixed` fails without `commit` and `rebased_onto`, and fails without `pr_number` or `pr_url`.
- [ ] Rendering `fix-complete.md.j2` with outcome `not_reproducible` and no commit succeeds and prints no `Commit:` line.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_not_reproducible_needs_no_commit_but_fixed_does`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0025: Fix (`fix-assignment`)

**Status:** Draft  
### Requirement Statement

Cannot fix: include the reason, command and failure evidence in the task refusal's `reason_md`; return the bead open, unassigned, `FIX_CANNOT_COMPLETE` in notes; task `refused`. Never close a finding unfixed.


### Rationale

Closing a finding unfixed would hide it from the QA that filed it; only quality-mgr or the task assigner may do so, so a fixer that cannot fix returns the bead open with a recorded cause.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step f1 requires the refusal's `reason_md` to include the reason, command and failure evidence.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step f1 runs `bd update <task> --status open --assignee "" --append-notes "FIX_CANNOT_COMPLETE; <reason>" --actor "$ATM_IDENTITY"` and closes the task `refused`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step f1 says the fixer never closes a fix or finding bead unfixed.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0026: Parallel quick fix (finder)

**Status:** Draft  
### Requirement Statement

A change other live branches need never goes in your layer: stop and tell the task assigner the change and the branches it breaks.


### Rationale

A shared type or trait change made inside one branch breaks the other live branches that carry the old signature; commit 7e19b2a2f made such a change a separate quick-fix layer and the dev stops and tells the assigner first.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d1 says that when the work needs a change other live branches need at the same time, the dev stops that edit and tells the task assigner the exact change and the branches it breaks.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/fix-assignment.xml.j2` step d1 states the same obligation.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_a_shared_change_the_dev_can_make_is_a_quick_fix_not_a_blocker`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0027: Parallel quick fix (finder)

**Status:** Draft  
### Requirement Statement

The lead picks the quick fix's `pr_target` (a lower bound); the finder cuts `fix/<thing>` from the stack's current top (`stack-top --root <phase-root> --pr-target <pr_target> --worktree <worktree>`) in its own worktree: only the change, compiler-forced implementors/call sites, one test for a bug; test passes; push; PR against that top as a new layer, never into a lower layer or the integration branch; report the PR by plain `atm send`.


### Rationale

A quick fix landing in a lower layer or the integration branch would reorder a stack other layers already build on; commit 7e19b2a2f (R4, R5, B1-B4) defined it as a new layer on the current top with `pr_target` as a lower bound.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d1 points the dev to the Parallel Quick Fix section of `SKILL.md` for the base to follow.
- [ ] The Parallel Quick Fix section of `SKILL.md` has the lead set the quick fix's `pr_target` as a lower bound and the finder cut `fix/<thing>` from the output of `assignment-gates.py stack-top`.
- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d1 says the dev reports the quick-fix PR by plain `atm send`.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0028: Parallel quick fix (finder)

**Status:** Draft  
### Requirement Statement

Sprint task stays open; continue on the rebased layer.


### Rationale

A quick fix is a side branch of the same work; closing the sprint task for it would hand an unfinished bead to sanity.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/templates/dev-template.xml.j2` step d1 and the sentence 'A shared change you can make yourself is not a blocker: it is a Parallel Quick Fix (step d1) and the task continues' in step g1 keep the sprint task active after the quick fix is reported.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_a_shared_change_the_dev_can_make_is_a_quick_fix_not_a_blocker`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0029: Scripts

**Status:** Draft  
### Requirement Statement

`assignment-gates.py dev` prints one code; exit 0 `READY`, 2 `GATE_CANNOT_RUN`, 5 otherwise. Every command the gates run is bounded by `ATM_BD_GATE_TIMEOUT_S` seconds (default 180; validate-plan at least 300); a timeout is `GATE_CANNOT_RUN` whose stderr names the command and the fix (retry once, or raise `ATM_BD_GATE_TIMEOUT_S` on a loaded host). A value that is not a positive integer is also `GATE_CANNOT_RUN` whose stderr names the value and the fix. `stack-top --root <phase-root> --pr-target <b> --worktree <worktree>` prints the last layer's branch from `<phase-root>.stack` on exit 0. With no layers it resolves `origin/<b>` and prints `<b>`; unreadable or invalid ledger data or an unresolvable fallback returns `GATE_CANNOT_RUN` (2).


### Rationale

On 2026-10-20 a fixed 30 s bound refused three dispatches in a row under load; commits fc85adda5 and dc9323421 made the bound configurable with a 180 s default, typed errors that carry the fix, and no traceback for a bad value. `stack-top` gives the devs one command instead of guessing the stack top.

### Success Criteria

**Acceptance Criteria:**

- [ ] `assignment-gates.py dev` prints exactly one code, exits 0 for `READY`, 2 for `GATE_CANNOT_RUN` and 5 for every other code.
- [ ] With `ATM_BD_GATE_TIMEOUT_S` unset the command timeout is 180 seconds; a set value replaces it, and `validate-plan` is bounded by at least 300 seconds.
- [ ] A command that times out prints `GATE_CANNOT_RUN` and a stderr message naming the command and `retry once, or raise ATM_BD_GATE_TIMEOUT_S`.
- [ ] A value that is not a positive integer prints `GATE_CANNOT_RUN`, a stderr message naming the value and `ATM_BD_GATE_TIMEOUT_S=180`, and no traceback.
- [ ] `stack-top` with layers in `<phase-root>.stack` prints the last layer's branch and exits 0; with no layers it prints `<pr-target>` after resolving `origin/<pr-target>`; unreadable or invalid ledger data or an unresolvable fallback prints `GATE_CANNOT_RUN` and exits 2.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_dev_refusals_and_ready`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_runner_timeouts_are_typed_and_name_command`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_invalid_timeout_env_is_gate_cannot_run_not_a_traceback`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_command_timeout_defaults_to_180_and_env_overrides_it`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_validate_plan_alone_gets_the_longer_timeout`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_stack_top_reads_the_phase_ledger_and_rejects_invalid_data`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0030: Scripts

**Status:** Draft  
### Requirement Statement

Checks in order: `validate-plan` (`PLAN_INVALID`), in `bd ready` (`NOT_READY`), open and unassigned or self (`UNCLAIMABLE`), `pr_target` (the sprint container's for a poured dev bead) is `--pr-target` or its ancestor (`PR_TARGET_MISMATCH`), `origin/<pr_target>` ancestor of HEAD (`WRONG_BASE`).


### Rationale

The gate order puts the cheapest global refusal first and the base check last, so a dev learns the root cause rather than a downstream symptom; check (4) accepts a `pr_target` that is an ancestor because a quick fix's target is a lower bound.

### Success Criteria

**Acceptance Criteria:**

- [ ] `assignment-gates.py dev` returns `PLAN_INVALID` when `validate-plan --root <root>` exits non-zero, before any other check.
- [ ] It returns `NOT_READY` when `bd ready -n 0 --json` does not list the bead, `UNCLAIMABLE` when the bead is not open or is assigned to someone other than the caller, `PR_TARGET_MISMATCH` when the bead's `pr_target` (the sprint container's for a poured dev bead) is neither `--pr-target` nor its ancestor, and `WRONG_BASE` when `origin/<pr_target>` is not an ancestor of HEAD.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_dev_refusals_and_ready`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_a_poured_dev_bead_takes_its_sprint_containers_pr_target`

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## REQ-DEV-0031: Scripts

**Status:** Draft  
### Requirement Statement

Difficulty models (substring): hard fable/opus/astra; normal terra/opus/sonnet; fast luna/haiku.


### Rationale

User ruling R14 (comment in `plan_contract.py`) fixed which model classes may take a bead of each difficulty; commit c601b20a7 later removed the dev gate's difficulty check so the lead, not a script, decides, and difficulty stays as a minimum tier.

### Success Criteria

**Acceptance Criteria:**

- [ ] `DIFFICULTY_MODELS` in `plugins/atm-bd-orchestration/skills/atm-beads/scripts/plan_contract.py` maps `hard` to `fable`, `opus`, `astra`; `normal` to `terra`, `opus`, `sonnet`; and `fast` to `luna`, `haiku`.
- [ ] A roster model string matches a difficulty when it contains one of that difficulty's names as a substring.

### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

## Unresolved

None.
