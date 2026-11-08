# dev-sanity

**ID Range:** REQ-DSAN-0001 through REQ-DSAN-0059  
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

## REQ-DSAN-0051: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

Rand (#497): "context packing LLM must split and send array of requests to jev." The dev-sanity agent that holds the full context splits each deliverable's evidence into an array of requests and sends that array to `jev_client.py`, which reads it as the array of requests.


### Rationale

Rand's #497 ruling is the origin of this requirement (commit 3c5baf412 records requirements 51-56): the agent that holds the full context, not Python, packs evidence into requests for Jev.

### Success Criteria

**Acceptance Criteria:**

- [ ] The dev-sanity agent builds each deliverable's evidence into an array of requests and passes that array to `jev_client.py`
- [ ] `jev_client.py` reads the argument as an array of requests

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0052: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

`jev_client.py` never splits, packs or halves a request in Python: no `split_request`, no `diff_pieces`, no chunking, and no halving after an HTTP 413. It sends each request to Jev as given; Rand: "agreed: Python splitting deleted." A request over the input budget returns a named error, never a silent cut.


### Rationale

The CHANGELOG records that Python splitting was added for oversized requests (#94, then 413 shortening and 400 `max_tokens_exceeded` splitting), which the #497 ruling reverses: Rand, "agreed: Python splitting deleted" (commit 3c5baf412). Splitting belongs to the agent that holds the context.

### Success Criteria

**Acceptance Criteria:**

- [ ] `jev_client.py` defines no `split_request` or `diff_pieces` function and contains no chunking or halving code after an HTTP 413
- [ ] A request larger than the input budget makes `jev_client.py` return a named error object and send nothing cut

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_unsplittable_local_request_reports_too_large_without_sending`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0053: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

Rand (#365): "the jev call should be returned. I do NOT want an agent 'interpreting' what the jev python call returns. the return must be json and included in the final result/data written to sanity log." Rand: "client should return jsonl one response per request." `jev_client.py` reads the array of requests and writes JSONL to stdout: exactly one line per request, in request order, each line the JSON result for that request (an evaluation or an error). Every line is copied unchanged into the final result and the sanity log. No agent interprets the return.


### Rationale

Rand's #365 ruling: an agent "interpreting" what the Jev call returns is not wanted. The CHANGELOG shows the opposite today: a split request returns `data.parts` that the agent reduces. One JSONL line per request in request order gives every result a fixed place in the log.

### Success Criteria

**Acceptance Criteria:**

- [ ] For an array of N requests, `jev_client.py` writes exactly N lines to stdout, each valid JSON, in request order, each an evaluation or an error
- [ ] Each line appears byte-identical in the final result and in the sanity log
- [ ] No agent prompt instructs the agent to turn the client's lines into a finding or verdict

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0054: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

Rand (#365): "the elapsed time for the jev call is calculated in jev-py". `jev_client.py` measures the elapsed time of each Jev call and returns it in its JSON; no agent computes it.


### Rationale

Rand (#365): "the elapsed time for the jev call is calculated in jev-py". The client already returns `elapsed_s` including retries and on failure, so agent-side timing is redundant and unreliable.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each result line from `jev_client.py` contains the elapsed time of its Jev call, measured inside the client
- [ ] No agent prompt computes a Jev elapsed time

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_jev_client.py::JevClientTests::test_elapsed_includes_retries_and_is_present_on_failure`

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0055: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

Rand (#365): "jev-py includes retry for known API 'busy' error (it does not stupidly retry on other errors like out-of-tokens, context-too-large)." `jev_client.py` retries only the known API-busy error and returns the number of retries in its JSON (zero when none). It never retries any other error.


### Rationale

Rand (#365): retry only the known API "busy" error. The client today retries transient statuses and transport errors up to four attempts (`test_transient_statuses_and_transport_retry_to_success`, `test_retry_is_bounded`), which also retries errors that cannot succeed on retry.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a busy response `jev_client.py` retries the request and the result JSON carries the retry count, which is 0 for a request that was not retried
- [ ] After an out-of-tokens error or a context-too-large error the client sends the request once and returns the error with retry count 0

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0056: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

Rand (#365): "jev should return an enum with all known errors which is exhaustively checked in match." Rand: "I am planning on writing a rust crate for launching which would have match. write the jev python code w/ this in mind." Every known `jev_client.py` error is a member of one closed enum with stable string codes, and the code that handles an error checks that enum exhaustively in a `match`. Each error is a tagged JSON variant, `{"kind": "<code>", ...fields}`, so a Rust enum with an exhaustive `match` mirrors it one to one. There is no Python-only behaviour: no exception classes carried in output, and no free-form message decides behaviour.


### Rationale

Rand (#365): the errors should be an enum checked exhaustively in a `match`, mirrored by a planned Rust crate. The client today carries errors as `JevError` exception codes and free-form messages that other code matches on (`jev_client.py`, `SANITY.JEV_*` message screening in `sanity-merge`).

### Success Criteria

**Acceptance Criteria:**

- [ ] Every known `jev_client.py` error is one member of a single closed enum with a stable string code
- [ ] Each emitted error is a JSON object `{"kind": "<code>", ...fields}`
- [ ] No Python exception class or free-form message text decides behavior in the code that handles an error

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0057: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

**Status:** Draft  
### Requirement Statement

Rand: "if jev-api failed (i.e. jev did not respond), the parallel llm evaluator's response is used. If both llm+jev respond a failure on either is failure on iteration #1. for iteration > 1, sanity-agent to triage (which should be done w/ background agent if sanity-agent has queue backlog)." When Jev returned no evaluation (any enum error), that deliverable mechanically takes the parallel LLM reply and the Jev error JSON stays in the log. When both reply, a failure from either is a FAIL on iteration 1; from iteration 2 the sanity agent triages the disagreement, by a background agent when it has a queue backlog.


### Rationale

Rand's ruling (quoted in this requirement): a Jev outage must not stop the deliverable, and disagreement is a FAIL on iteration 1 but a triage question afterward. The existing prompts already forbid substituting one reviewer for the other except through selection.

### Success Criteria

**Acceptance Criteria:**

- [ ] When Jev returned no evaluation (any enum error), the deliverable's selected reply is the parallel LLM reply and the Jev error JSON is in the log
- [ ] With both replies valid on iteration 1, a failure from either makes the deliverable a FAIL
- [ ] From iteration 2 the sanity agent triages the disagreement, using a background agent when it has a queue backlog

### Implementation Notes

Sources: `agents/{dev-sanity,sanity-stack,sc-sanity-llm,sc-sanity-jev}.md`, `templates/{dev-sanity-template.xml.j2,dev-sanity-assignment.json.j2}`, `scripts/{sanity-split,sanity-merge,sanity-run-history,sanity-close-vars,sanity-stack-link,assignment-gates.py}`, `skills/atm-bd-orchestration/scripts/{jev_client.py,atm-task-close.py}`, `atm-bd-orchestration/SKILL.md`, `formulas/README.md`, `atm-beads/resources/{dev-sanity,orchestrating}.md`, `README.md`, `install.py`.

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0058: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

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

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## REQ-DSAN-0059: Jev request and return contract (Rand rulings 2026-10-21; issues #497, #365) — not yet implemented (phase bl)

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

Not yet implemented (phase bl): these items state the ruled target. Today `jev_client.py` still splits requests (`split_request`, `diff_pieces`) and shortens them after an HTTP 413, and dev-sanity still dispatches an `sc-sanity-jev` child.

## Unresolved

1. Clean tree: all three ignore `.beads.gate.lock`/`.sc-compose/`; `assignment-gates.py` also ignores untracked files, while `sanity-split` and `sanity-merge` fail `COMMIT_MISMATCH` on any other `git status --porcelain` output.
2. Jev child: requirements 20, 22, 24, 33 and 45 still describe an `sc-sanity-jev` child and a Jev reply screened by `sanity-merge --reviewer sanity-jev` (a reply whose choice contradicts its findings, a receipt check), where a request now yields one JSONL line (53) instead of one reply per child. Requirements 19, 40 and 51 to 53 now have dev-sanity send the request array to `jev_client.py` and copy its JSON unchanged with no agent interpreting it. What a Jev failure does is settled by 57 (the LLM reply is used); how a Jev evaluation becomes a verdict, and whether the `sc-sanity-jev` child and the receipt screening in 45 remain, awaits a ruling and the phase-bl design.
