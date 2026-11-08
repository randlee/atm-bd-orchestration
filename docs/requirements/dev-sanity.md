# dev-sanity

**ID Range:** REQ-DSAN-0001 through REQ-DSAN-0061  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-24  
**Owner:** Rand Lee  

---

## REQ-DSAN-0001: Role

**Status:** Draft  
### Requirement Statement

Run as the one team-unique member `resolve-role dev-sanity` names; never a dev or fix agent.


### Rationale

dev-sanity is a named teammate resolved from `roles.dev-sanity`, and the installer adds that member to the team separately from the dev roster (CHANGELOG: the installer adds the dev-sanity member, whose host name must be unique). Keeping the role distinct from dev and fix keeps the checker independent of the work it checks.

### Success Criteria

**Acceptance Criteria:**

- [ ] `plugins/atm-bd-orchestration/agents/dev-sanity.md` frontmatter has `spawn_policy: named_teammate_required` and its body opens "You are the team's dev-sanity member selected by roles.dev-sanity"
- [ ] The member named by `resolve-role dev-sanity` is not the assignee of any dev or fix task in `atm task list --all`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0002: Role

**Status:** Draft  
### Requirement Statement

Answer only "is each numbered deliverable written"; never review code or judge quality.


### Rationale

The dev-sanity prompt and task template both define the check as presence of each numbered deliverable ("This is not QA"), because QA owns quality; the bk-phase confusion of sanity with QA is recorded in this document (REQ-DSAN-0058).

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/dev-sanity.md` states that it judges only whether each numbered deliverable is written, never code quality
- [ ] A reviewer finding of any kind other than `skipped` is rejected by `sanity-merge` with a non-zero exit

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_rejects_multiple_or_non_skipped_findings`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0003: Role

**Status:** Draft  
### Requirement Statement

Own the verdict: the selected result alone sets PASS/FAIL; a FAIL is handed back by the close hook, not as finding children.


### Rationale

The close hook, not the agent, reopens the dev bead and sends `sanity-fail`; finding beads were retired (CHANGELOG: `dev-sanity-complete.md.j2` drops `finding_bead_ids` and states that no finding beads are filed). The merge script sets the verdict so an agent cannot talk a failure into a pass.

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-merge` prints a `PASS` verdict only when no deliverable has a finding and lint exits 0, and `FAIL` when a `skipped` finding exists
- [ ] After a FAIL close, the dev bead is `open`, the dev is assigned a task carrying the `sanity-fail` template, and no finding bead exists
- [ ] The rendered `dev-sanity-complete.md.j2` for a FAIL says "no finding beads were filed"

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_pass`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_fail_from_skipped_finding`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_task_close_hook.py::test_fail_reopens_dev_leaves_sanity_blocked_and_notifies_dev_before_close`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::TemplateContractTests::test_sanity_fail_report_explains_handoff_without_finding_beads`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0004: Role

**Status:** Draft  
### Requirement Statement

Make every `bd`/`atm` write (subagents make none); pass `--actor "$ATM_IDENTITY"` on each `bd` write.


### Rationale

The coordinator holds all bead and task writes so the parallel reviewers cannot race them; the reviewer prompts forbid `bd` and `atm`, and the task template claims with `bd update ... --claim --actor "$ATM_IDENTITY"` so writes are attributable.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/sc-sanity-llm.md` and `agents/sc-sanity-jev.md` each forbid running `bd` or `atm`
- [ ] Every `bd` write command in `templates/dev-sanity-template.xml.j2` includes `--actor "$ATM_IDENTITY"`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0005: Role

**Status:** Draft  
### Requirement Statement

Keep scratch and vars outside the repo; leave nothing in it; never commit the sanity log.


### Rationale

A dirty worktree makes `sanity-split` refuse with COMMIT_MISMATCH (CHANGELOG: sc-obs wrote an untracked checklist into a sprint worktree and dev-sanity refused it), so scratch must live elsewhere and the repo stays clean.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/dev-sanity.md` says to keep scratch outside the repository
- [ ] After a sanity run, `git status --porcelain` in the checked worktree lists no path created by dev-sanity
- [ ] `git ls-files` in the repository lists no sanity ledger file

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_commit_mismatch`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0006: Role

**Status:** Draft  
### Requirement Statement

Never edit code, commit or push; after the PASS close hook succeeds, hand the generated stack input to sanity-stack, which links under the stack bead lock (28).


### Rationale

Sanity runs after the dev's work is frozen and must not alter it; the stack link is a separate agent step after the close succeeds (CHANGELOG: sanity closes on its selected verdict before handing off stacking, #498).

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/dev-sanity.md` says it never edits code, commits or pushes
- [ ] In `agents/dev-sanity.md` the `atm task close` instruction comes before "Only after successful PASS close", which hands `stack-input.json` to sanity-stack
- [ ] `sanity-stack-link` outputs a result and sends no `atm task` write

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_agent_prompts.py::test_sanity_prompts_close_before_ordered_stack_handoff`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failed_post_close_handoff_notifies_lead_without_task_writes`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0007: Startup and Jev outages

**Status:** Draft  
### Requirement Statement

At session start and on credential change, run the Jev startup probe (`jev_client.py --startup`).


### Rationale

Jev outages need to be detected before a task is lost to them; `jev_client.py --startup` exits 2 on failure and dev-sanity runs it at session start and credential change (CHANGELOG: Jev startup and child-error announcements).

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/dev-sanity.md` says to run the Jev startup probe at session start and at credential change
- [ ] `jev_client.py --startup` exits 2 and prints an error with `code`, `message`, `recoverable` and `suggested_action` when the probe fails

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_startup_announcement_uses_configured_phase_recipients_despite_conflicting_environment`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0008: Startup and Jev outages

**Status:** Draft  
### Requirement Statement

Probe exit 2, or a JEV child failing with `SANITY.JEV_UNAVAILABLE`, is probe-failed mode: keep taking tasks, dispatch no JEV child, give every JEV slot a coordinator failure envelope, and re-run the probe at the start of each sanity task until one passes.


### Rationale

A Jev outage must not stop sanity work: the CHANGELOG records that dev-sanity enters probe-failed mode on probe exit 2 or a JEV child `SANITY.JEV_UNAVAILABLE` and re-probes at each task, and that the probe-failed slot carries the probe's own code and message.

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/dev-sanity.md` states that a failed probe or `SANITY.JEV_UNAVAILABLE` keeps Jev slots unavailable with their exact error and that the probe is retried at the start of the next task
- [ ] With the probe failed, the Jev slot of each deliverable in `sanity-merge` input holds a failure envelope whose code and message equal the probe's

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0009: Startup and Jev outages

**Status:** Draft  
### Requirement Statement

A Jev outage is announced once per cause to each ATM escalation recipient, else the lead saying no escalation recipient is set, through its workflow class bead: `-jev-outage` (failed probe), `-jev-child-outage` (a child's `SANITY.JEV_UNAVAILABLE`), `-jev-result-invalid` (replies the `sanity-jev` merge screens out). Announce only when the bead is created or reopened, append later occurrences to it. `-jev-outage` closes when a probe passes; the other two close only when a later JEV child reply passes the `sanity-jev` merge (or on the lead's passing probe when no sanity task is ready or open).


### Rationale

Serious failures are announced once per cause through a workflow class bead (CHANGELOG: announce on create, append later uses, close when it clears), and a child's Jev failure closes the class bead only on a passing Jev child (commit 1b5a03091), so repeated outages do not spam the recipients.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each of `-jev-outage`, `-jev-child-outage` and `-jev-result-invalid` is created as a workflow class bead, announced only on create or reopen, with later occurrences appended to its notes
- [ ] `-jev-outage` is closed after a passing probe, and the other two only after a later Jev child reply passes the `sanity-jev` merge

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_error_announces_a_child_failure_verbatim_without_probing`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_announcement_falls_back_to_phase_lead_with_no_recipient_note`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0010: Startup and Jev outages

**Status:** Draft  
### Requirement Statement

Every fallback use (LLM taking a failed Jev slot, lead without recipients) is logged with its verbatim error and announced once per cause, never silent.


### Rationale

Fallbacks hide outages when silent; the CHANGELOG (stack #66 review fixes) requires every fallback use to be logged with its verbatim error, and the sanity run history keeps the Jev error while the LLM reply is selected.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each fallback use (LLM taking a failed Jev slot, lead used for lack of recipients) appears in the sanity run-history row with the verbatim error code and message
- [ ] An announcement for that cause is sent once to the escalation recipients, else to the lead with the text "no escalation recipient is set"

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_announcement_falls_back_to_phase_lead_with_no_recipient_note`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0011: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Start every open sanity task at once (claim all, `atm task start` the active one); close each when its verdict arrives through the close hook (28, 29). The dev's close hook assigns the task as the lead as soon as the checked bead closes; after FAIL, the same task id is reopened in place.


### Rationale

The CHANGELOG records that the sanity close dispatches from the dev close hook and that a sanity FAIL re-assigns the same task id; and that dev-sanity executes every open task at once (SKILL.md: claim all, `atm task start` the active one), so the dev's next task is not blocked.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every open sanity task of the member is claimed with `bd update --claim` and exactly one is `active` in `atm task list`
- [ ] After a FAIL the same task id is reopened in place rather than a new task being created

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0012: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Not ready (`bd ready -n 0` omits it): do not claim or start; find the root cause; close the task `refused` (`bead_state` open), `reason_md` = bead, why, who must move and the dependency to add (`bd dep add <bead> --blocked-by <blocker>`); a blocker met mid-task: return the bead open, unassigned, blocker in notes, close the task `refused` the same way; never wait.


### Rationale

A task whose bead is not ready cannot be done and must not be held (CHANGELOG: a blocked task is refused, never held, naming the blocker and the dependency to add), so the lead can add the edge and re-assign.

### Success Criteria

**Acceptance Criteria:**

- [ ] For a bead absent from `bd ready -n 0`, `assignment-gates.py sanity` prints `NOT_READY` and dev-sanity makes no claim and no `atm task start`
- [ ] The task closes `refused` with `bead_state` `open` and a `reason_md` that names the bead, the blocker, who must move it and the `bd dep add <bead> --blocked-by <blocker>` command
- [ ] A blocker met mid-task leaves the bead open and unassigned with the blocker in its notes, and closes the task `refused`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_not_ready_is_a_gate_result`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0013: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

No separate `bd ready`, PR-base or stack gate precedes sanity. `assignment-gates.py sanity` checks NOT_READY, COMMIT_REQUIRED, SANITY_FROZEN and COMMIT_MISMATCH. The assignment carries BEADS_DIR and close context; sanity-split carries checked content and inline notes, so subagents perform no bead lookup.


### Rationale

The gate set was reduced to the checks sanity needs (CHANGELOG: sanity checks only history and the assigned worktree commit; the PR-base and stack gates were dropped), and the assignment carries `BEADS_DIR`, close context and inline notes so subagents need no bead lookup.

### Success Criteria

**Acceptance Criteria:**

- [ ] `assignment-gates.py sanity` returns exactly one of `READY`, `NOT_READY`, `COMMIT_REQUIRED`, `SANITY_FROZEN`, `COMMIT_MISMATCH` or `GATE_CANNOT_RUN`, and runs no `gh` or stack command
- [ ] The dev-sanity assignment JSON contains `BEADS_DIR` and the close context, and the `sanity-split` manifest contains the checked content and inline bead notes

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_checks_only_history_and_the_assigned_worktree_commit`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_requires_an_assigned_commit_before_reading_state`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0014: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

An unlinked PR is the normal state when sanity starts; after PASS closes, sanity-stack links it under the stack bead lock.


### Rationale

Layer 0 alone cannot form a gh stack (CHANGELOG: sanity accepts an unlinked PR on the trunk), so a PR unlinked at sanity time is normal and linking happens only under the stack bead lock after PASS.

### Success Criteria

**Acceptance Criteria:**

- [ ] `assignment-gates.py sanity` returns `READY` for a bead whose PR is not in any stack
- [ ] After the PASS close, `sanity-stack-link` links the PR under the stack bead claim and prints `stacked`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_refusals_and_ready`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0015: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Any refusal: close the task `refused` with the reason, command and failure evidence in `reason_md`; do not create or cite an outage class bead. A refusal before a reviewer report has no history row (27).


### Rationale

Refusals must be actionable and honest; outage class beads are only for outages, and a refusal before any reviewer report has nothing to log (CHANGELOG: gate failures print their reason; `GATE_CANNOT_RUN` is not a refusal of the bead).

### Success Criteria

**Acceptance Criteria:**

- [ ] A refusal closes the task `refused` with `reason_md` containing the reason, the failing command and its failure output
- [ ] No `-jev-outage`, `-jev-child-outage` or `-jev-result-invalid` bead is created or cited for a refusal
- [ ] A refusal before any reviewer report appends no row to the sanity run history

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0016: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Claim and `atm task start`; iteration = completed events of the task + 1.


### Rationale

Iteration decides whether disagreement is mechanical or triaged (REQ-DSAN-0057) and a reopened task is the same task id, so the count must come from the task's events (CHANGELOG: sanity close iteration comes from the complete task assignment history, #881).

### Success Criteria

**Acceptance Criteria:**

- [ ] After claiming and `atm task start`, dev-sanity records iteration equal to the number of `completed` events in `atm task events <task> --json` plus 1
- [ ] For a task completed once and reopened, the recorded iteration is 2

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_reopened_assignment_counts_from_task_events_not_old_context`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0017: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Run `sanity-split` exactly once (after a dev-fix, over the sprint's own layer PRs, the checked PR last); its run id, sha and reviewers apply to the whole run.


### Rationale

A second split would give a second run id, sha and lint run, so the reviewers' results could not merge into one verdict; the manifest carries one run id, pinned sha and reviewers (CHANGELOG: layer PR ranges read from one listing).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-split` is invoked once per task and writes one manifest with one `run_id`, one `sha` and one reviewer roster
- [ ] After a dev-fix the manifest's layer PR ranges cover the sprint's own layer PRs with the checked PR last

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0018: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Split failure: refuse with its actual code before dispatch; `SANITY.PLAN_INVALID`: tell the task assigner planning failed for that bead.


### Rationale

A split failure means the plan, target or commit is wrong; sanity-split exits with a named code and starts nothing, and `SANITY.PLAN_INVALID` tells the planner that the bead has no usable deliverables.

### Success Criteria

**Acceptance Criteria:**

- [ ] A `sanity-split` failure leaves no reviewer dispatched and the task `refused` with the actual `SANITY.*` code in `reason_md`
- [ ] For `SANITY.PLAN_INVALID`, the task assigner receives a message that planning failed for that bead

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_plan_invalid`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0019: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Dispatch every deliverable's assignment unchanged as fenced JSON to one `sc-sanity-llm` child, and send the deliverable's request array (51) to `jev_client.py`, both families before waiting; record each family's start and completion times. The request array to `jev_client.py` is not yet implemented (phase bl).


### Rationale

Splitting per deliverable gives each reviewer a bounded job, and sending both families at once keeps a sanity task at minutes (REQ-DSAN-0058); CHANGELOG records that handoffs send the inner assignment object exactly as the receiver's fenced JSON input accepts.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each manifest assignment is sent unchanged as fenced JSON to one `sc-sanity-llm` child per deliverable, and a request array to `jev_client.py`, both before any wait
- [ ] The start and completion epochs of each family are recorded for the later `sanity-merge --started-at/--completed-at`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0020: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Keep each reply unchanged in its own reviewer's array; never mix arrays.


### Rationale

Arrays from different reviewers carry different guarantees (Jev receipts versus none); mixing them would let a merge accept a result under the wrong reviewer, and `sanity-merge --reviewer` validates per family.

### Success Criteria

**Acceptance Criteria:**

- [ ] The LLM replies and the Jev replies are saved as two separate arrays and each is passed unchanged to `sanity-merge --reviewer sanity-llm|sanity-jev`
- [ ] No reply object appears in the other family's array

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0021: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Stop a child silent 30 minutes and keep its failure envelope; a failed child is yours: fix its assignment or context and rerun it; the rerun reply replaces the failed envelope before its merge; the replaced envelope goes in notes.


### Rationale

A silent child must not stall the 2-4 minute check, and the coordinator owns child failures (CHANGELOG: a failed LLM API spawn is retried up to three times, retaining the exhausted `SANITY.LLM_API_FAILURE` envelope).

### Success Criteria

**Acceptance Criteria:**

- [ ] A child silent for 30 minutes is stopped and its failure envelope kept
- [ ] A failed child is rerun after fixing its assignment or context, and the replacing reply is merged in place of the failed envelope while the replaced envelope is recorded in the completion notes

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0022: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Rerun fails, dispatch fails or the Jev probe has not passed: a coordinator failure envelope in that slot (in probe-failed mode the probe's own code and message verbatim); say that reviewer could not run; never substitute one reviewer for the other in that slot, except that a Jev no-evaluation takes the LLM reply (57, not yet implemented (phase bl)); one failed reviewer is not a blocker or CANNOT_RUN.


### Rationale

The CHANGELOG records that LLM and Jev are redundant reviewers: one failed reviewer keeps its failure envelope and only a deliverable with no valid reply is CANNOT_RUN, so no reviewer may be substituted in the other's slot.

### Success Criteria

**Acceptance Criteria:**

- [ ] When a rerun fails, dispatch fails or the probe has not passed, that slot holds a coordinator failure envelope (the probe's own code and message in probe-failed mode)
- [ ] No LLM reply is placed in the Jev slot except by the Jev no-evaluation rule of REQ-DSAN-0057
- [ ] One failed reviewer alone does not produce a blocker or CANNOT_RUN verdict

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0023: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Merge each family as it finishes; append no history yet.


### Rationale

Merging each family as it finishes keeps the merge ahead of the slower reviewer and lint, while history rows depend on the selected verdict and so wait (REQ-DSAN-0027).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each family is merged with `sanity-merge --reviewer ...` as soon as its last reply arrives
- [ ] The run history file has no appended row for the run until after the selected merge

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0024: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

From iteration 2 (57, not yet implemented (phase bl)), triage per deliverable: select `llm`, `jev` or `rerun`, with a reason for every disagreement or rerun; one reviewer failed: select the other's valid reply with the failure as reason; neither valid: CANNOT_RUN. A rerun goes to one child with the missing context added.


### Rationale

From iteration 2 a disagreement is triaged by the sanity agent (Rand's ruling quoted in REQ-DSAN-0057); `sanity-merge` accepts only a selection entry with the keys `deliverable`, `llm`, `jev`, `selected`, `reason`, `rerun`, `llm_sha256` and `jev_sha256`.

### Success Criteria

**Acceptance Criteria:**

- [ ] From iteration 2 each deliverable has a selection entry whose `selected` is `llm`, `jev` or `rerun`, with a non-empty `reason` for every disagreement or rerun
- [ ] When one reviewer failed, the selection entry takes the other's valid reply with the failure as `reason`; when neither reply is valid the deliverable is CANNOT_RUN
- [ ] A `rerun` entry goes to one child with the missing context added

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_handoff_contracts.py::DevSanityHandoffTests::test_selection_entry_keys_in_the_instruction_are_the_ones_sanity_merge_requires`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0025: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

`sanity-close-vars` writes stack input only for a fixed PASS, copying `budget` from the assignment's close context; `sanity-stack-link` makes one claim attempt, releases its claim after the write, and notifies the phase lead when the result is not `stacked`.


### Rationale

The stack input is written only for a fixed PASS and carries the assignment's budget and worktree path (CHANGELOG: `sanity-stack-link` runs git and gh in the checked layer's worktree), and a non-stacked result must not stay silent (stack outcomes notify the lead).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-close-vars` writes the stack input file only when the verdict is PASS, with `budget` equal to the assignment's close-context `budget`
- [ ] `sanity-stack-link` makes one claim attempt, releases its claim after the write, and sends the phase lead a notice when its result is not `stacked`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_stack_input_carries_assignment_budget_and_worktree_and_only_passes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_release_failure_after_write_keeps_stacked_result`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0026: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Selected merge: exit 4 (lint running) retry with the same times, never rerun lint; exit 0: PASS/FAIL; exit 1/3 with a report: CANNOT_RUN, keep error and raw results; no report: coordinator error, never PASS.


### Rationale

The shared lint run may still be going when the reviewers finish; the merge returns exit 4 and the same merge must be retried unchanged, never restarting lint (CHANGELOG: lint supervisor and `completed_at` stable across the exit-4 retry).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-merge` exiting 4 is retried with the same epochs and the same inputs, and lint is not started a second time
- [ ] On exit 0 the verdict is PASS or FAIL; on exit 1 or 3 with a report it is CANNOT_RUN with the error and raw results kept; with no report it is a coordinator error and never PASS

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_lint_unavailable`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_pass`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0027: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

After the selected merge, append exactly two history rows, `sanity-llm` then `sanity-jev`, with the selected verdict as final; selection or selected merge cannot run: `CANNOT_RUN`, still append both; a reviewer merge with no report has no row: report it to the task assigner.


### Rationale

The sanity ledger has two rows per run (CHANGELOG: `sanity-llm` and `sanity-jev`) with the selected verdict as final, and CANNOT_RUN still appends both rows so a failed run is auditable.

### Success Criteria

**Acceptance Criteria:**

- [ ] After the selected merge exactly two rows are appended to the phase sanity ledger, `sanity-llm` first and `sanity-jev` second, each carrying the selected verdict as `final`
- [ ] If selection or the selected merge cannot run, both rows are still appended with `CANNOT_RUN`
- [ ] A reviewer merge that produced no report has no row and is reported to the task assigner

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_selected_verdict_differs_from_one_reviewer`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_selected_merge_cannot_run_keeps_reviewer_verdicts`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0028: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

PASS: sanity-close-vars derives the complete hook input from the pinned split manifest and selected result; never hand-edit close vars. Run the close hook immediately on the selected verdict. It closes the sanity bead, dev and sanity tasks, then assigns QA. Only afterwards hand the generated input to sanity-stack; no stack link or human response gates the close.


### Rationale

Hand-edited close vars produced wrong closes, so the CHANGELOG makes `sanity-close-vars` derive the complete hook input from the pinned manifest and selected result, and the close runs on the verdict without waiting for any stack result (#498).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-close-vars` output for a PASS contains the complete close-hook vars and `stacked` null, with no hand-built field added
- [ ] `atm-task-close.py --role sanity` (or the daemon `atm task close`) is run immediately on the selected verdict and closes the sanity bead, the dev and sanity tasks, then assigns QA
- [ ] The stack handoff happens only after that close returns success

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_pass_builds_full_close_input_without_waiting_for_stack`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_agent_prompts.py::test_sanity_prompts_close_before_ordered_stack_handoff`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0029: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

FAIL within the cap: invoke the close hook with verdict FAIL and the selected undone deliverables and their reasons; it increments `metadata.sanity_round` on the sanity bead, reopens the checked bead to its assignee, sends the dev `sanity-fail.xml.j2` listing exactly what was NOT complete with the sprint reference, returns the sanity bead open and unassigned, and closes the sanity task `completed`, same template. No finding children are created.


### Rationale

A FAIL is the dev's work to redo, not a finding bead trail (CHANGELOG: sanity FAIL reopens the dev bead and sends `sanity-fail`; `finding_bead_ids` removed).

### Success Criteria

**Acceptance Criteria:**

- [ ] The FAIL close hook increments `metadata.sanity_round` on the sanity bead, reopens the checked bead to its assignee and leaves the sanity bead open and unassigned
- [ ] The dev receives `sanity-fail.xml.j2` listing exactly the undone deliverables and the sprint reference, and the sanity task closes `completed` with the same template
- [ ] No finding bead is created

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_task_close_hook.py::test_fail_reopens_dev_leaves_sanity_blocked_and_notifies_dev_before_close`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_task_close_hook.py::test_fail_notes_use_current_assignment_iteration`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0030: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Failure to perform the close-hook handoff is an error, not a completed handoff.


### Rationale

A close hook failure that is not noticed leaves the dev bead stuck; the daemon hook returns validation errors naming field, owner and correlation id and a pending drain refuses with `BEADS.WRITE_PENDING` so the failure surfaces.

### Success Criteria

**Acceptance Criteria:**

- [ ] When the close-hook handoff fails, the sanity task is not reported completed and the error is returned to dev-sanity
- [ ] The error is reported to the lead or assigner rather than treated as handoff done

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_task_close_hook.py::test_pending_drain_refuses_then_retry_assigns_without_repeating_writes`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0031: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Cannot run (unsplittable plan, missing worktree, unpushed commit, timeout, rejected twice): include the reason and evidence as in 15; bead open, no assignee, note; task `refused`.


### Rationale

An unrunnable check must not become a verdict; the CHANGELOG records CANNOT_RUN as an infrastructure state with the reason and evidence retained, and a refusal rather than a PASS or FAIL.

### Success Criteria

**Acceptance Criteria:**

- [ ] For an unsplittable plan, missing worktree, unpushed commit, timeout or twice-rejected result, the task closes `refused` with the reason and evidence in `reason_md`
- [ ] The checked bead is left `open` with no assignee and a note

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0032: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

FAIL exceeding the configured cap reports SANITY.ROUND_CAP to the lead with undone deliverables. Post-close stack outcomes never increment sanity_round; stack_failed, lock_timeout and rebase_required notify the lead and never reopen or hold the sanity task.


### Rationale

A FAIL loop with no limit never converges; SANITY.ROUND_CAP escalates it, and stack outcomes after a close are the lead's, so they never count as sanity rounds (CHANGELOG: rebase_required, lock_timeout and stack_failed notify the lead).

### Success Criteria

**Acceptance Criteria:**

- [ ] A FAIL beyond the configured cap sends `SANITY.ROUND_CAP` to the lead with the undone deliverables
- [ ] `stack_failed`, `lock_timeout` and `rebase_required` each notify the lead, leave the sanity task closed and leave `metadata.sanity_round` unchanged

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failed_post_close_handoff_notifies_lead_without_task_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0033: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

Keep LLM, JEV, selection and rerun evidence in completion notes.


### Rationale

The evidence for a verdict must survive the run; the sanity run history stores the LLM, Jev, selection and rerun evidence and the completion notes are what the lead and console read afterward (CHANGELOG: sanity ledger rows with receipts and errors).

### Success Criteria

**Acceptance Criteria:**

- [ ] The sanity task's completion notes contain the LLM reply, the Jev reply with its receipts, the selection entry and any rerun reply for each deliverable

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0034: Per assignment (task id = sanity bead id)

**Status:** Draft  
### Requirement Statement

After the task closes, read ATM again; never rewrite the sanity ledger.


### Rationale

The ledger is an append-only record of what ran; the CHANGELOG records that `sanity-run-history` appends with a single atomic write and refuses to alter an existing row, so changing it after the fact would falsify the record.

### Success Criteria

**Acceptance Criteria:**

- [ ] After the task closes dev-sanity reads ATM for its next task and issues no `sanity-run-history` rewrite or edit of the ledger file
- [ ] `sanity-run-history` fails with a non-zero exit when given a duplicate row that differs from the stored one

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_new_fields_round_trip_and_conflicting_retry_fails`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0035: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Judge only `deliverable.text` from deliverable text, owned paths, changed files, `context` paths and pinned commit; never request more.


### Rationale

Each reviewer judges one numbered deliverable from fixed evidence; the sc-sanity-llm and sc-sanity-jev prompts define the narrow luna-class test (`written: yes/no, file:line` from the deliverable text, owned paths, changed files and pinned commit) so verdicts are repeatable.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each reviewer prompt names `deliverable.text` as the only requirement judged and reads only the deliverable text, owned paths, changed files, `context` paths and the pinned commit

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0036: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Missing input field: `VALIDATION.INPUT`.


### Rationale

Reviewers run in parallel from one assignment object; a missing field would make them guess, so the sc-sanity-llm and sc-sanity-jev prompts both make step 1 validate the input and return `VALIDATION.INPUT`.

### Success Criteria

**Acceptance Criteria:**

- [ ] An assignment missing any field returns `success` false with `error.code` `VALIDATION.INPUT` from each reviewer
- [ ] The reply's `error.deliverable` equals the assignment's deliverable number

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0037: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Read only the pinned diff and files at `<commit>`, never the working tree; unreadable: `SANITY.TARGET_UNREADABLE`.


### Rationale

Working-tree reads would judge uncommitted or moved state; the prompts require `git diff <base_sha>...<commit>` and `git show <commit>:<path>` (CHANGELOG: sanity uses the PR parent commit as its pinned diff base) and `sanity-merge` rejects a worktree that moved after the split.

### Success Criteria

**Acceptance Criteria:**

- [ ] Reviewer commands in the prompts are limited to `git -C <worktree_path> diff <base_sha>...<commit>` and `git -C <worktree_path> show <commit>:<path>`
- [ ] An unreadable worktree, commit or base returns `SANITY.TARGET_UNREADABLE`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_target_unreadable`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_worktree_must_still_be_pinned`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0038: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Existing code may satisfy a deliverable; PR, QA, linking, merging are not judged.


### Rationale

Sanity asks whether a deliverable is written, not who wrote it or what came after (sc-sanity-llm prompt: code that already existed can satisfy it; PR, QA, linking and merging are not judged).

### Success Criteria

**Acceptance Criteria:**

- [ ] A deliverable satisfied by code that exists in the tree at the pinned commit but is absent from the diff is judged done
- [ ] Downstream PR, QA, linking or merging state is not cited in any reviewer finding

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0039: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Not done: exactly one `skipped` finding at a real relative file and line; missing file: line 1 of the nearest file that should reference it.


### Rationale

A single `skipped` finding at a real file and line gives the dev one place to look and keeps the merge rule simple (CHANGELOG: sanity findings are `skipped` only; `sanity-merge` rejects other kinds or several findings).

### Success Criteria

**Acceptance Criteria:**

- [ ] For a not-done deliverable the reply data has exactly one finding with `kind` `skipped`, a relative `file` that exists at the pinned commit and a numeric `line`
- [ ] For a missing file the finding is at line 1 of the nearest existing file that should reference it

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_rejects_multiple_or_non_skipped_findings`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0040: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

JEV: ask Jev for every deliverable through `jev_client.py --request` (one Choice question `written`, `yes`/`no`); the client's JSON return is copied unchanged (53, not yet implemented (phase bl)), and no agent turns it into a finding or verdict; Jev unavailable, timed out or invalid: failure envelope with the client's error verbatim, never an unaided result labelled Jev.


### Rationale

Jev replies carry proof of the call (CHANGELOG: `jev_client.py --request` prints a receipt and `sanity-merge --reviewer sanity-jev` rejects replies without one), and an unaided LLM conclusion must never be labelled Jev.

### Success Criteria

**Acceptance Criteria:**

- [ ] The sc-sanity-jev reply contains `data.jev` taken from the client's receipt and no finding or verdict is derived by an agent from the client's JSON
- [ ] When Jev is unavailable, timed out or invalid, the reply is a failure envelope carrying the client's error verbatim

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0041: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Return fenced JSON `{success, data, error}`; failure: `data:null`, `error:{code, message, recoverable, suggested_action, deliverable}`.


### Rationale

The coordinator parses reviewer output mechanically, so both prompts fix the shape: `{success, data, error}` with `data:null` and an `error` of code, message, recoverable, suggested_action and deliverable on failure.

### Success Criteria

**Acceptance Criteria:**

- [ ] A successful reply is fenced JSON with `success` true, `data` set and `error` null
- [ ] A failed reply has `success` false, `data` null and an `error` object with exactly `code`, `message`, `recoverable`, `suggested_action` and `deliverable`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0042: Subagents (sc-sanity-llm, sc-sanity-jev)

**Status:** Draft  
### Requirement Statement

Never edit, commit, push, build, test, lint or run `bd`/`atm`; empty findings is success.


### Rationale

Reviewers run in parallel on a shared worktree beside a lint run; any write, build or lint by a reviewer would corrupt the pinned state, and both prompts list the read-only constraint. An empty findings list is a success.

### Success Criteria

**Acceptance Criteria:**

- [ ] Neither reviewer prompt allows an edit, commit, push, build, test, lint or `bd`/`atm` command
- [ ] A reply with an empty `findings` array is accepted as success by `sanity-merge`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_pass`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0043: Scripts

**Status:** Draft  
### Requirement Statement

`assignment-gates.py sanity`: READY, NOT_READY, COMMIT_REQUIRED, COMMIT_MISMATCH, SANITY_FROZEN or GATE_CANNOT_RUN.


### Rationale

Gate results must be a closed set so the template can branch on them (CHANGELOG: every `GATE_CANNOT_RUN` prints its reason to stderr).

### Success Criteria

**Acceptance Criteria:**

- [ ] `assignment-gates.py sanity` prints exactly one of `READY`, `NOT_READY`, `COMMIT_REQUIRED`, `COMMIT_MISMATCH`, `SANITY_FROZEN` or `GATE_CANNOT_RUN`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_refusals_and_ready`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_frozen_history_wins_even_when_the_worktree_head_changed`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::AssignmentGateTests::test_sanity_commit_check_that_cannot_run_is_not_a_refusal`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0044: Scripts

**Status:** Draft  
### Requirement Statement

`sanity-split`: exit 2 `PLAN_INVALID` (no top-level numbered `## Deliverables`), 3 `TARGET_UNREADABLE`, 4 `COMMIT_MISMATCH` (HEAD, branch or origin not at sha, any `git status --porcelain` line other than the ignored paths, or the last layer PR's head not the sha), 5 `RENDER_FAILED`; one assignment per deliverable; lint once, detached, 1800 s timeout.


### Rationale

The split's exit codes are how dev-sanity decides whether to refuse (CHANGELOG: lint runs once, detached, with a timeout; lock and log files are not dirt).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-split` exits 2 `PLAN_INVALID` when there is no top-level numbered `## Deliverables`, 3 `TARGET_UNREADABLE`, 4 `COMMIT_MISMATCH` and 5 `RENDER_FAILED`
- [ ] `sanity-split` produces one assignment per deliverable and starts lint once, detached, with a 1800 s timeout

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_plan_invalid`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_commit_mismatch`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_target_unreadable`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_split.py::SanitySplit::test_lint_timeout_reaches_the_merge_as_lint_unavailable`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0045: Scripts

**Status:** Draft  
### Requirement Statement

`sanity-merge`: one valid result per deliverable at the pinned sha, at most one `skipped` each; PASS only with no findings and lint exit 0; lint diagnostics fold in as findings; lint timeout/cancelled/error is `SANITY.LINT_UNAVAILABLE`. `--reviewer sanity-jev` turns a reply without a valid receipt, whose choice contradicts its findings, that reuses another deliverable's receipt, or a `SANITY.JEV_*` failure not in the client's own text, into `SANITY.RESULT_INVALID` for that deliverable; the selected merge rejects such a reply, a failure envelope selected over a valid reply, and a failed rerun while either original reply is valid.


### Rationale

The merge is the one place the verdict is computed (REQ-DSAN-0003) and it screens Jev replies by receipt (CHANGELOG: Jev replies carry proof of the call).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-merge` outputs PASS only when each deliverable has one valid result with at most one `skipped` finding, no findings exist and lint exits 0
- [ ] Lint diagnostics appear as findings and a lint timeout, cancellation or error yields `SANITY.LINT_UNAVAILABLE`
- [ ] `--reviewer sanity-jev` converts a reply with no valid receipt, a contradicting choice, a reused receipt, or a `SANITY.JEV_*` message not in the client's text into `SANITY.RESULT_INVALID` for that deliverable

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_pass`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_lint_unavailable`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_lint_failure_parsed_to_file_and_line`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_a_jev_reply_without_a_valid_receipt_becomes_a_result_invalid_failure`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0046: Scripts

**Status:** Draft  
### Requirement Statement

`sanity-run-history`: rows only for `sanity-llm` or `sanity-jev`; a `sanity-jev` PASS/FAIL row carries every receipt; CANNOT_RUN has null findings and an error; locked append to the phase sanity ledger; an identical retry is a no-op, a differing duplicate fails.


### Rationale

History rows must be idempotent and complete (CHANGELOG: an identical retry is the same row; Jev PASS/FAIL rows carry every receipt).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-run-history` accepts a row only for reviewer `sanity-llm` or `sanity-jev`
- [ ] A `sanity-jev` PASS or FAIL row contains every receipt, and a CANNOT_RUN row has null findings and an error
- [ ] Appending the identical row again changes nothing and appending a differing duplicate exits non-zero

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_result_kind_uses_extensible_reviewer_matchers`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_jev_receipts_are_required_on_a_jev_verdict_and_absent_on_llm`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_new_fields_round_trip_and_conflicting_retry_fails`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0047: Scripts

**Status:** Draft  
### Requirement Statement

`sanity-create-findings`: retired by the close hook (29): a FAIL is reported to the dev as `sanity-fail`, not as finding children; the script is deleted with the hook change.


### Rationale

The finding-children script was retired by the close hook (CHANGELOG: close hook and `sanity-fail`; finding children removed), so no code should still create them.

### Success Criteria

**Acceptance Criteria:**

- [ ] The plugin tree contains no `sanity-create-findings` script
- [ ] A FAIL handoff creates no finding beads

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_task_close_hook.py::test_fail_reopens_dev_leaves_sanity_blocked_and_notifies_dev_before_close`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0048: Scripts

**Status:** Draft  
### Requirement Statement

`jev_client.py --startup` exits 2 on failure; `--announce` (with `--startup` or `--error "<code>: <message>"`, and `--lead`) sends the failure to each ATM escalation recipient, else to `--lead` saying no escalation recipient is set; missing `TYPESAFE_API_KEY` is `SANITY.JEV_UNAVAILABLE`.


### Rationale

`jev_client.py --startup` and `--announce` give the outage notice a single route (CHANGELOG: announces only with `--announce`, to the escalation recipients, else the lead saying none is set); a missing key is an outage, not a crash.

### Success Criteria

**Acceptance Criteria:**

- [ ] `jev_client.py --startup` exits 2 on failure and sends nothing without `--announce`
- [ ] `--announce` with `--startup` or `--error "<code>: <message>"` sends the failure to each escalation recipient, else to the lead with the note "no escalation recipient is set"
- [ ] A missing `TYPESAFE_API_KEY` yields `SANITY.JEV_UNAVAILABLE`

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_startup_without_announce_sends_nothing`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_startup_announcement_uses_configured_phase_recipients_despite_conflicting_environment`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_announcement_falls_back_to_phase_lead_with_no_recipient_note`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_error_announces_a_child_failure_verbatim_without_probing`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0049: Scripts

**Status:** Draft  
### Requirement Statement

`sanity-close-vars`: `--manifest`, `--selected`, optional `--stack-input` and `--stack-result`; prints the complete close-hook vars for the selected verdict and, for a fixed PASS, writes the stack input; exit 2 on invalid or mismatched input. Never hand-edited.


### Rationale

Close vars once needed hand assembly and drifted from the manifest (CHANGELOG: `sanity-close-vars` derives the complete input), so the script has a fixed interface and rejects mismatched input.

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-close-vars --manifest M --selected S` prints the complete close-hook vars for the selected verdict
- [ ] With `--stack-input F` and a fixed PASS it writes the stack input to F, and with a non-PASS verdict it writes none
- [ ] Invalid or mismatched input exits 2

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_pass_builds_full_close_input_without_waiting_for_stack`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_pinned_identity_mismatch_is_rejected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_stack_input_carries_assignment_budget_and_worktree_and_only_passes`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0050: Scripts

**Status:** Draft  
### Requirement Statement

`sanity-stack-link --input <stack-input.json> [--notify-lead <lead>]`: under the stack bead lock links the PASS layer and prints `stacked`, `stack_failed`, `lock_timeout` or `rebase_required`; a non-`stacked` result is sent to the lead; it never reopens the sanity task or counts a sanity round.


### Rationale

Stack linking is serialized under the stack bead lock and must not feed back into sanity (CHANGELOG: linked-only idempotent replay; layer 0 stays unlinked; results are lead notices).

### Success Criteria

**Acceptance Criteria:**

- [ ] `sanity-stack-link --input <file>` prints exactly one of `stacked`, `stack_failed`, `lock_timeout` or `rebase_required`
- [ ] A non-`stacked` result is sent to the lead
- [ ] The script never reopens the sanity task and never increments the sanity round

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_lock_timeout_returns_after_one_claim_attempt`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_stack.py::test_failed_post_close_handoff_notifies_lead_without_task_writes`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

## REQ-DSAN-0051: Jev client builds the sanity request from the assignment

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- `jev_client.py` MUST take exactly one mode: `--startup`, `--request <file>`, `--assignment <file>` or `--error <text>`.
- With `--assignment`, `jev_client.py` MUST read one sanity assignment, as fenced JSON or bare JSON.
- With `--assignment`, `jev_client.py` MUST reject an assignment that lacks `deliverable.text`, `worktree_path`, `commit`, `base_sha`, `changed_files` or `context` with `VALIDATION.INPUT`, before any Jev call.
- `jev_client.py` MUST build the request itself, with one `written` choice question (`yes`/`no`) whose state holds:
  - the deliverable text verbatim;
  - the committed `git diff <base_sha>...<commit>` of `changed_files`;
  - each `context` entry read at `commit`: the whole file for a plain `path`, only lines start..end for `path:start-end`.
- `jev_client.py` MUST reject a `path:start-end` entry outside the file's line count with `VALIDATION.INPUT`.
- `jev_client.py` MUST put each `external_evidence` reference into the state, labelled with its source:
  - `bead_notes` text inline;
  - a `pr_body` or `pr_comment` fetched with `gh api`.
- `jev_client.py` MUST fail an unreadable or malformed `external_evidence` reference with `VALIDATION.INPUT` before any Jev call.
- sc-sanity-jev MUST write the assignment it received, unchanged, to a file outside the worktree and run `jev_client.py --assignment <file>` on it.
- dev-sanity MUST pass each manifest entry's assignment unchanged to one sc-sanity-llm child and one sc-sanity-jev child.

**MUST NOT statements:**

- sc-sanity-jev MUST NOT write a Jev request itself.
- `jev_client.py --request` MUST NOT accept anything but one JSON object holding the pinned model, a state and nonempty Choice questions.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." Today the request is built by `jev_client.py` from the assignment, one deliverable per call. No agent packs evidence into an array of requests.

### Success Criteria

**Acceptance Criteria:**

- [ ] `jev_client.py --assignment` sends the deliverable text verbatim, the committed diff and the `context` files read at `commit` (`test_assignment_request_carries_the_deliverable_verbatim_and_the_committed_diff`)
- [ ] A `path:start-end` context entry sends only those lines, and an out-of-range entry is rejected (`test_a_line_range_context_entry_sends_only_those_lines_and_a_bad_range_is_rejected`)
- [ ] Context entries are read at the pinned top commit (`test_layered_source_reads_lower_layer_context_at_the_pinned_top`)
- [ ] Bead notes go inline and PR text is fetched, each labelled with its source (`test_evidence_only_deliverable_sends_bead_notes_and_pr_text_with_their_source`)
- [ ] Unreadable or malformed external evidence fails before any Jev call (`test_external_evidence_that_cannot_be_read_or_is_malformed_fails_before_any_jev_call`, `test_null_pr_body_is_empty_evidence_but_any_other_non_string_body_still_fails`)

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_assignment_request_carries_the_deliverable_verbatim_and_the_committed_diff`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_a_line_range_context_entry_sends_only_those_lines_and_a_bad_range_is_rejected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_layered_source_reads_lower_layer_context_at_the_pinned_top`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_evidence_only_deliverable_sends_bead_notes_and_pr_text_with_their_source`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_external_evidence_that_cannot_be_read_or_is_malformed_fails_before_any_jev_call`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_null_pr_body_is_empty_evidence_but_any_other_non_string_body_still_fails`

### Implementation Notes

Paths are under `plugins/atm-bd-orchestration/`; `jev_client.py` is `skills/atm-bd-orchestration/scripts/jev_client.py`.

- Modes, mutually exclusive and required: `jev_client.py:966-970`.
- Fenced or bare assignment JSON: `jev_client.py:920-922` (`FENCED`, line 59).
- Missing assignment fields → `VALIDATION.INPUT`: `jev_client.py:741-751`.
- Request built from the assignment (`assignment_requests`): `jev_client.py:765-797`. Diff: lines 782-783. Context excerpt: lines 785-794. The `written` question: `written_request`, lines 391-406.
- Out-of-range context entry: `jev_client.py:792-793`.
- External evidence shapes and fetch: `jev_client.py:644-728`. Invalid reference: lines 752-760. Unreadable fetch: line 676.
- `--request` shape check: `jev_client.py:171-187`, `929-934`.
- sc-sanity-jev writes the assignment unchanged and never writes a request: `agents/sc-sanity-jev.md:55-62`.
- dev-sanity passes each assignment unchanged to both children: `agents/dev-sanity.md:48-50`.

## REQ-DSAN-0052: Jev client splits oversized evidence losslessly

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- `jev_client.py` MUST hold every request it sends at or under `MAX_REQUEST_BYTES` (96000 encoded bytes).
- When an assignment's request is over the cap and it has `context` or `external_evidence`, `jev_client.py` MUST split the evidence, context and external text into labelled parts (`state.part` = `"i of n"`, with `state.changed_files`) without dropping content.
- When an assignment's request is over the cap and only the diff is present, `jev_client.py` MUST group the `changed_files` diffs into parts that each fit. A diff over the cap is cut by hunk, then by line, then by character.
- A `--request` over the cap MUST be split the same lossless way before sending.
- After an HTTP 413, or a 4xx whose `detail.error_type` is `max_tokens_exceeded`, `jev_client.py` MUST split that part into halves. The halves share the part's remaining attempt budget.
- When the deliverable text alone makes the request over the cap, `jev_client.py` MUST return `SANITY.JEV_REQUEST_TOO_LARGE` without a Jev call. Its `suggested_action` MUST tell the assigner to split the deliverable in the plan.
- When no further split fits, `jev_client.py` MUST return `SANITY.JEV_REQUEST_TOO_LARGE`. The message MUST name the request size and the bound.
- Each part MUST ask only whether that part delivers its share of the deliverable.

**MUST NOT statements:**

- `jev_client.py` MUST NOT drop or silently cut any evidence, context or external-evidence text when it splits.
- `jev_client.py` MUST NOT make a Jev call for a request it cannot split to fit.
- dev-sanity and sc-sanity-jev MUST NOT trim evidence to fit; splitting belongs to the client.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." Python splitting is still in the client: `split_request` and `diff_pieces`, and halving after a 413 or `max_tokens_exceeded`. This record states that splitting as it works today.

### Success Criteria

**Acceptance Criteria:**

- [ ] A local oversize request is split before sending, every part fits, and the evidence rejoins byte-for-byte (`test_local_oversize_is_shortened_before_sending_with_independent_part_budgets`)
- [ ] A diff over the cap is split by hunks, and a hunk by lines and characters (`test_a_diff_over_the_cap_is_split_by_hunks_and_every_part_returns_its_own_result`, `test_a_hunk_over_the_cap_is_cut_by_lines_and_a_line_by_characters`)
- [ ] Context and external evidence over the cap split without loss, empty entries kept (`test_oversize_assignment_splits_and_preserves_context`, `test_external_evidence_over_the_cap_splits_without_dropping_text`, `test_split_preserves_empty_context_and_external_evidence`)
- [ ] A 413 or `max_tokens_exceeded` splits the part, and the halves share its attempts (`test_server_oversize_splits_with_remaining_budget_and_eventually_succeeds`, `test_400_max_tokens_exceeded_splits_like_413`, `test_shortened_children_share_the_original_parts_remaining_attempts`, `test_four_oversize_attempts_never_issue_a_fifth`)
- [ ] An unsplittable request returns `SANITY.JEV_REQUEST_TOO_LARGE` with no Jev call (`test_unsplittable_local_request_reports_too_large_without_sending`, `test_non_text_oversize_state_is_terminal_without_network`, `test_deliverable_text_alone_over_the_cap_names_the_plan_fix`)

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_local_oversize_is_shortened_before_sending_with_independent_part_budgets`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_a_diff_over_the_cap_is_split_by_hunks_and_every_part_returns_its_own_result`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_a_hunk_over_the_cap_is_cut_by_lines_and_a_line_by_characters`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_oversize_assignment_splits_and_preserves_context`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_external_evidence_over_the_cap_splits_without_dropping_text`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_split_preserves_empty_context_and_external_evidence`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_server_oversize_splits_with_remaining_budget_and_eventually_succeeds`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_400_max_tokens_exceeded_splits_like_413`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_shortened_children_share_the_original_parts_remaining_attempts`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_four_oversize_attempts_never_issue_a_fifth`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_unsplittable_local_request_reports_too_large_without_sending`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_non_text_oversize_state_is_terminal_without_network`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_deliverable_text_alone_over_the_cap_names_the_plan_fix`

### Implementation Notes

Paths are under `plugins/atm-bd-orchestration/`; `jev_client.py` is `skills/atm-bd-orchestration/scripts/jev_client.py`.

- Cap: `jev_client.py:35`. The send path refuses a body over the cap: lines 194-201.
- Assignment split with context or external evidence (`split_request`): `jev_client.py:798-801`, `506-586`.
- Diff-only grouping: `jev_client.py:802-816`. Hunk, line and character cuts (`diff_pieces`): lines 434-466.
- `--request` split before sending (`evaluate_parts`): `jev_client.py:605-614`.
- Halving after 413 or `max_tokens_exceeded`: `jev_client.py:256-259`, `620-627`. The halves reuse the parent's `AttemptBudget`: line 627.
- Deliverable text alone over the cap, with the plan fix: `jev_client.py:803-807`. `suggested_action` uses `exc.fix`: lines 84-85.
- Unsplittable request → `SANITY.JEV_REQUEST_TOO_LARGE` naming the size and bound: `jev_client.py:425-431`, `515-516`, `538-539`, `570-571`.
- Per-part question: `jev_client.py:400-404`.
- Agents leave splitting to the client: `agents/dev-sanity.md:51-53`, `agents/sc-sanity-jev.md:58-62`, `113-114`.

## REQ-DSAN-0053: Jev client result envelope and verbatim receipts

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- `jev_client.py` MUST write exactly one JSON object to stdout: `{success, data, error, elapsed_s}`. It MUST exit 0 on success and 2 on failure.
- For an unsplit request, `data` MUST be the validated Jev response plus a `receipt`.
- For a split request, `data` MUST be `{model, parts}`, with every part in order. Each part is `{part, changed_files, response, receipt}`.
- A failure MUST carry `data: null` and `error: {code, message, recoverable, suggested_action}`.
- Each receipt MUST hold `model`, `question`, `choice`, `probabilities`, `response_id`, the `request_sha256` and an HMAC-SHA256 `mac` keyed with `TYPESAFE_API_KEY`.
- `jev_client.py` MUST reject a Jev response with the wrong model, answer ids that differ from the questions, or an invalid Choice answer, as `SANITY.JEV_RESPONSE_INVALID`.
- sc-sanity-jev MUST derive its findings from the client's choice:
  - `no` gives exactly one `skipped` finding, `yes` none;
  - for a split request, parts that agree set the findings;
  - parts that disagree give one `skipped` finding wrapped with `--for-triage`, and dev-sanity triages them.
- sc-sanity-jev MUST return the stdout of `wrap_jev_receipt.py`. That stdout copies the client's `data.receipt`, or its `data.parts`, verbatim into `data.jev`, and a client failure verbatim with `deliverable` added.
- `sanity-merge --reviewer sanity-jev` MUST turn a reply into `SANITY.RESULT_INVALID` when:
  - it has no verified receipt;
  - its findings contradict its receipts;
  - it reuses another deliverable's receipt.
- The sanity log row of a sanity-jev PASS or FAIL MUST carry the reply's `data.jev` receipts in `jev_receipts`.

**MUST NOT statements:**

- `jev_client.py` MUST NOT reduce split parts to one combined choice, answer or receipt.
- `jev_client.py` MUST NOT echo a Jev error response body or the API key. Only a short `detail.error_type` identifier may appear.
- sc-sanity-jev and dev-sanity MUST NOT hand-write `data.jev` or edit a receipt.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." Today the client returns one envelope per call, not JSONL. The sc-sanity-jev child turns the choice into findings, and the receipts are carried verbatim and verified.

### Success Criteria

**Acceptance Criteria:**

- [ ] An unsplit `--request` prints a receipt that verifies only with the API key (`test_request_prints_a_receipt_only_the_call_can_write`)
- [ ] A split assignment returns `data` with exactly `model` and `parts`, each part with its own response and verified receipt (`test_a_diff_over_the_cap_is_split_by_hunks_and_every_part_returns_its_own_result`)
- [ ] Error bodies and the key never reach the output (`test_auth_error_does_not_echo_body_or_key`, `test_4xx_names_the_parsed_error_type_and_nothing_else_from_the_body`)
- [ ] Invalid Jev responses are `SANITY.JEV_RESPONSE_INVALID` (`test_invalid_responses_are_terminal`, `test_bad_answer_shapes`)
- [ ] The wrapper copies receipts and parts verbatim and refuses edited ones (`test_single_receipt_passes_through_byte_identical`, `test_split_parts_pass_through_verbatim`, `test_hand_edited_receipt_field_is_rejected`, `test_hand_written_receipt_without_key_match_is_rejected`, `test_multi_choice_without_final_selection_is_rejected`)
- [ ] `sanity-merge` rejects a reply without a valid receipt (`test_a_jev_reply_without_a_valid_receipt_becomes_a_result_invalid_failure`)
- [ ] The ledger row carries the receipts (`test_jev_receipts_are_required_on_a_jev_verdict_and_absent_on_llm`)

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_request_prints_a_receipt_only_the_call_can_write`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_a_diff_over_the_cap_is_split_by_hunks_and_every_part_returns_its_own_result`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_auth_error_does_not_echo_body_or_key`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_4xx_names_the_parsed_error_type_and_nothing_else_from_the_body`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_invalid_responses_are_terminal`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_bad_answer_shapes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_single_receipt_passes_through_byte_identical`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_split_parts_pass_through_verbatim`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_hand_edited_receipt_field_is_rejected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_hand_written_receipt_without_key_match_is_rejected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_multi_choice_without_final_selection_is_rejected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_a_jev_reply_without_a_valid_receipt_becomes_a_result_invalid_failure`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_jev_receipts_are_required_on_a_jev_verdict_and_absent_on_llm`

### Implementation Notes

Paths are under `plugins/atm-bd-orchestration/`. Scripts are in `skills/atm-bd-orchestration/scripts/`.

- Envelope and exit codes: `jev_client.py:954-960`, `1009-1010`.
- Unsplit data plus receipt: `jev_client.py:630-633`, `946-948`.
- Split `{model, parts}`, unreduced: `jev_client.py:634-641`.
- Failure object: `jev_client.py:91-95`.
- Receipt fields and MAC: `jev_client.py:304-351`. Verification: lines 374-380.
- Response validation: `jev_client.py:124-135`, `204-213`, `269-277`.
- Body withheld, only `error_type`: `jev_client.py:265-268`, `409-418`.
- Choice to findings, and split handling: `agents/sc-sanity-jev.md:62-69`. Triage of disagreeing parts: `agents/dev-sanity.md:63-65`.
- Wrapper copies verbatim: `wrap_jev_receipt.py:21-24`, `330-331`. Agents must not hand-write: `agents/sc-sanity-jev.md:70-77`, `agents/dev-sanity.md:65`.
- Merge screening: `sanity-merge:26-32`, `404-458`.
- Ledger receipts: `skills/atm-bd-orchestration/templates/sanity-run-record.json.j2:4`, `50`.

## REQ-DSAN-0054: Jev client measures its own elapsed time

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- `jev_client.py` MUST measure `elapsed_s` with a monotonic clock around all of one invocation's Jev calls, including retries, Retry-After waits and every split part.
- `jev_client.py` MUST put `elapsed_s` in the outer envelope on success and on failure.
- `elapsed_s` MUST be `0.0` when the invocation fails before any Jev call.
- `wrap_jev_receipt.py` MUST copy the client's outer `elapsed_s` unchanged into the sc-sanity-jev reply. It MUST refuse a value that is not a finite nonnegative number.
- `sanity-run-history` MUST record a sanity-jev row's `jev_elapsed_s` as the maximum `elapsed_s` of its replies, or null when none carries one.

**MUST NOT statements:**

- dev-sanity and sc-sanity-jev MUST NOT compute or edit a Jev `elapsed_s`.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." The client already times its own calls. The time is one value per invocation, not one per request line.

### Success Criteria

**Acceptance Criteria:**

- [ ] `elapsed_s` includes retries and waits and is present on failure (`test_elapsed_includes_retries_and_is_present_on_failure`)
- [ ] A split request's `elapsed_s` covers every part's calls (`test_local_oversize_is_shortened_before_sending_with_independent_part_budgets`)
- [ ] A failure before any call reports `elapsed_s` 0.0 (`test_unsplittable_local_request_reports_too_large_without_sending`)
- [ ] The wrapper copies `elapsed_s` unchanged and refuses invalid values (`test_client_elapsed_s_is_copied_unchanged`)
- [ ] `sanity-merge` preserves a valid `elapsed_s` and rejects an invalid one (`test_jev_envelopes_accept_optional_elapsed_and_preserve_it`)
- [ ] The ledger takes the maximum (`test_jev_elapsed_uses_maximum_and_missing_is_null`)

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_elapsed_includes_retries_and_is_present_on_failure`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_local_oversize_is_shortened_before_sending_with_independent_part_budgets`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_unsplittable_local_request_reports_too_large_without_sending`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_client_elapsed_s_is_copied_unchanged`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_merge.py::SanityMerge::test_jev_envelopes_accept_optional_elapsed_and_preserve_it`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::SanityHistory::test_jev_elapsed_uses_maximum_and_missing_is_null`

### Implementation Notes

Paths are under `plugins/atm-bd-orchestration/`. Scripts are in `skills/atm-bd-orchestration/scripts/`.

- Timing around the calls: `jev_client.py:935-945`. Outer field and `0.0` default: line 959.
- Wrapper copy and validation: `wrap_jev_receipt.py:24`, `257-263`. The agent instruction: `agents/sc-sanity-jev.md:75-76`.
- Merge validation: `sanity-merge:310-314`.
- Ledger maximum: `sanity-run-history:110-123`.
- dev-sanity records only reviewer start and completion epochs, and the scripts derive the elapsed fields: `agents/dev-sanity.md:57-61`, `86-88`.

## REQ-DSAN-0055: Jev client retries transient failures within four attempts

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- `jev_client.py` MUST give each request part at most `MAX_JEV_ATTEMPTS` (4) HTTP attempts. Initial parts have independent budgets.
- `jev_client.py` MUST retry, within that budget:
  - HTTP 429, 502 and 529;
  - a transport failure (`OSError`, socket timeout, `http.client.HTTPException`).
- Before retrying a 429, 502 or 529, `jev_client.py` MUST wait for `Retry-After` (seconds or HTTP date), capped at 30 seconds. With no header it MUST wait 1 second, and with an unparseable one 30 seconds.
- When the budget is exhausted, `jev_client.py` MUST return `SANITY.JEV_UNAVAILABLE` with `recoverable: true`.
- Any other non-200 status MUST be terminal on the first attempt as `SANITY.JEV_UNAVAILABLE`. It is `recoverable: true` only for 429, 502 and 529.
- An invalid 200 response MUST be terminal on the first attempt as `SANITY.JEV_RESPONSE_INVALID`.
- A missing `TYPESAFE_API_KEY` MUST fail as `SANITY.JEV_UNAVAILABLE` before any network call.

**MUST NOT statements:**

- `jev_client.py` MUST NOT make a fifth attempt for one part, including the attempts used by the halves of a 413 or `max_tokens_exceeded` split.
- `jev_client.py` MUST NOT resend an unchanged request after a 413 or `max_tokens_exceeded`; it splits instead (REQ-DSAN-0052).
- `jev_client.py` MUST NOT retry any other 4xx or 5xx status, or an invalid response.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." The four-attempt budget is the lead ruling recorded at `jev_client.py:37`. The client does not report a retry count.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each transient status and transport error stops at 4 attempts and is recoverable (`test_retry_is_bounded`)
- [ ] A transient failure followed by success returns the result (`test_transient_statuses_and_transport_retry_to_success`)
- [ ] Every other 4xx or 5xx is sent once and is not recoverable (`test_other_http_errors_are_terminal`)
- [ ] Invalid responses are sent once (`test_invalid_responses_are_terminal`)
- [ ] `Retry-After` is honoured and capped at 30 s (`test_retry_after_is_honoured_and_capped_without_sleeping`)
- [ ] Each part has its own four attempts (`test_parts_have_independent_four_attempt_budgets`)
- [ ] Split halves share the part's remaining attempts (`test_four_oversize_attempts_never_issue_a_fifth`, `test_shortened_children_share_the_original_parts_remaining_attempts`)
- [ ] A missing key makes no network call (`test_missing_key_no_network`)

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_retry_is_bounded`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_transient_statuses_and_transport_retry_to_success`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_other_http_errors_are_terminal`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_invalid_responses_are_terminal`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_retry_after_is_honoured_and_capped_without_sleeping`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_parts_have_independent_four_attempt_budgets`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_four_oversize_attempts_never_issue_a_fifth`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_shortened_children_share_the_original_parts_remaining_attempts`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_missing_key_no_network`

### Implementation Notes

`jev_client.py` is `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/jev_client.py`.

- Budget: `jev_client.py:37-43`. Independent initial budgets: line 614. Shared by the halves: line 627.
- Transport retry: `jev_client.py:248-251`. Status retry with delay: lines 260-264.
- Retry-After parsing and cap: `jev_client.py:216-226`.
- Budget exhausted: `jev_client.py:278`.
- Other statuses terminal: `jev_client.py:265-268`. Invalid response terminal: lines 269-277.
- Missing key before network: `jev_client.py:98-104`, `231`.
- 413 and `max_tokens_exceeded` raise oversize and are never retried unchanged: `jev_client.py:256-259`.
- dev-sanity leaves API retries to the client: `agents/dev-sanity.md:51`. sc-sanity-jev never retries: `agents/sc-sanity-jev.md:62`.

## REQ-DSAN-0056: Jev client error codes and client-written messages

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every `jev_client.py` failure MUST carry one of four codes:
  - `SANITY.JEV_UNAVAILABLE`;
  - `SANITY.JEV_RESPONSE_INVALID`;
  - `SANITY.JEV_REQUEST_TOO_LARGE`;
  - `VALIDATION.INPUT`.
- Every failure message `jev_client.py` writes MUST match one pattern in `CLIENT_MESSAGES`.
- `jev_client.py` MUST pick `suggested_action` from the message: the oversize fix, then the HTTP case, then the first matching `FIXES` prefix, else "Report this error unchanged".
- An unreadable `--request` or `--assignment` file, or invalid JSON in it, MUST be reported as `VALIDATION.INPUT` with "Request file unavailable or invalid JSON".
- `wrap_jev_receipt.py` MUST refuse a client failure whose message is not a client message.
- `sanity-merge` MUST turn a `SANITY.JEV_*` failure whose message is not a client message into `SANITY.RESULT_INVALID`.

**MUST NOT statements:**

- `jev_client.py` MUST NOT emit a failure message outside `CLIENT_MESSAGES`.
- sc-sanity-jev MUST NOT change the client's error. It returns the error verbatim with `deliverable` added.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." Today errors are `JevError` exceptions, each with a string code and a fixed message. Downstream screening matches the message text.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every `JevError` literal in the client is a recognised client message (`test_every_failure_message_the_client_writes_is_recognised`)
- [ ] Each known error returns its fix (`test_each_known_error_returns_its_fix`)
- [ ] An unsplittable request reports `SANITY.JEV_REQUEST_TOO_LARGE` with a recognised message (`test_400_max_tokens_exceeded_on_every_attempt_names_the_token_limit`)
- [ ] The wrapper copies a client failure verbatim and refuses an edited message (`test_client_failure_is_copied_verbatim_with_deliverable`)

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_every_failure_message_the_client_writes_is_recognised`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_each_known_error_returns_its_fix`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_400_max_tokens_exceeded_on_every_attempt_names_the_token_limit`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_wrap_jev_receipt.py::WrapJevReceipt::test_client_failure_is_copied_verbatim_with_deliverable`

### Implementation Notes

Paths are under `plugins/atm-bd-orchestration/`. Scripts are in `skills/atm-bd-orchestration/scripts/`.

- `JevError` (code, message, recoverable): `jev_client.py:46-51`.
- Codes raised: `SANITY.JEV_UNAVAILABLE` at lines 101, 103, 251, 267, 278. `SANITY.JEV_RESPONSE_INVALID` at 126-148, 205-210, 270-276, 952. `SANITY.JEV_REQUEST_TOO_LARGE` at 428. `VALIDATION.INPUT` at 175-198, 676, 707, 743-759, 779, 793, 924, 933, 958.
- `CLIENT_MESSAGES`: `jev_client.py:281-301`.
- `suggested_action` selection: `jev_client.py:54-88`.
- File and JSON errors: `jev_client.py:957-958`.
- Wrapper refusal: `wrap_jev_receipt.py:330-331`.
- Merge screening: `sanity-merge:417-424`.
- Verbatim error in the child: `agents/sc-sanity-jev.md:106-112`.

## REQ-DSAN-0057: A failed Jev slot keeps its error and the LLM reply is selected

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- dev-sanity MUST run the Jev startup probe (`jev_client.py --startup`) at session start and on a credential change.
- The probe MUST send only synthetic state and pass only when Jev answers `ready`.
- A failed probe, or `SANITY.JEV_UNAVAILABLE`, MUST keep the Jev slots unavailable with their exact error. dev-sanity MUST retry the probe at the start of the next task.
- With `--announce --phase <phase>`, a failed probe MUST be sent through `atm send --as <tool_identity>`. The recipients are tried in this order:
  - the phase team's escalation list;
  - the daemon's escalation list;
  - the phase lead, with a note that no escalation recipient is set.
- dev-sanity MUST dispatch the sc-sanity-llm and sc-sanity-jev children for a deliverable concurrently.
- dev-sanity MUST keep a Jev child's failure envelope unchanged in that deliverable's Jev slot. The selected reply is then the LLM reply already running beside it.
- For `SANITY.JEV_REQUEST_TOO_LARGE`, dev-sanity MUST announce the error once per run with `jev_client.py --announce --phase <phase> --error "<code>: <message>"`. The announcement states that no LLM or haiku check replaces Jev for that slot.
- `sanity-merge --reviewer sanity-selected` MUST reject:
  - a selection that takes a `cannot_run` reply while the other reviewer's reply is valid;
  - a disagreement or rerun without a `reason`.
- When neither reviewer has a valid reply, the deliverable MUST be CANNOT_RUN, not FAIL.
- The failed Jev slot's error MUST be logged verbatim in the sanity-jev ledger row, as `API_FAILURE`, while the LLM reply is selected.
- On iteration 1, when Jev and the LLM both return a valid result, dev-sanity MUST treat a FAIL from either as the deliverable's FAIL. From iteration 2 it MUST triage the disagreement and name it in `reason`.

**MUST NOT statements:**

- dev-sanity MUST NOT start a new LLM or haiku check in place of a Jev slot.
- dev-sanity MUST NOT let an LLM PASS override a Jev FAIL on iteration 1.
- dev-sanity MUST NOT replace a valid original reply with a failed rerun.

### Rationale

Rand (2026-11-07): "The strategy for how to prompt jev sanity needs to get reviewed and tightened. For now we need documentation and code in sync." The iteration-1 and iteration-2 rule is in the dev-sanity prompt only. `sanity-merge` does not read the iteration: it accepts a selected LLM PASS over a Jev FAIL when a reason is given (`test_selected_verdict_differs_from_one_reviewer`).

### Success Criteria

**Acceptance Criteria:**

- [ ] A failed startup probe with `--announce` reaches the phase escalation recipients as the tool identity (`test_startup_announcement_uses_configured_phase_recipients_despite_conflicting_environment`)
- [ ] It falls back to the daemon list, then to the phase lead with the note (`test_announcement_falls_back_to_daemon_recipients`, `test_announcement_falls_back_to_phase_lead_with_no_recipient_note`)
- [ ] `--error` announces verbatim without probing (`test_error_announces_a_child_failure_verbatim_without_probing`)
- [ ] An oversized-request announcement says no LLM or haiku check replaces Jev (`test_an_oversized_request_error_is_announced_without_an_llm_fallback`, `test_oversized_jev_request_is_announced_and_never_starts_an_llm_check`)
- [ ] A failed Jev slot is logged verbatim while the LLM reply is selected (`test_failed_jev_slot_error_is_logged_verbatim_while_llm_is_selected`, `test_oversized_jev_failure_reaches_ledger_with_reason`)
- [ ] A disagreement without a reason makes the selected merge CANNOT_RUN (`test_selected_merge_cannot_run_keeps_reviewer_verdicts`)
- [ ] No existing test covers the iteration-1 FAIL rule, the "take the valid reviewer" rejection, or the failed-rerun rejection

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_startup_announcement_uses_configured_phase_recipients_despite_conflicting_environment`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_announcement_falls_back_to_daemon_recipients`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_announcement_falls_back_to_phase_lead_with_no_recipient_note`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_error_announces_a_child_failure_verbatim_without_probing`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_an_oversized_request_error_is_announced_without_an_llm_fallback`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_agent_prompts.py::test_oversized_jev_request_is_announced_and_never_starts_an_llm_check`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::ShippedFlow::test_failed_jev_slot_error_is_logged_verbatim_while_llm_is_selected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::ShippedFlow::test_oversized_jev_failure_reaches_ledger_with_reason`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::ShippedFlow::test_selected_merge_cannot_run_keeps_reviewer_verdicts`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_run_history.py::ShippedFlow::test_selected_verdict_differs_from_one_reviewer`

### Implementation Notes

Paths are under `plugins/atm-bd-orchestration/`. Scripts are in `skills/atm-bd-orchestration/scripts/`.

- Probe duty: `agents/dev-sanity.md:22-25`. Synthetic probe: `jev_client.py:383-388`. Probe result: lines 949-953.
- Announce argument rules: `jev_client.py:975-978`. Recipients: lines 852-874. Send as the tool identity: lines 877-888. Startup failure message: lines 1003-1008.
- `--error` messages: `jev_client.py:990-1001`. The oversized branch: lines 992-996.
- Concurrent children: `agents/dev-sanity.md:48-50`.
- Failure kept in the slot, with no new check: `agents/dev-sanity.md:53`, `agents/sc-sanity-jev.md:123-131`.
- Selection rules: `sanity-merge:603-604` (reason), `631-632` (take the valid reviewer), `633-635` (failed rerun).
- CANNOT_RUN when neither reviewer is valid: `agents/dev-sanity.md:79-80`.
- Iteration rule (prompt only): `agents/dev-sanity.md:67-70`.

## REQ-DSAN-0058: dev-sanity checks that deliverables are written, not QA

**Status:** Draft  
### Requirement Statement

dev-sanity checks that each deliverable is written; it is not QA and does not judge quality or requirements. A sanity task is expected to take 2 to 4 minutes; in phase bk dev-sanity mistook its role for QA and caused a many-hour backlog.


### Rationale

The sanity role is bounded by minutes: in phase bk dev-sanity mistook its role for QA and caused a many-hour backlog (commit 72b880b34 records Rand's role and speed rulings).

### Success Criteria

**Acceptance Criteria:**

- [ ] `agents/dev-sanity.md` instructs it to judge only whether each numbered deliverable is written, never code quality or requirements
- [ ] For a run with no Jev outage, the time from the `started` to the `completed` event in `atm task events <task>` is between 2 and 4 minutes

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.


## REQ-DSAN-0059: dev-sanity works up to 3 sanity tasks in parallel

**Status:** Draft  
### Requirement Statement

dev-sanity runs up to 3 ATM tasks in parallel. `atm task` allows only one ACTIVE task, which is not a limit on parallel work: the agent starts the active one, claims the others, and works all three at once.


### Rationale

Sanity tasks queue behind each other when run one at a time. SKILL.md records that ATM nudges one active task at a time while dev-sanity and quality-mgr execute every open task at once (`atm task start` for the active one, `bd update --claim` for all); commit 72b880b34 records the ruling.

### Success Criteria

**Acceptance Criteria:**

- [ ] With three open sanity tasks assigned, all three beads are claimed with `bd update --claim` and exactly one task shows `active` in `atm task list`
- [ ] The other two tasks are worked concurrently and each closes on its own verdict

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.


## Unresolved

1. Clean tree: all three ignore `.beads.gate.lock`/`.sc-compose/`; `assignment-gates.py` also ignores untracked files, while `sanity-split` and `sanity-merge` fail `COMMIT_MISMATCH` on any other `git status --porcelain` output.
2. Jev client: REQ-DSAN-0051..0057 describe today's `jev_client.py` (Rand 2026-11-07: "For now we need documentation and code in sync"). Requirements 19, 20, 22, 24, 33, 40 and 45 still describe the phase-bl request array, JSONL output or an `sc-sanity-jev` child, and must be corrected to match those records. The phase-bl contract items are future work, not records.

## REQ-DSAN-0060: Sanity pass closes the sanity task and bead

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- On a sanity PASS, the sanity task.close hook MUST close the sanity bead.
- On a sanity PASS, the sanity task.close hook MUST leave the sanity ATM task closed as completed.


### Rationale

Rand (2026-11-08): "typical sanity close path is 'sanity pass' condition in atm-task-close-sanity-hook (which would close sanity task + sanity bead)."

### Success Criteria

**Acceptance Criteria:**

- [ ] After a sanity PASS close, the sanity bead is closed and the sanity task is completed, with no further command.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/sanity_task_close_hook.py`, `SANITY-CLOSE-HOOK.md`. State: implemented for phases that register the hook; `atm-task-close.py --role sanity` remains as a second path (aa45ccc31, #557, 2026-10-23: local rollout).

## REQ-DSAN-0061: Phase lead has written sanity close and bypass steps

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The skill MUST give the phase lead the exact commands to close a sanity check as PASS.
- The skill MUST give the phase lead the exact commands to bypass sanity for a bead.
- Each set of commands MUST name the evidence the lead records with it.
- The sanity task.close hook MUST accept a close or bypass of a sanity task by the phase lead.


### Rationale

Rand (2026-11-08): "phase-lead must also be able to close/bypass sanity with clear instructions (so he doesn't guess)."

### Success Criteria

**Acceptance Criteria:**

- [ ] Following only the skill's steps, a lead closes a sanity check as PASS and the QA bead becomes ready.
- [ ] Following only the skill's steps, a lead bypasses sanity and the QA bead becomes ready.

### Implementation Notes

State: not yet implemented; `skills/atm-bd-orchestration/SKILL.md` has no lead close or bypass steps (only `SANITY.ROUND_CAP`, line 372).
