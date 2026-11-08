# parallax

**ID Range:** REQ-PLX-0001 through REQ-PLX-0008  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-04  
**Last Updated:** 2026-10-04  
**Owner:** Rand Lee  

---

## REQ-PLX-0001: parallax

**Status:** Draft  
### Requirement Statement

Optional: the lead may run a phase with a work-orchestrator teammate (`agents/parallax.md`); without one nothing changes.


### Rationale

Rand ruled that parallax is a named teammate running the lead's routine orchestration so the lead keeps `bv`, monitoring and rulings (commit 4a8b1dc80; CHANGELOG, Optional parallax mode). It is optional and adds a role, not a second workflow.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/agents/parallax.md` exists, with front matter `metadata.spawn_policy: named_teammate_required`.
- [ ] The Roles table in `skills/atm-bd-orchestration/SKILL.md` lists `parallax` as `optional work-orchestrator`.
- [ ] `skills/atm-bd-orchestration/SKILL.md` and its templates contain no step that requires a parallax teammate to be present.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0002: parallax

**Status:** Draft  
### Requirement Statement

The work-orchestrator runs the lead's routine steps exactly as `atm-bd-orchestration/SKILL.md` writes them: Loop, Dispatch, Sync, stack landing.


### Rationale

Commit 4a8b1dc80 records Rand's ruling that parallax "is not a second workflow": the earlier wave docs, wave loop and wave-monitor were removed, and it runs the lead's routine steps under the same skill.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/parallax.md` instructs the agent to run the lead's orchestration under `.claude/skills/atm-bd-orchestration/SKILL.md` "exactly as written there".
- [ ] `agents/parallax.md` names the Loop, Dispatch, Sync and stack landing as the steps it runs.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0003: parallax

**Status:** Draft  
### Requirement Statement

It uses the same templates, formulas and scripts as the lead; no parallax-only copy or branch exists.


### Rationale

Commit 4a8b1dc80 removed the wave docs and wave loop so parallax is not a second workflow, and the CHANGELOG entry states "No formula or script changes".

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/parallax.md` defines no template, formula or script of its own and refers only to the shared skill.
- [ ] No file in the package carries a parallax-specific copy or branch of a dispatch template, formula or script (`grep -ril parallax` finds only the agent, SKILL.md, README, CHANGELOG, manifest and one test list).

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0004: parallax

**Status:** Draft  
### Requirement Statement

It assigns the tasks it dispatches, so their closes return to it.


### Rationale

Routing needs no variable: `atm task close` returns to whoever assigned the task, so commit 4a8b1dc80 dropped `lead` and `cc` from the templates and review round 1 (2e437acbd) made the recipient "the task assigner". A parallax that assigns its own tasks therefore receives their closes, and the lead does not.

### Success Criteria

**Acceptance Criteria:**

- [ ] `SKILL.md` Lead Role states that a close returns to the task's assigner.
- [ ] A task assigned by the work-orchestrator with `atm task assign` shows the work-orchestrator as `assigner` in `atm task events <task-id>`.
- [ ] No dispatch template names `lead`, `team-lead` or a fixed recipient for the close.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0005: parallax

**Status:** Draft  
### Requirement Statement

The lead keeps `bv`, monitoring, rulings, `ROUND_CAP`, overruling a ceremony closure, gates, phase closure and the merge to the base branch, and escalations to the user; everything else is the work-orchestrator's, and it keeps dispatching every other ready bead meanwhile.


### Rationale

The lead needs bv, monitoring, rulings and the merge to stay with it, while the routine work moves off its plate; commit 4a8b1dc80 states this split, and review round 1 added that parallax keeps dispatching other ready beads meanwhile.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/parallax.md` lists `bv`, monitoring, rulings, `ROUND_CAP`, overruling a ceremony closure, gates, phase closure, the merge to the base branch and escalations to the user as kept by the lead.
- [ ] `agents/parallax.md` says everything else is the work-orchestrator's and to keep dispatching every other ready bead meanwhile.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0006: parallax

**Status:** Draft  
### Requirement Statement

For anything the lead keeps, or where the skill says report to the user, it sends the lead an `ESCALATION`.


### Rationale

The lead keeps rulings and user escalations, so parallax needs one defined way to hand those up; the CHANGELOG workflow-gaps entry lists "parallax escalates anything the lead keeps" (`parallax` 0.1.1).

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/parallax.md` instructs the agent to send the lead an `ESCALATION` for anything the lead keeps.
- [ ] `agents/parallax.md` instructs the agent to send the lead an `ESCALATION` where the skill says report to the user.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0007: parallax

**Status:** Draft  
### Requirement Statement

It sends the lead only summaries and escalations, one message each: `work-orchestrator: <SUMMARY|ESCALATION|HANDOVER>`, `beads`, `evidence`, `need`; never task traffic; a `SUMMARY` on the lead's request.


### Rationale

The lead is to be freed from reading task traffic, so commit 4a8b1dc80 limits parallax's messages to summaries and escalations in one fixed shape.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/parallax.md` contains a fenced message template whose first line is `work-orchestrator: <SUMMARY|ESCALATION|HANDOVER>`, followed by `beads:`, `evidence:` and `need:` lines.
- [ ] `agents/parallax.md` says to send one message per summary or escalation, never task traffic, and a `SUMMARY` on the lead's request.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## REQ-PLX-0008: parallax

**Status:** Draft  
### Requirement Statement

Handover and the stack writer: `SKILL.md` Lead Role.


### Rationale

Handover and the single stack writer are specified once in `SKILL.md` Lead Role; review round 1 made parallax point there and the skill require one stack writer at a time rather than restating it.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/parallax.md` refers to the `SKILL.md` Lead Role section for handover and the stack writer.
- [ ] `SKILL.md` Lead Role states that the lead or its work-orchestrator is the only stack writer, one at a time.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## Unresolved

None. The Jev startup probe failure, which runs outside any task, goes to the ATM escalation recipients (`SKILL.md` Lead Role), else the lead.
