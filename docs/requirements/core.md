# core

**ID Range:** REQ-CORE-0001 through REQ-CORE-0040  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-11-07  
**Last Updated:** 2026-11-07  
**Owner:** Rand Lee  

---

## REQ-CORE-0001: Team and identity come from phase folder

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every atm-bd entry point that sends an ATM message or reads ATM tasks MUST take the ATM team from the `team` key of the phase file `.atm-bd/phase-<x>.toml`, else from `[atm] default_team` in the `.atm.toml` of the folder that holds `.atm-bd`.
- Every such entry point MUST take the ATM identity it acts as from the `lead` key of that phase file.

**MUST NOT statements:**

- An atm-bd entry point MUST NOT read `ATM_TEAM` or `ATM_IDENTITY` from the caller's environment to choose a team or identity.


### Rationale

Rand (2026-11-07): "atm-bd should not get team or identity from environment. It should come from folder where phase config is loaded." and "when omega-prime@hermes runs `atm-bd query` for atm-dev, I do not want team hermes leaking in. Every ingress into the system MUST access the risk of environment var being used." The phase lead is defined in the phase file.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `ATM_TEAM=hermes` set and a phase file whose team is `atm-dev`, `atm-bd queues` reads tasks for team `atm-dev`.
- [ ] With `ATM_IDENTITY=other` set, the identity used equals the phase file's `lead`.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_phase_settings.py::test_invalid_phase_setting_fails_launch_before_effects`

### Implementation Notes

Sources: `apps/atm-bd-console/src/atm_bd_console/config.py:99-126` (`phase_caller`), `queues.py:150-178`. State: lite implemented for console and queues (those files); the cron tick path is not yet (see the next records). orchestration: not assessed in this draft.

## REQ-CORE-0002: Cron recipients use the phase team

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The shared executor MUST address every phase recipient as `<agent>@<phase team>` using the team resolved from the phase file.

**MUST NOT statements:**

- The shared executor MUST NOT read `ATM_TEAM` from the environment to address a recipient.


### Rationale

Rand (2026-11-07): "atm-bd should not get team or identity from environment. It should come from folder where phase config is loaded." and "when omega-prime@hermes runs `atm-bd query` for atm-dev, I do not want team hermes leaking in. Every ingress into the system MUST access the risk of environment var being used."

### Success Criteria

**Acceptance Criteria:**

- [ ] With `ATM_TEAM` unset and a phase file naming team `atm-dev`, a Report is addressed to `<lead>@atm-dev` and is sent.
- [ ] With `ATM_TEAM=hermes` set, the same Report is still addressed to `<lead>@atm-dev`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:144-150` (`recipient`). State: lite not yet implemented (`execute.py:147` reads `os.environ.get("ATM_TEAM")` and raises when unset; `core/tests/tick/test_tick.py::test_missing_team_returns_typed_failure_without_running_command` asserts that behaviour and would have to change). orchestration: not assessed in this draft.

## REQ-CORE-0003: Child commands inherit no caller identity

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every ATM or bd command the shared tick runs MUST receive the team and identity from the phase file as explicit arguments or as the only ATM variables in its environment.

**MUST NOT statements:**

- The shared tick MUST NOT pass the caller's `ATM_TEAM` or `ATM_IDENTITY` through to a child command.


### Rationale

Rand (2026-11-07): "atm-bd should not get team or identity from environment. It should come from folder where phase config is loaded." and "when omega-prime@hermes runs `atm-bd query` for atm-dev, I do not want team hermes leaking in. Every ingress into the system MUST access the risk of environment var being used."

### Success Criteria

**Acceptance Criteria:**

- [ ] A recording runner shows no `ATM_TEAM` value from the parent environment in any child command's environment or argv.
- [ ] `atm task list` is issued with `--team <phase team> --as <phase lead>`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/tick.py:33-39` (`SubprocessRunner.run` builds `{**os.environ, "ATM_IDENTITY": ...}`), `plugins/atm-bd-orchestration/core/atm_bd_core/collect/atm.py:16-26` (`atm task list --all --json` with no `--team`). State: lite not yet implemented (`tick.py:36` copies the whole environment; `collect/atm.py:19` omits `--team` and `--as`). orchestration: not assessed in this draft.

## REQ-CORE-0004: Hooks read no environment

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every package task hook MUST take the caller, team and task from the ATM hook request and the phase file only.

**MUST NOT statements:**

- A package task hook MUST NOT read an environment variable.
- A package task hook MUST NOT run a subprocess.


### Rationale

Rand (2026-11-07): "atm-bd should not get team or identity from environment. It should come from folder where phase config is loaded." and "when omega-prime@hermes runs `atm-bd query` for atm-dev, I do not want team hermes leaking in. Every ingress into the system MUST access the risk of environment var being used." Hooks are an ingress into the system.

### Success Criteria

**Acceptance Criteria:**

- [ ] No hook script contains `os.environ`, `getenv` or `subprocess`.
- [ ] The import-boundary test fails when a hook imports a module other than `atm_bd_types` and `sys`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_boundary.py::test_plugin_imports_only_atm_bd_types`
- `plugins/atm-bd-orchestration/tests/lite/test_boundary.py::test_checker_rejects_framework_and_io_imports`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:9-12`, `atm-bd-task-start-hook.py:9-12`, `atm-bd-task-hook.py:9-12` (imports are `sys` and `atm_bd_types`). State: lite implemented (those lines; test_boundary.py). orchestration: not assessed in this draft.

## REQ-CORE-0005: Phase lead has no default

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The phase file MUST define a non-empty `lead`.
- Loading a phase file without a non-empty `lead` MUST return a typed refusal.

**MUST NOT statements:**

- An atm-bd component MUST NOT substitute `team-lead` or any other name when the phase file's `lead` is absent.


### Rationale

Rand (2026-11-07): "phase-lead is defined in the phase-file (it should NOT default to team-lead)."

### Success Criteria

**Acceptance Criteria:**

- [ ] A phase file with `lead` absent, empty or whitespace is refused, naming the key.
- [ ] No source file under the package assigns the literal `team-lead` as a default lead.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_phase_settings.py::test_invalid_phase_setting_fails_launch_before_effects`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/store/phase.py:21-24` (missing `lead` becomes PHASE_UNREADABLE), `apps/atm-bd-console/src/atm_bd_console/config.py:106-109`. State: lite implemented for the lead key (those lines). The lite policy still carries `lead = "team-lead"` (see the lite cron record). orchestration: not assessed in this draft.

## REQ-CORE-0006: Agents claim with their own identity

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every agent step that claims a bead or the stack bead MUST pass `--actor "$ATM_IDENTITY"`, the agent's own session identity.


### Rationale

Rand (2026-11-07): agents claim with `--actor "$ATM_IDENTITY"` (their own session identity); "this is correct".

### Success Criteria

**Acceptance Criteria:**

- [ ] Every `bd update` claim line in every dispatch template contains `--actor "$ATM_IDENTITY"`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/templates/dev.xml.j2:32,51,66`. State: lite not yet implemented in the stated form (the claim lines use `--assignee "$ATM_IDENTITY"` and no template contains `--actor`; whether bd's `--actor` is needed in addition is for the owner to confirm). orchestration: not assessed in this draft.

## REQ-CORE-0007: Planning names a class not an agent

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A planned dev bead MUST name its assignee as one of `fast`, `normal` or `frontier`.

**MUST NOT statements:**

- A planned bead MUST NOT lock in an exact agent name.


### Rationale

Rand (2026-11-07): "in planning asignee should be fast/normal/frontier so exact dev is not locked in."

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan` accepts `fast`, `normal`, `frontier` and rejects an agent name in the planned assignee field.

### Implementation Notes

Sources: none found. State: lite not yet implemented (`plugins/atm-bd-orchestration/skills/atm-bd-lite/policy.toml:2,4` fix `dev_agent = "dev"` and `qa_agent = "quality-mgr"`; `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py:29-33` read those names; no class-to-agent mapping exists). orchestration: not assessed in this draft.

## REQ-CORE-0008: Phase lead sets the agent at assign

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The package's task.assign hook MUST set the bead's assignee to the agent named in the request when the phase lead assigns.
- The package's task.assign hook MUST make that assignment as its one bead write.


### Rationale

Rand (2026-11-07): "At task assign, asignee should be set by phase-lead to agent-name."

### Success Criteria

**Acceptance Criteria:**

- [ ] Assigning an open unassigned bead to agent `A` leaves the bead with assignee `A` and exactly one recorded write.
- [ ] Assigning a bead already assigned to `A` to `A` writes nothing.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_t_assign_02_open_unassigned_writes_one_assign`
- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_t_assign_01_already_this_agent_passes_through`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:29-41`. State: lite implemented (those lines, those tests). orchestration: not assessed in this draft.

## REQ-CORE-0009: Follow-on task assigner copies dev assigner

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The assigner of every ATM task that reviews a dev task MUST equal the assigner of that dev task.
- The dev task's assigner MUST be read from the dev task's ATM task record.
- The reviewing task's assigner MUST be stored as the assigner of the reviewing ATM task.


### Rationale

Rand (2026-11-07): "for sanity and qa task assign, the assigner must be set based from what is read from the dev task assigner."

### Success Criteria

**Acceptance Criteria:**

- [ ] For a dev task assigned by `lead-a`, the follow-on QA assignment command carries `--as lead-a`.
- [ ] The assigner is read from the ATM task list output, not from the phase file.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:128` (`--as self.lead`), `plugins/atm-bd-orchestration/core/atm_bd_core/collect/atm.py:26` (`TaskFact` built from task_id, assignee, state only). State: lite not yet implemented (QA assignments use the phase file lead; the collected task facts carry no assigner). orchestration: not assessed in this draft.

## REQ-CORE-0010: Assigner is set at assign and at close

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The package's task.assign hook for a dev task MUST record the dev task's assigner as the assigner of its follow-on review task.
- The package's task.close hook for a dev task MUST perform the same assignment again.

**SHOULD statements:**

- The close-hook assignment SHOULD be a write only when the recorded assigner differs from the dev task's assigner.

**MUST NOT statements:**

- The close-hook assignment MUST NOT write a bead when the recorded assigner already equals the dev task's assigner.


### Rationale

Rand (2026-11-07): "This can occur at 'atm task assign <dev>' in an assign hook, AND it can also occur at the 'atm task close <dev-task>' hook ... doing it in both places would be prudent ... the 2nd close-hook assignment should do a write IF NOT correct. No need to actually write a bead to db w/ redundant data."

### Success Criteria

**Acceptance Criteria:**

- [ ] After dev assign, the follow-on task's recorded assigner equals the dev assigner.
- [ ] A dev close with a correct recorded assigner produces no assigner write.
- [ ] A dev close with a wrong recorded assigner writes the correct one.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/hooks/task-assign.md:3` (one write: the assignee), `plugins/atm-bd-orchestration/skills/atm-bd-lite/hooks/task-close.md:3` (close hook assigns nothing); `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:86-90`. State: lite not yet implemented in either hook. Conflict with existing lite docs: task-close.md says the close hook assigns nothing and writes only the caller's own bead. Where the assigner is stored is not stated by the ruling; the owner must name it. orchestration: not assessed in this draft.

## REQ-CORE-0011: Messages go to the task assigner

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every completion report and escalation about a task MUST be sent to the assigner read from that ATM task.

**MUST NOT statements:**

- A completion report or escalation MUST NOT be addressed to the phase file's `lead` when the task's assigner differs.


### Rationale

Rand (2026-11-07): messages go to the task's assigner, read from the ATM task. Rand: "sometimes lead transitions mid phase (i.e. out of tokens)".

### Success Criteria

**Acceptance Criteria:**

- [ ] For a task assigned by `lead-b` while the phase file names `lead-a`, the completion message is addressed to `lead-b`.
- [ ] After the assigner changes by reassignment, the next message goes to the new assigner.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:131-134` (Report goes to `self.recipient(self.lead)`), `plugins/atm-bd-orchestration/core/atm_bd_core/tick.py:104`. State: lite not yet implemented (Reports go to the phase file lead; `TaskFact` has no assigner). orchestration: not assessed in this draft.

## REQ-CORE-0012: Pre-claim checks run in task.start

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The package's task.start hook MUST check that `bd ready` lists the bead before the claim.
- The package's task.start hook MUST run the git checks after the `bd ready` check.
- The package's task.start hook MUST allow the start only when both checks pass.

**MUST NOT statements:**

- The package's task.start hook MUST NOT claim the bead when either check fails.


### Rationale

Rand (2026-11-07): pre-claim checks belong in the task.start hook: "check bd ready -> git checks -> atm-open returns true otherwise atm-open returns false and lead is notified".

### Success Criteria

**Acceptance Criteria:**

- [ ] A bead absent from `bd ready` is refused and not claimed.
- [ ] A bead that passes both checks starts.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-start-hook.py:20-39` (checks assignee and open blockers only). State: lite not yet implemented (no `bd ready` check, no git check, no `atm-open` result). The term `atm-open` has no definition or use anywhere in either repository's history searched. Conflict with existing lite docs: ANC-066 (atm-core `docs/plans/phase-bo/anchors.json`) forbids a subprocess in a lite hook, and hooks/task-start.md says the hook does not read the ledger. orchestration: not assessed in this draft.

## REQ-CORE-0013: Assigner is notified when a start is refused

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- When the task.start hook refuses a start, the package MUST notify the task's assigner with the failed check.


### Rationale

Rand (2026-11-07): "...otherwise atm-open returns false and lead is notified".

### Success Criteria

**Acceptance Criteria:**

- [ ] A start refused by a failed pre-claim check produces one message to the lead naming the bead and the failed check.

### Implementation Notes

Sources: none. State: lite not yet implemented (no notification path exists in `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-start-hook.py`). orchestration: not assessed in this draft.

## REQ-CORE-0014: QA findings are always created

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A QA task that finds a defect MUST create a finding bead for it.
- A QA task MUST pour each finding before closing with a FINDINGS verdict.

**MUST NOT statements:**

- A package rule MUST NOT stop QA from creating findings.


### Rationale

Rand (2026-11-07): findings are always created ("refusing to create findings does NOT sound like a useful thing to do").

### Success Criteria

**Acceptance Criteria:**

- [ ] The QA template contains a pour block that creates every listed finding.
- [ ] A FINDINGS close whose findings are not poured is refused.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_t_close_04_finding_bead_missing`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/templates/qa.xml.j2:30-46`, `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:57-80`. State: lite implemented (those lines; test). orchestration: not assessed in this draft.

## REQ-CORE-0015: More than three QA rounds escalate

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- When a bead's QA has run more than 3 rounds, the package MUST send the task's assigner a message asking it to deploy an architect to find why the rounds are not converging.


### Rationale

Rand (2026-11-07): more than 3 QA rounds "should excelate to lead w/ a message having the lead deploy an architect to see why this isn't converging".

### Success Criteria

**Acceptance Criteria:**

- [ ] A fourth QA round on one bead produces exactly one message to the lead requesting an architect.
- [ ] Three rounds produce no such message.

### Implementation Notes

Sources: none (`grep -rn round plugins/atm-bd-orchestration/skills/atm-bd-lite/ plugins/atm-bd-orchestration/core/atm_bd_core/` finds nothing). State: lite not yet implemented (no round counter exists). orchestration: not assessed in this draft.

## REQ-CORE-0016: Round-cap escalation never halts the phase

**Status:** Draft  
### Requirement Statement

**MUST NOT statements:**

- The round-cap escalation MUST NOT instruct anyone to stop all work.
- The round-cap escalation MUST NOT notify the user.


### Rationale

Rand (2026-11-07): escalation goes to the lead; no "stop everything and notify user" language.

### Success Criteria

**Acceptance Criteria:**

- [ ] The escalation text names the lead and the architect request and contains no instruction to stop work or notify the user.

### Implementation Notes

Sources: `grep -rn "stop everything" plugins/atm-bd-orchestration/skills/atm-bd-lite/ plugins/atm-bd-orchestration/core/atm_bd_core/` finds nothing. State: lite implemented vacuously (no such text exists, because no escalation exists yet). orchestration: not assessed in this draft.

## REQ-CORE-0017: One evaluate and notify path per package

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Each package MUST have exactly one function that evaluates the phase and sends its notifications.
- The package's cron entry and its console MUST both call that function.


### Rationale

Rand (2026-11-07): one evaluate/notify path per package, "regardless of whether cron or console calls it".

### Success Criteria

**Acceptance Criteria:**

- [ ] The cron entry and the console `cron` command both reach `tick`; no second code path sends Reports or Assigns.
- [ ] A console dry run and a cron dry run produce the same decision for the same facts.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/install/test_profile_install.py::test_cron_tick_passes_profile_phase_and_primary`
- `apps/atm-bd-console/tests/test_monitor.py::test_cron_dry_run_never_sends_and_live_tick_sends_only_decided_action`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/cron_entry.py:17-26`, `apps/atm-bd-console/src/atm_bd_console/monitor.py:251-257,415-452`. State: lite implemented (both call `atm_bd_core.tick.tick`). orchestration: not assessed in this draft.

## REQ-CORE-0018: Notifications come from the tool identity

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every notification the package sends MUST be sent as the configured tool identity `<identity>@<team>`.

**SHOULD statements:**

- The tool identity SHOULD default to `atm-bd@tool` when none is configured.


### Rationale

Rand (2026-11-07): "the notification sender is the configured tool identity". The console already reads `tool_identity` (REQ-CON-0001).

### Success Criteria

**Acceptance Criteria:**

- [ ] With `tool_identity: notify@automation` configured, a Report is sent `--as notify --team automation`.
- [ ] With none configured the sender is `atm-bd@tool`.

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:133,137,140` (hard-coded `--as atm-bd --team tool`), `apps/atm-bd-console/src/atm_bd_console/config.py:183-194`. State: lite not yet implemented (the executor ignores the configured value). orchestration: not assessed in this draft.

## REQ-CORE-0019: Executor sends each action key once

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The executor MUST drop a repeated action key within one tick.
- The executor MUST run an Assign or Notify key at most once while the plug-in still decides it.

**MUST NOT statements:**

- The executor MUST NOT re-send a Report whose key is in `reported-keys.json`.


### Rationale

Commit aec7860b4 (2026-11-02, Complete unattended lite workflow) and tests record that each action runs once; a sent Report stays visible as a row.

### Success Criteria

**Acceptance Criteria:**

- [ ] Two equal keys in one decision execute one command.
- [ ] A second tick after a sent Assign executes nothing.
- [ ] A sent Report becomes a row on the next tick and is not re-sent.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_duplicate_keys_in_one_decide_execute_once`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_released_qa_bead_is_assigned_once_and_deduped_next_tick`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_missing_params_report_goes_to_the_lead_once_then_stays_a_row`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:88-105`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0020: Failed commands retry three times

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The executor MUST retry a failed command on the next tick.
- After 3 failed attempts the executor MUST stop running that key.
- After 3 failed attempts the executor MUST report the key FAILED on every tick with the last typed error id until the plug-in stops deciding it.

**SHOULD statements:**

- The executor SHOULD type a failure only when its output contains a whole-token error id.


### Rationale

Docstring of `execute.py` and commit 5a5547422 (2026-11-03, Match whole ErrorId tokens in command failures) record the retry limit and whole-token typing.

### Success Criteria

**Acceptance Criteria:**

- [ ] Three refusals are retried on three ticks; the fourth tick runs no command and reports the retry limit.
- [ ] Output without an error id types as REQUEST_INVALID; success clears the count.
- [ ] An id inside a larger token does not type.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_failed_assign_is_retried_next_tick_then_reported_with_its_error_id`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_failure_without_an_error_id_is_request_invalid_and_success_clears_the_count`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_error_id_substring_inside_larger_token_is_not_typed`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:27,174-178,202-207`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0021: Executed ledger persists after each command

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The executor MUST write `executed.json` atomically after every command.
- The executor MUST remove ledger keys the plug-in no longer decides only when the collected facts were complete.
- Loading an unreadable `executed.json` MUST refuse with PHASE_UNREADABLE before any read.


### Rationale

Commits 322231234 and 1710599c4 (2026-11-02) persist the ledger per command and preserve it on incomplete facts, so a crash or degraded read neither re-sends nor forgets.

### Success Criteria

**Acceptance Criteria:**

- [ ] An exception on the second command leaves the first command's key in `executed.json`.
- [ ] A tick with unreadable ready facts leaves `executed.json` unchanged.
- [ ] A corrupt `executed.json` refuses before the collector runs.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_completed_assign_is_persisted_before_a_later_command_raises`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_degraded_ready_facts_preserve_sent_keys_and_failure_counts`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_corrupt_executed_state_refuses_before_any_read`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_a_key_decide_stops_returning_is_forgotten_and_assigned_again_when_re_released`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:53-85,152-165`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0022: Unreadable report ledger holds reports

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- When `reported-keys.json` is unreadable the executor MUST hold every Report and return PHASE_UNREADABLE for it.

**MUST NOT statements:**

- The executor MUST NOT overwrite an unreadable `reported-keys.json`.


### Rationale

`execute.py` states a Report is held so it is not sent twice.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `{not json` in `reported-keys.json`, no command runs and the file is unchanged.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_unreadable_reported_keys_hold_reports_instead_of_resending`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:170-173`, `plugins/atm-bd-orchestration/core/atm_bd_core/reported.py:16-28`. State: lite implemented (those lines; test). orchestration: not assessed in this draft.

## REQ-CORE-0023: Dry run executes and writes nothing

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A dry-run tick MUST return the decided actions with outcome DRY_RUN.

**MUST NOT statements:**

- A dry-run tick MUST NOT run a command.
- A dry-run tick MUST NOT write any state file.
- Console, queues and snapshot MUST NOT execute actions.


### Rationale

The console and queues render a preview of the cron decision; only cron sends.

### Success Criteria

**Acceptance Criteria:**

- [ ] A dry-run tick leaves `.atm-bd/state` absent and the runner's call list empty.
- [ ] `atm-bd queues` and `snapshot` call the tick with `dry_run=True`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_dry_run_executes_nothing_and_writes_no_state`
- `apps/atm-bd-console/tests/test_monitor.py::test_cron_dry_run_never_sends_and_live_tick_sends_only_decided_action`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:184-189`, `monitor.py:357-359,366,404`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0024: Tick drains the cache journal first

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A live tick MUST drain the bead-cache journal before it collects facts.
- A live tick MUST report each escalated journal write to the lead as BEAD_RACED or CACHE_UNAVAILABLE.
- A live tick MUST mark an escalation announced only after its Report was sent or already recorded.


### Rationale

`tick.py` drains before collection so hook-journaled writes are applied before decisions are made.

### Success Criteria

**Acceptance Criteria:**

- [ ] Event order is drain, collect, announce.
- [ ] A `BD_CACHE.PRECONDITION` escalation reports BEAD_RACED.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_tick_drains_before_collection_and_reports_escalated_race`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/tick.py:76-93,108-111`. State: lite implemented (those lines; test). orchestration: not assessed in this draft.

## REQ-CORE-0025: Tick refuses bad configuration before reading

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A tick MUST refuse before any fact read when the profile, policy, cron script, phase file or ledger does not load.
- A tick MUST refuse a phase file whose profile differs from the profile manifest's name with PROFILE_MISMATCH.
- A tick MUST refuse a failed plug-in decision before it executes or writes state.


### Rationale

ANC-027 (atm-core phase-bo anchors, 2026-10-31): each tick takes the profile from the phase file and refuses when it is not its own.

### Success Criteria

**Acceptance Criteria:**

- [ ] The collector is never called in each refusal case.
- [ ] A decide that returns a non-list or a non-action raises and no state is written.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_phase_file_for_another_profile_refuses_before_any_read`
- `plugins/atm-bd-orchestration/core/tests/tick/test_profile.py::test_tick_refuses_policy_bad_params_before_collecting`
- `plugins/atm-bd-orchestration/core/tests/tick/test_tick.py::test_decide_failure_refuses_before_executing_or_writing_state`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/tick.py:55-73,85-89`, `plugins/atm-bd-orchestration/core/atm_bd_core/profile.py:68-153`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0026: Profile and policy files are validated

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Loading a profile MUST refuse with PROFILE_MISMATCH when its manifest is malformed, names an unknown key, or names a hook, template, policy or cron file that does not exist.
- Loading a policy MUST refuse with POLICY_BAD_PARAMS when it is missing, malformed, or has a param that is neither an integer nor a string.
- Loading a policy MUST refuse with PROFILE_MISMATCH when its `profile` key differs from the manifest's name.

**MUST NOT statements:**

- Shared framework source MUST NOT name a profile.


### Rationale

ANC-061 and the framework/plug-in boundary of phase bo (atm-core `docs/plans/phase-bo/design/lite-and-core.md`).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each refusal case returns the named error id.
- [ ] No file under `core/atm_bd_core` contains the words `lite` or `orchestration`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/tick/test_profile.py::test_bad_profile_refuses_profile_mismatch`
- `plugins/atm-bd-orchestration/core/tests/tick/test_profile.py::test_bad_policy_refuses_policy_bad_params`
- `plugins/atm-bd-orchestration/core/tests/tick/test_profile.py::test_policy_naming_another_profile_refuses_profile_mismatch`
- `plugins/atm-bd-orchestration/core/tests/tick/test_profile.py::test_host_source_names_no_profile`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/profile.py:68-153`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0027: Hooks ignore tasks outside the phase

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every package task hook MUST return not-applicable for a task that is not a phase task.
- Every package task hook MUST refuse a phase file that is unreadable (PHASE_UNREADABLE) or names another profile (PROFILE_MISMATCH).


### Rationale

ANC-026 (2026-10-31): the hook takes the profile from the phase file and refuses when it is not its own.

### Success Criteria

**Acceptance Criteria:**

- [ ] Non-phase tasks return not-applicable with no bead read.
- [ ] A phase file of another profile is refused.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_not_a_phase_task_is_not_applicable`
- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_phase_unreadable_and_profile_mismatch`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_not_a_phase_task`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:16-19`, `atm-bd-task-start-hook.py:16-19`, `atm-bd-task-hook.py:16-19`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0028: Only the assignee starts or closes

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The package's task.start hook MUST refuse a caller who is not the bead's assignee with TASK_NOT_ASSIGNEE.
- The package's task.close hook MUST refuse a caller who is not the bead's assignee with TASK_NOT_ASSIGNEE.
- The task.close hook MUST accept a close by the phase lead where a package record grants the phase lead that close.


### Rationale

Hook specs `task-start.md` and `task-close.md` (atm-core commit 39f9c8c1d, 'phase-bo: hook specs (Rand's edits: --vars, REQUEST_INVALID, QA verdict shape)').

### Success Criteria

**Acceptance Criteria:**

- [ ] A start or close by a different agent is refused and writes nothing.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_caller_not_assignee`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_caller_not_assignee`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-start-hook.py:22-23`, `atm-bd-task-hook.py:22-23`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0029: Hook writes are guarded and single

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every package task hook MUST make at most one bead write.
- Every package task hook MUST write with a guard that returns BEAD_RACED when the bead changed since it was read.

**MUST NOT statements:**

- A package task hook MUST NOT write the stack bead.
- A package task hook MUST NOT create a bead.


### Rationale

ANC-064 and ANC-065 (2026-11-01): a hook makes at most one beads-cache write and never writes the ledger.

### Success Criteria

**Acceptance Criteria:**

- [ ] A raced write yields BEAD_RACED with one attempted write.
- [ ] No hook call passes the stack bead to a write.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_t_start_01_raced_write_is_bead_raced`
- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_t_assign_02_raced_write_is_bead_raced`
- `plugins/atm-bd-orchestration/tests/lite/test_task_close.py::test_close_never_writes_the_ledger_or_assigns`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-hook.py:86-90`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0030: Open blockers refuse assign and start

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The package's task.assign hook MUST refuse a bead with open blockers with BEAD_NOT_READY before it examines the bead's status.
- The package's task.start hook MUST refuse a bead with open blockers with BEAD_NOT_READY before it examines the bead's status.


### Rationale

Hook specs `task-assign.md` and `task-start.md`, flowchart node B (open blockers) precedes the transition.

### Success Criteria

**Acceptance Criteria:**

- [ ] A bead with blocker `b-dep` is refused with a message containing `b-dep`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_task_assign.py::test_open_blockers_before_status`
- `plugins/atm-bd-orchestration/tests/lite/test_task_start.py::test_open_blockers_before_status`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-task-assign-hook.py:26-27`, `atm-bd-task-start-hook.py:24-25`. State: lite implemented (those lines; tests). orchestration: not assessed in this draft.

## REQ-CORE-0031: Cron stops when the phase root closes

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The package's cron stop hook MUST return stop true with reason `phase closed` when the phase root bead is closed.
- The package's cron stop hook MUST return stop false when the root bead is not closed.


### Rationale

Comment in `cron_entry.py` cites ADR-069 D4: the phase root's closure is the mandatory atm-bd cron stop condition.

### Success Criteria

**Acceptance Criteria:**

- [ ] A closed root returns `{"stop": true, "reason": "phase closed"}`; an open root returns `{"stop": false}`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/install/test_profile_install.py::test_cron_stop_only_when_root_bead_is_closed`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/cron_entry.py:27-45`. State: lite implemented (those lines; test). orchestration: not assessed in this draft.

## REQ-CORE-0032: Installer registers hooks and cron

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- The installer MUST register every hook and the cron declared in the profile manifest through generated launchers.
- The installer MUST verify the registrations and fail when a registered hook is absent or differs.


### Rationale

Commits 0198f8866 and ca3a5c09e record that the installer registers all hooks and the phase cron and verifies them.

### Success Criteria

**Acceptance Criteria:**

- [ ] After install, each declared hook and the cron appear once in the ATM registration list.
- [ ] Reinstall reuses identical registrations.

**Test Evidence:**

- `plugins/atm-bd-orchestration/core/tests/install/test_profile_install.py::test_registers_each_declared_hook_and_cron_with_runtime_launchers`
- `plugins/atm-bd-orchestration/core/tests/install/test_profile_install.py::test_install_fails_when_registered_hook_is_absent`
- `plugins/atm-bd-orchestration/core/tests/install/test_profile_install.py::test_reinstall_reuses_venv_and_identical_active_hooks_and_cron`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/core/atm_bd_core/install/`. State: lite implemented (installer and tests). orchestration: not assessed in this draft.

## REQ-CORE-0033: Assignment variables render strictly

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every Assign action's variables MUST equal the set the target template declares in `required_variables`.
- Every dispatch template MUST render under `sc-compose render --strict` with those variables.


### Rationale

Commit 6c08ff5a8 (Render lite templates from action vars) established strict rendering of action vars.

### Success Criteria

**Acceptance Criteria:**

- [ ] For each stage, the provided variable set equals the declared set and strict render exits 0.

**Test Evidence:**

- `plugins/atm-bd-orchestration/tests/lite/test_cron.py::test_decision_vars_strictly_render_assignment`

### Implementation Notes

Sources: `plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/atm-bd-cron.py`, `plugins/atm-bd-orchestration/core/atm_bd_core/execute.py:119-130`. State: lite implemented (tests). orchestration: not assessed in this draft.

## REQ-CORE-0034: Bead access goes through bd-cache

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every atm-bd script, hook, template and agent instruction that reads or writes a bead MUST do so through bd-cache.

**MUST NOT statements:**

- An atm-bd script, hook, template or agent instruction MUST NOT invoke `bd` directly to read or write a bead.


### Rationale

Rand (2026-11-08): "everything in atm-bd (including agent 'bd' instructions) need to use bd-cache". Rand (2026-11-08): "the bd-cache should be the source of truth for the phase" and "changes must align w/ beads-cache api"; its reads and writes match the bd JSON API as closely as possible.

### Success Criteria

**Acceptance Criteria:**

- [ ] A search of the package's skills, agents, templates and scripts finds no direct `bd` read or write outside bd-cache.

### Implementation Notes

State: not yet implemented. On 2026-11-08, 236 lines under `plugins/atm-bd-orchestration/skills` and `agents` invoke `bd show|list|ready|update|close|create` directly. Bead create (finding pour) waits on beads-cache journaled create (randlee/beads-cache #104).

## REQ-CORE-0035: Task facts come from ATM task queries first

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A component that needs a task's assigner, assignee or state MUST read it from an `atm task` query.
- A component MUST use the phase file's value only when the ATM task does not carry it.


### Rationale

Rand (2026-11-08): "I would like all of atm-bd to move toward getting information from existing 'atm task' queries w/ fallback of atm-bd config."

### Success Criteria

**Acceptance Criteria:**

- [ ] With a task whose assigner differs from the phase file's `lead`, the component uses the task's assigner.
- [ ] With a task that has no assigner, the component uses the phase file's `lead`.

### Implementation Notes

State: not yet implemented; close hooks and the console route by the phase file's `lead` today.

## REQ-CORE-0036: CLI tools resolve context from the launch folder

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Every atm-bd CLI tool MUST take its team, identity, phase and configuration from the repository or folder it was launched from.

**MUST NOT statements:**

- An atm-bd CLI tool MUST NOT take its team, identity, phase or configuration from the caller's environment.


### Rationale

Rand (2026-11-08): "the original 'use ATM_TEAM' became a problem when orchestrator omega-prime@hermes became infolved. all atm-bd cli tools should get all info from repo/folder it was launched from." This reverses ADR-066 and phase-bi ANC-042/043 (2026-10-18), which allowed `ATM_TEAM` to select the team.

### Success Criteria

**Acceptance Criteria:**

- [ ] Run from an atm-dev checkout with `ATM_TEAM=hermes` and `ATM_IDENTITY=omega-prime`, each CLI tool acts on team atm-dev with the identity the folder's configuration names.

### Implementation Notes

State: partly implemented (console `phase_caller`). Environment reads remain at `assignment-gates.py:242-243`, `atm-task-close.py:149-151,160`, `sanity-stack-link:532-534,561`, `core/atm_bd_core/execute.py:147`, `tick.py:33-39`, `collect/atm.py:16-26`.

## REQ-CORE-0037: Skills require updating the phase lead on a change

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- Each package's skill MUST state that the phase file's `lead` must be updated when the phase lead changes during a phase.


### Rationale

Rand (2026-11-08): "There should be a note in the skills that the atm-bd config file naming phase-lead MUST be updated if there is a change mid-sprint." The phase file is the fallback when an ATM task carries no assigner (REQ-CORE-0035).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each package's SKILL.md contains the instruction to update the phase file's `lead` on a lead change.

### Implementation Notes

State: not yet implemented in either skill.

## REQ-CORE-0038: Dev assignments do not render the assignee identity

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A dev agent MUST take its identity from its own session (`ATM_IDENTITY`), not from its assignment text.

**MUST NOT statements:**

- A dev assignment MUST NOT render the assignee's identity into its body.


### Rationale

Rand (2026-11-07): rendering the assignee identity into the assignment "is fine for quality-mgr/sanity, NOT ok for dev". Review assignments may render it.

### Success Criteria

**Acceptance Criteria:**

- [ ] A rendered dev assignment contains no assignee identity.
- [ ] A dev agent's claim uses `--actor "$ATM_IDENTITY"` (REQ-CORE-0006).

### Implementation Notes

State: to verify per dev template.

## REQ-CORE-0039: bd-cache is the phase's source of truth

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- bd-cache MUST be the source of truth for a phase's beads.
- Every bead need atm-bd has that bd-cache does not meet MUST be filed as a beads-cache requirement and consumed through the beads-cache API.
- atm-bd's bead reads and writes MUST use the bd JSON shapes that beads-cache returns.

**MUST NOT statements:**

- atm-bd MUST NOT add its own bead storage, cache or write layer.


### Rationale

Rand (2026-11-08): "I expect that the cache matches the bd api as closely as possible (json)." "I would expect changes 'from upstream' to be rare. The bd-cache should be the source of truth for the phase." "beads-cache (rust daemon using tokio is already in development based on requirements coming from atm-bd) and changes must align w/ beads-cache api."

### Success Criteria

**Acceptance Criteria:**

- [ ] No atm-bd module stores bead state outside bd-cache.
- [ ] Bead create used by atm-bd is a beads-cache operation (randlee/beads-cache #104).

### Implementation Notes

State: bead create waits on beads-cache #104. Related: REQ-CORE-0034.

## REQ-CORE-0040: Requirements are shared or package-specific

**Status:** Draft  
### Requirement Statement

**MUST statements:**

- A requirement or ADR that applies to every atm-bd package MUST live in the shared files (`docs/requirements/core.md`, `docs/adr/adr-core.md`).
- A requirement or ADR that applies to one package MUST live in that package's files.
- Which packages implement a shared record MUST be stated only in its Implementation Notes.

**MUST NOT statements:**

- A requirement or ADR statement MUST NOT condition on which package runs.


### Rationale

Rand (2026-11-07): "I expect a lot of requirements will be the same for both atm-bd-lite and atm-bd-orch. make sure the requirements/ADR are partitioned so common requirements are in one place, specific req/adr in package-specific location. Do NOT write requirements with IF orch ELSE lite in them. I expect we will write dozens of packages and they should have shared or individual req/adr, not hybrid."

### Success Criteria

**Acceptance Criteria:**

- [ ] No statement in `docs/requirements` or `docs/adr` names a package as a condition.

### Implementation Notes

State: core.md and lite.md partitioned; the older orchestration files still hold shared rules (to move).
