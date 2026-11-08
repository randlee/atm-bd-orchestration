# dev

**ID Range:** REQ-DEV-0001 through REQ-DEV-0031  
**Version:** 1.0.0  
**Status:** Approved  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-20  
**Owner:** Rand Lee  

---

## REQ-DEV-0001: All assignments

**Status:** Approved  
### Requirement Statement

The task id is the bead id; `bd show <bead>` is the assignment; the bead wins over the template and the mismatch is reported.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0002: All assignments

**Status:** Approved  
### Requirement Statement

Start a task only after the previous one is closed; after each close read ATM, and only then does the next task start.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0003: All assignments

**Status:** Approved  
### Requirement Statement

Work only on the assigned branch and worktree. Never run `gh stack link/sync/rebase/merge` or `bd sync` (the lead is the stack writer and owns sync); `--actor "$ATM_IDENTITY"` on every `bd` write.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0004: All assignments

**Status:** Approved  
### Requirement Statement

Before claiming: dev rebases onto `origin/<pr_target>` (a conflict is part of the work); dev-fix and fix only fetch (their branch was cut from the stack top). Then run `assignment-gates.py dev`; `READY`: `bd update <bead> --claim`, then `atm task start <bead> "<one line>"`.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0005: All assignments

**Status:** Approved  
### Requirement Statement

`NOT_READY`: do not claim or start; find the blockers; close the task `refused` (`bead_state` open), `reason_md` = bead, cause, who must move and the dependency to add (`bd dep add <bead> --blocked-by <blocker>`). A blocker met mid-task (work another bead or agent owns that is not done; a shared change you can make yourself is a quick fix, 26, and the task continues): return the bead open, unassigned, blocker in notes, close the task `refused` the same way. Never wait.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0006: All assignments

**Status:** Approved  
### Requirement Statement

Any other gate code: close the task `refused` with the code, command and failure evidence in `reason_md`; leave the bead unchanged when the gate fails before claim.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0007: All assignments

**Status:** Approved  
### Requirement Statement

Commit as items land and push early; a push or `atm send` closes nothing.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0008: All assignments

**Status:** Approved  
### Requirement Statement

Never weaken a test, skip a criterion, or leave a placeholder; run `<test_command>` and `<lint_command>` (dev and dev-fix: also the bead's validation commands) to zero failures, including lint failures inherited from a lower layer.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0009: All assignments

**Status:** Approved  
### Requirement Statement

Before closing, the dev rebases onto the stack's current top (`assignment-gates.py stack-top --root <phase-root> --pr-target <pr_target> --worktree <worktree>`; any other exit is a code to refuse with, never a guess), re-runs the tests, force-pushes and opens the PR against that top (never draft; a quick-fix finding fixed on a branch that already has its PR keeps that PR), then runs `/sc-gh-stack-view`.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0010: All assignments

**Status:** Approved  
### Requirement Statement

Close bead and task together with the close template, `bd close` first and the task only if it succeeded; the close carries the pushed head, the top rebased onto, the PR and the verbatim `/sc-gh-stack-view` output. The task close is the report; it returns to the task assigner.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0011: Dev (`dev-template`)

**Status:** Approved  
### Requirement Statement

Read the bead: scope, deliverables, deletion targets, validation, acceptance criteria; `metadata.owned_paths` is the fence; a field the poured dev bead lacks comes from its sprint container.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0012: Dev (`dev-template`)

**Status:** Approved  
### Requirement Statement

Read every `metadata.requirements` and `metadata.adrs` id; satisfy each; `NONE` but the work touches one: tell the task assigner before coding past it.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0013: Dev (`dev-template`)

**Status:** Approved  
### Requirement Statement

Read `policy_path` and every guideline it names for the languages touched.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0014: Dev (`dev-template`)

**Status:** Approved  
### Requirement Statement

Read the complete plan and enumerate all tasks that must be completed in the primary and any child beads; create an itemized private checklist outside the tracked tree with every task identified; work through the checklist one item at a time; then go through it again one item at a time and confirm each is fully met; nothing outside the bead's scope.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0015: Dev (`dev-template`)

**Status:** Approved  
### Requirement Statement

Close: `bd close --reason "dev complete at <short sha>"` + `dev-complete.md.j2` with the deliverable inventory and gate output; deletion work adds a before/after inventory.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0016: Dev (`dev-template`)

**Status:** Approved  
### Requirement Statement

Cannot complete: include the reason, command and failure evidence in the task refusal's `reason_md`; `bd update --status blocked --assignee "" --append-notes "DEV_CANNOT_COMPLETE; ..."`; never `bd close` (it would release the sanity check); task `refused`. Unfinished is a failure.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0017: Dev-fix (`dev-fix`)

**Status:** Approved  
### Requirement Statement

Not ready while `closed` means never reopened. The fixes go on the assigned new layer cut from the stack's top; the sprint's first layer (`pr_target`) and any fix layer above it are frozen: never rebase, re-target or push them.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0018: Dev-fix (`dev-fix`)

**Status:** Approved  
### Requirement Statement

Read the complete plan and enumerate all tasks that must be completed in the primary and any child beads (`bd list --parent <bead> --status open --json`); create an itemized private checklist outside the tracked tree with every task identified; work through the checklist one item at a time, closing each child when fixed; then go through it again one item at a time and confirm each is done.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0019: Dev-fix (`dev-fix`)

**Status:** Approved  
### Requirement Statement

Re-check the whole bead; re-read its requirements and ADRs.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0020: Dev-fix (`dev-fix`)

**Status:** Approved  
### Requirement Statement

Close and cannot-complete as Dev 15 and 16, the deliverables listing each finding and its fix.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0021: Fix (`fix-assignment`)

**Status:** Approved  
### Requirement Statement

Read the bead, its `metadata.sprint_bead`, and the finding's requirements and ADRs; read `policy_path` and its guidelines.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0022: Fix (`fix-assignment`)

**Status:** Approved  
### Requirement Statement

Confirm the defect at the cited file:line; absent: no work, close `not_reproducible` with the file:line checked.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0023: Fix (`fix-assignment`)

**Status:** Approved  
### Requirement Statement

Fix every in-scope occurrence of the pattern; touch only what the remedy needs.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0024: Fix (`fix-assignment`)

**Status:** Approved  
### Requirement Statement

Close: `bd close --reason "fixed at <short sha>"` (or `"not reproducible: <file:line>"`) + `fix-complete.md.j2`, outcome `fixed` (with commit and PR) or `not_reproducible` (none).

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0025: Fix (`fix-assignment`)

**Status:** Approved  
### Requirement Statement

Cannot fix: include the reason, command and failure evidence in the task refusal's `reason_md`; return the bead open, unassigned, `FIX_CANNOT_COMPLETE` in notes; task `refused`. Never close a finding unfixed.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0026: Parallel quick fix (finder)

**Status:** Approved  
### Requirement Statement

A change other live branches need never goes in your layer: stop and tell the task assigner the change and the branches it breaks.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0027: Parallel quick fix (finder)

**Status:** Approved  
### Requirement Statement

The lead picks the quick fix's `pr_target` (a lower bound); the finder cuts `fix/<thing>` from the stack's current top (`stack-top --root <phase-root> --pr-target <pr_target> --worktree <worktree>`) in its own worktree: only the change, compiler-forced implementors/call sites, one test for a bug; test passes; push; PR against that top as a new layer, never into a lower layer or the integration branch; report the PR by plain `atm send`.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0028: Parallel quick fix (finder)

**Status:** Approved  
### Requirement Statement

Sprint task stays open; continue on the rebased layer.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0029: Scripts

**Status:** Approved  
### Requirement Statement

`assignment-gates.py dev` prints one code; exit 0 `READY`, 2 `GATE_CANNOT_RUN`, 5 otherwise. Every command the gates run is bounded by `ATM_BD_GATE_TIMEOUT_S` seconds (default 180; validate-plan at least 300); a timeout is `GATE_CANNOT_RUN` whose stderr names the command and the fix (retry once, or raise `ATM_BD_GATE_TIMEOUT_S` on a loaded host). A value that is not a positive integer is also `GATE_CANNOT_RUN` whose stderr names the value and the fix. `stack-top --root <phase-root> --pr-target <b> --worktree <worktree>` prints the last layer's branch from `<phase-root>.stack` on exit 0. With no layers it resolves `origin/<b>` and prints `<b>`; unreadable or invalid ledger data or an unresolvable fallback returns `GATE_CANNOT_RUN` (2).

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0030: Scripts

**Status:** Approved  
### Requirement Statement

Checks in order: `validate-plan` (`PLAN_INVALID`), in `bd ready` (`NOT_READY`), open and unassigned or self (`UNCLAIMABLE`), `pr_target` (the sprint container's for a poured dev bead) is `--pr-target` or its ancestor (`PR_TARGET_MISMATCH`), `origin/<pr_target>` ancestor of HEAD (`WRONG_BASE`).

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-DEV-0031: Scripts

**Status:** Approved  
### Requirement Statement

Difficulty models (substring): hard fable/opus/astra; normal terra/opus/sonnet; fast luna/haiku.

**MUST statements:**

**SHOULD statements:**

**MUST NOT statements:**


### Rationale




### Success Criteria



**Acceptance Criteria:**

**Test Evidence:**


### Dependencies



**Requires:**

**Related:**


### Product Applicability



**Applies To:**

**Does Not Apply To:**


### Implementation Notes

Package sources: `atm-bd-orchestration` templates `dev-template`, `dev-fix`, `fix-assignment`, `dev-complete`, `fix-complete`, `task-refused`; `scripts/assignment-gates.py`; `SKILL.md`; `atm-beads/scripts/validate-plan`, `plan_contract.py`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## Unresolved

None.
