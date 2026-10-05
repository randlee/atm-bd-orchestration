# parallax

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## Requirements

1. Optional: the lead may run a phase with a work-orchestrator teammate (`agents/parallax.md`); without one nothing changes.
2. The work-orchestrator runs the lead's routine steps exactly as `atm-bd-orchestration/SKILL.md` writes them: Loop, Dispatch, Sync, stack landing.
3. It uses the same templates, formulas and scripts as the lead; no parallax-only copy or branch exists.
4. It assigns the tasks it dispatches, so their closes return to it.
5. The lead keeps `bv`, monitoring, rulings, `ROUND_CAP`, overruling a ceremony closure, gates, phase closure and the merge to the base branch, and escalations to the user; everything else is the work-orchestrator's, and it keeps dispatching every other ready bead meanwhile.
6. For anything the lead keeps, or where the skill says report to the user, it sends the lead an `ESCALATION`.
7. It sends the lead only summaries and escalations, one message each: `work-orchestrator: <SUMMARY|ESCALATION|HANDOVER>`, `beads`, `evidence`, `need`; never task traffic; a `SUMMARY` on the lead's request.
8. Handover and the stack writer: `SKILL.md` Lead Role.

## Unresolved

None. The Jev startup probe failure, which runs outside any task, goes to the ATM escalation recipients (`SKILL.md` Lead Role), else the lead.
