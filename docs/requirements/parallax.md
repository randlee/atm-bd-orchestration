# parallax

Sources: `plugins/atm-bd-orchestration/`: `agents/parallax.md`, `skills/atm-bd-orchestration/SKILL.md` (Roles, Lead Role).

## Requirements

1. Optional: the lead may run a phase with a work-orchestrator teammate (`agents/parallax.md`); without one nothing changes.
2. The work-orchestrator runs the lead's routine steps exactly as `atm-bd-orchestration/SKILL.md` writes them: Loop, Dispatch, Sync, stack landing.
3. It uses the same templates, formulas and scripts as the lead; no parallax-only copy or branch exists.
4. It assigns the tasks it dispatches, so their closes return to it.
5. The lead keeps `bv`, monitoring, every ruling and every escalation to the user.
6. A judgement the skill leaves to the lead goes to the lead; the work-orchestrator keeps dispatching every other ready bead meanwhile.
7. It sends the lead only summaries and escalations, one message each: `work-orchestrator: <SUMMARY|ESCALATION|HANDOVER>`, `beads`, `evidence`, `need`; never task traffic.
8. When the lead takes the work back, it sends `HANDOVER` with the open task ids, open PRs and the stack number.
9. It may write the stack in the lead's place (`gh stack link`, `unstack`, `sync`, `rebase`, `merge`).

## Unresolved

1. `agents/dev-sanity.md` sends the Jev startup probe report to `<lead>` (`jev_client.py --startup --lead <lead>`); it runs at session start, outside any task, so it has no task assigner.
2. Only the original assigner can re-dispatch a closed task id (SKILL "ATM Limits Today"); after a handover the outgoing work-orchestrator must re-dispatch its own closed tasks.
