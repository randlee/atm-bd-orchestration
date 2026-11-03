---
name: atm-bd-lite
version: 0.19.12
description: Lightweight ATM Beads profile with task hooks and QA, without a sanity stage.
---

# atm-bd-lite

The lite profile provides the minimal ATM Beads workflow: task assignment, task start, and task close
hooks, followed by QA. It does not add a sanity stage. The profile manifest is `profile.toml`; hook
implementations and their behavior tests are kept under this skill.

Register the three hooks for a phase from the repository root, replacing `<phase>` with the phase name:

```sh
atm hook register task.assign --phase <phase> --cwd . --module .claude/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py
atm hook register task.start --phase <phase> --cwd . --module .claude/skills/atm-bd-lite/scripts/atm-bd-task-start-hook.py
atm hook register task.close --phase <phase> --cwd . --module .claude/skills/atm-bd-lite/scripts/atm-bd-task-hook.py
```

The profile policy routes QA to `quality-mgr` with `templates/qa.xml.j2`.
