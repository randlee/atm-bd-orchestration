---
name: atm-bd-lite
version: 0.19.12
description: One-agent development and QA orchestration for lite-profile phases.
format: markdown
---
# atm-bd-lite

Run a phase with one agent handling development and QA, without a separate review stage.
The phase file opts in explicitly:

```toml
profile = "lite"
```

Use the lite assignment templates from `skills/atm-bd-lite/templates/`. A
template or cron tick must first verify this profile; full phases use
`atm-bd-orchestration`.

## Lead loop

1. Run `bd ready -n 0 --json` and select a ready lite sprint child.
2. Assign development with `dev-template.xml.j2`; assign corrections with
   `fix-assignment.xml.j2`.
3. The dev/fix agent completes the work and invokes the lite task-close hook.
   The hook checks the current stack gate, closes the bead, links the layer,
   assigns QA, and closes the development task.
4. Assign the ready QA task with `qa-template.xml.j2`.
5. QA reports PASS or FAIL through the same hook. PASS closes the sprint work;
   FAIL pours finding groups and notifies the lead.
6. The lead lands completed work from the stack top.

Use `atm-bd cron --phase <phase>` for a deterministic queue tick. It prints
nothing when no action is due and one JSON object when queues or stalled tasks
need attention.

## Close hook

`scripts/atm-bd-task-hook.py` is the pure transition planner. The shared runner
profile-gates the phase before reading close vars or invoking commands:

```sh
atm-bd-task-close --role dev|fix|qa --vars <close-vars.json>
```

Lite close vars use the shared task-close schema and omit full-profile-only fields.
Every command is replay-safe: the runner observes current bead, stack, task,
and PR state and skips already satisfied steps. On failure, repair the named
cause and rerun the exact hook command.

## Errors

| Error | Action |
| --- | --- |
| `PROFILE_MISMATCH` | Use the command matching the phase profile. |
| `CONFIG_INVALID` | Repair the phase or close-vars input, then rerun. |
| `COMMAND_FAILED` / `TIMEOUT` | Repair the named operation and rerun the same hook. |
| Stack gate is not `Stacked` | Rebase the PR onto the current stack top and push it. |
| `NOT_FOUND` | Restore the missing bead, phase file, or configured command. |
