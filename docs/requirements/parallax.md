# parallax

**ID Range:** REQ-PLX-0001 through REQ-PLX-0008  
**Version:** 1.0.0  
**Status:** Approved  
**Created:** 2026-10-04  
**Last Updated:** 2026-10-04  
**Owner:** Rand Lee  

---

## REQ-PLX-0001: parallax

**Status:** Approved  
### Requirement Statement

Optional: the lead may run a phase with a work-orchestrator teammate (`agents/parallax.md`); without one nothing changes.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0002: parallax

**Status:** Approved  
### Requirement Statement

The work-orchestrator runs the lead's routine steps exactly as `atm-bd-orchestration/SKILL.md` writes them: Loop, Dispatch, Sync, stack landing.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0003: parallax

**Status:** Approved  
### Requirement Statement

It uses the same templates, formulas and scripts as the lead; no parallax-only copy or branch exists.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0004: parallax

**Status:** Approved  
### Requirement Statement

It assigns the tasks it dispatches, so their closes return to it.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0005: parallax

**Status:** Approved  
### Requirement Statement

The lead keeps `bv`, monitoring, rulings, `ROUND_CAP`, overruling a ceremony closure, gates, phase closure and the merge to the base branch, and escalations to the user; everything else is the work-orchestrator's, and it keeps dispatching every other ready bead meanwhile.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0006: parallax

**Status:** Approved  
### Requirement Statement

For anything the lead keeps, or where the skill says report to the user, it sends the lead an `ESCALATION`.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0007: parallax

**Status:** Approved  
### Requirement Statement

It sends the lead only summaries and escalations, one message each: `work-orchestrator: <SUMMARY|ESCALATION|HANDOVER>`, `beads`, `evidence`, `need`; never task traffic; a `SUMMARY` on the lead's request.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLX-0008: parallax

**Status:** Approved  
### Requirement Statement

Handover and the stack writer: `SKILL.md` Lead Role.

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

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

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

None. The Jev startup probe failure, which runs outside any task, goes to the ATM escalation recipients (`SKILL.md` Lead Role), else the lead.
