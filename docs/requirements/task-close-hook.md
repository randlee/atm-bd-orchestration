# atm-task-close (close hook)

**ID Range:** REQ-TCH-0001 through REQ-TCH-0021  
**Version:** 1.0.0  
**Status:** Approved  
**Created:** 2026-10-19  
**Last Updated:** 2026-11-05  
**Owner:** Rand Lee  

---

## REQ-TCH-0001: Contract

**Status:** Approved  
### Requirement Statement

One script, `atm-task-close.py --role <dev|fix|sanity|qa> --vars <file> [--result <file>]`, is the only way a dev, fix, sanity or QA task completes. The agent never runs `bd close` or `atm task close ... completed` by hand for those roles.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0002: Contract

**Status:** Approved  
### Requirement Statement

For dev and fix, the lead writes an immutable close-dispatch JSON file containing the role's `required_variables_by_role` from `task-close-vars.j2`; this is a separate file from the dev/fix assignment template's render vars. The agent passes it unchanged as `--vars` and supplies a mandatory `--result` JSON file containing only its role's `result_variables_by_role`. The files must not overlap. Matching examples are `examples/task-close-vars-{dev,fix}.json` and `examples/task-close-result-{dev,fix}.json`. The hook derives `commit`, `pr_number`, `pr_url`, `rebased_onto` and `generated_at`; the caller types none of them. Sanity and QA keep a single `--vars` file. The shared header declares exact `render_variables_by_role` sets (required plus result); the hook strictly renders only those actual fields, with no other-role placeholders. Missing or unknown fields fail before live checks; non-empty derived identity is checked after derivation and before writes.
   The lead supplies `stack_bead`, the stack ledger bead ID, in the vars file.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0003: Contract

**Status:** Approved  
### Requirement Statement

The result is JSON on stdout and stderr, `{"ok": {...}}` or `{"err": {"code", "message", "fix"}}`, and the exit code mirrors it. Every `err` names the exact fix; there is no separate ledger.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0004: Contract

**Status:** Approved  
### Requirement Statement

Commands that need the lead's authority (`atm task assign`) run with `ATM_IDENTITY=<lead>` and `ATM_TEAM=<team>` set on that one subprocess, `lead` from `.atm-bd/phase-<x>.toml` and the team from `.atm.toml`. Every other `bd` and `atm` write runs as the caller: `bd` writes carry `--actor "$ATM_IDENTITY"`, and `atm` writes take `ATM_IDENTITY` from the environment.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0005: Contract

**Status:** Approved  
### Requirement Statement

`--skip-checks` skips the PR and stack checks only, never vars validation, derived identity validation or state writes. It appears only in `--help`: "skips the PR and stack checks. Do NOT use without permission from the phase lead." No template names it. Dev/fix still derive a non-empty HEAD and require non-empty `pr_number` and `pr_url` recorded on the checked bead before writing; an empty identity is `VARS.EMPTY` with remediation.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0006: Contract

**Status:** Approved  
### Requirement Statement

GitHub unreachable or rate limited falls back to local git (the pushed head is on `origin/<branch>`, `origin/<current stack top>` is an ancestor of it (or `origin/<pr_target>` when the ledger is empty)). The hook uses the checked bead's recorded PR identity, records `github: unavailable`, and sanity and QA proceed only when that identity is non-empty. Missing recorded PR number or URL is `VARS.EMPTY` before any write, naming the required repair. The lead owns stack hygiene.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0007: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Approved  
### Requirement Statement

Checks, in order: merge and strictly validate dispatch/result vars (2); derive non-empty HEAD and the UTC generation time; the worktree is clean and HEAD is the pushed head on `origin/<branch>`; the current top from the stack bead's `layers` (its `pr_target` when the ledger is empty) is an ancestor of HEAD, read locally, deriving `rebased_onto`; exactly one open PR exists for `branch` with HEAD as its head (when GitHub is reachable), deriving its number and URL. No match is `PR.NOT_FOUND`; multiple matches are `PR.AMBIGUOUS`, never arbitrary selection. The PR base is retargeted by linking, so the hook does not check it. Finally require non-empty commit, PR number and URL before any bd/atm write, including permitted skipped-check and offline paths. Nothing else: not the whole stack, not lint or tests (the dev ran the gates before calling; sanity runs lint). The dev rebases onto the current top before every hook run, after a sanity FAIL or a rebase-required too. Result evidence records `ledger_top` and `pr_base` separately and reports differing branches; an empty ledger has no difference. Replay compares only the current assignment.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0008: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Approved  
### Requirement Statement

On pass, create ephemeral completion vars from dispatch plus result plus derived fields: `bd update <bead> --metadata '<full metadata JSON>'`, then `bd close <bead> --reason "dev complete at <sha>"` (`fixed at <sha>` for a fix). When a sanity assignment is due and none is already open, send the dev-complete or fix-complete report to the lead by plain `atm send --template` (not a task close) before `atm task assign <sanity member> --task-id <sanity bead> --template dev-sanity-template.xml.j2 --vars <completion file>` as the lead (4). `atm task assign` consumes `--vars` synchronously at assignment time; the file is not a path for the recipient to reopen. Delete the temporary completion files when the hook returns; persist nothing and never rewrite either input file. Report delivery is at least once: a retry after interruption before the assignment is recorded can send the report again. The hook then closes the dev's ATM task (21).

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0009: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Approved  
### Requirement Statement

The sanity bead is the group's: `metadata.sanity_bead` on the checked bead when present, else the open `stage:dev-sanity` bead whose `metadata.dev_bead` is the checked bead. None: `err` naming the lead, who creates it (team-lead 16).

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0010: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Approved  
### Requirement Statement

`not_reproducible` (fix only): the PR and head checks are skipped (nothing is pushed); the close reason is `not reproducible: <file:line>`; the hook sends the report before assigning sanity as in item 8, using the checked bead's branch and worktree and the checked worktree's HEAD for the sanity assignment. Sanity verifies the one deliverable, the absence at the cited line; QA's filing reviewer confirms it. No special close, no special assignment.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0011: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Approved  
### Requirement Statement

Refused and cancelled closes do not go through the hook: `atm task close <id> refused --template task-refused.md.j2` as before (dev 5 and 16).

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0012: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Approved  
### Requirement Statement

After a pass the dev's task is closed and the dev starts its next queued task. A sanity FAIL re-assigns the same task id using the phase dev or fix assignment template; a rebase-required message means another layer took the top first: rebase onto the new top, push, run the hook again; `sanity_round` does not move.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0013: Role sanity (`--role sanity`)

**Status:** Approved  
### Requirement Statement

Sanity input is generated mechanically by sanity-close-vars from the split manifest, selected-vars.json and an optional stack result. It carries the selected verdict, pinned sha, checked bead, QA identity and selected undone deliverables with verbatim reasons. A PASS close does not require linking or a stack result: it closes first, then hands off to sanity-stack. A not_reproducible fix skips linking.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0014: Role sanity (`--role sanity`)

**Status:** Approved  
### Requirement Statement

PASS: `bd close <sanity bead> --reason "PASS at <sha>"`; the dev's task is already closed (21) and the dev-complete report was sent by the dev's hook; `atm task close <sanity bead> completed --template dev-sanity-complete.md.j2`; `atm task assign <qa member> --task-id <qa bead> --template qa-template.xml.j2 --vars <file>` as the lead, with `base` = the PR base, `commit`, `round`, and for a fix bead `carry_forward` = the fix bead.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0015: Role sanity (`--role sanity`)

**Status:** Approved  
### Requirement Statement

FAIL below the cap: append `sanity FAIL round <n> at <sha>:` and one numbered line per undone deliverable with the reviewer’s verbatim reason to the checked bead notes; reopen the checked bead retaining its assignee; set the sanity bead open and unassigned. Once those writes are applied, assign the checked bead’s same ATM task id to its developer using the phase dev or fix template and vars rebuilt from bead metadata and repository configuration. Close the sanity task. A pending journal write refuses with `BEADS.WRITE_PENDING` and a retry instruction; retry emits the assignment after writes apply. Re-closing the dev at a new sha assigns sanity again.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0016: Role sanity (`--role sanity`)

**Status:** Approved  
### Requirement Statement

FAIL exceeding the cap: `max_sanity_rounds` from the repo config (`.claude/project/atm-bd-orchestration.yaml`, rendered from `registry.yaml`), default 5. The hook reopens nothing: it sends the lead `SANITY.ROUND_CAP` with the undone deliverable numbers and closes the sanity task (FAIL). The dev's task stays closed until the lead rules.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0017: Role sanity (`--role sanity`)

**Status:** Approved  
### Requirement Statement

CANNOT_RUN: as today (dev-sanity 31): bead open, no assignee, task `refused`; the dev's task is already closed.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0018: Role qa (`--role qa`)

**Status:** Approved  
### Requirement Statement

Input: the verdict, the sha, the round, the pours made. The hook closes the QA bead and task together (`bd close` first) with `qa-complete.md.j2` and sends the lead a status message, PASS or FAIL alike. It assigns nothing: quality-mgr has already poured the fix groups, and fix dispatch is the lead's judgment.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0019: Lead and console

**Status:** Approved  
### Requirement Statement

Sanity and QA assignment are mechanical and belong to the hook. The fallback for a sanity or QA bead that `bd ready` lists with no ATM task (a hook that died between its commands) is the console or the lead assigning it as the lead; the console checks `atm task list` before assigning, and a second assign of the same id is an in-place update, never a second task.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0020: Lead and console

**Status:** Approved  
### Requirement Statement

The lead does not link layers: after the PASS close hook succeeds, the sanity side links under the stack bead lock ([sanity-stack.md](sanity-stack.md)). The lead creates the stack bead with the integration branch, claims it before its own unstack, restack and land, and owns stack hygiene and every `stack_failed`. A sanity FAIL or rebase-required is fixed on the same unlinked branch.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-TCH-0021: Lead and console

**Status:** Approved  
### Requirement Statement

Dev and fix assignment stay with the lead: the hook closes the dev's own task (as the caller) at dev complete, after assigning sanity, so the dev starts its next queued task at once; a sanity FAIL re-assigns the same task id; fix beads from QA go to the dev the lead picks at the finding's difficulty.

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

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## Command timeouts, retries and diagnostics

Each `bd`, `git` and `gh` call is bounded by `COMMAND_TIMEOUT` seconds (default 180, overridable with the `ATM_BD_GATE_TIMEOUT_S` environment variable). A call that times out is not retried: it fails the close with `COMMAND.FAILED` after one `COMMAND_TIMEOUT`. A `bd` call that fails with a dropped Dolt connection (output matching `invalid connection` or `i/o timeout`, seen at host load 40-55) is retried `DOLT_RETRIES = 3` times, sleeping `DOLT_RETRY_SLEEP_S = 10` seconds between attempts.

Worst case for one `bd` call that keeps dropping: `(3 + 1) x COMMAND_TIMEOUT + 3 x 10`. That is 750s at the default 180s timeout. A close makes several `bd` calls, so a fully starved close can wait that long per call. A close that times out waits one `COMMAND_TIMEOUT` (180s by default) before failing.

The hook records every attempt that was not a clean first-try success, and a success that needed a retry, under `attempts` in its JSON output: `command`, `attempt`, `timeout_s`, `elapsed_s`, `outcome` (`ok`, `dolt_drop_retry`, `failed`, `timeout`, `error`), `retries_until_now`, `total_elapsed_s`, `load_avg` (1, 5 and 15 minute `os.getloadavg`) and `cpu_pct` (1 minute load as a percentage of CPU count; `null` where `os.getloadavg` is unavailable).
