# atm-task-close (close hook)

**ID Range:** REQ-TCH-0001 through REQ-TCH-0021  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-19  
**Last Updated:** 2026-11-05  
**Owner:** Rand Lee  

---

## REQ-TCH-0001: Contract

**Status:** Draft  
### Requirement Statement

One script, `atm-task-close.py --role <dev|fix|sanity|qa> --vars <file> [--result <file>]`, is the only way a dev, fix, sanity or QA task completes. The agent never runs `bd close` or `atm task close ... completed` by hand for those roles.


### Rationale

Without a single completion path, each agent assembled close vars and ran `bd close` and `atm task close` by hand; the 0.19.x changelog records that close-vars context is now "seeded from the bead graph, never hand-stuffed" (#825, #671). The dev template's closing step routes every dev completion through this script and forbids closing the bead or task by hand.

### Success Criteria

**Acceptance Criteria:**

- [ ] `scripts/atm-task-close.py --role other --vars /absent` exits 1 with an `err` of code `ARGS.INVALID`, and `--role` accepts only `dev`, `fix`, `sanity` and `qa`.
- [ ] `templates/dev-template.xml.j2` step g tells the dev to complete through `atm-task-close.py --role dev --vars <file> --result <file>` and ends with "Do not close the completed bead or task by hand."
- [ ] A hook run for each of `dev`, `fix`, `sanity` and `qa` performs that role's `bd close` and `atm task close` itself (the recorded write sequence contains both).

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_argument_errors_use_typed_json`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_each_role_command_order_and_identity`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0002: Contract

**Status:** Draft  
### Requirement Statement

For dev and fix, the lead writes an immutable close-dispatch JSON file containing the role's `required_variables_by_role` from `task-close-vars.j2`; this is a separate file from the dev/fix assignment template's render vars. The agent passes it unchanged as `--vars` and supplies a mandatory `--result` JSON file containing only its role's `result_variables_by_role`. The files must not overlap. Matching examples are `examples/task-close-vars-{dev,fix}.json` and `examples/task-close-result-{dev,fix}.json`. The hook derives `commit`, `pr_number`, `pr_url`, `rebased_onto` and `generated_at`; the caller types none of them. Sanity and QA keep a single `--vars` file. The shared header declares exact `render_variables_by_role` sets (required plus result); the hook strictly renders only those actual fields, with no other-role placeholders. Missing or unknown fields fail before live checks; non-empty derived identity is checked after derivation and before writes.
   The lead supplies `stack_bead`, the stack ledger bead ID, in the vars file.


### Rationale

The lead's dispatch file used to be required to carry completion values (commit, pr_number, pr_url, rebased_onto) that only exist after the work, so the hook refused the lead's immutable file with `VARS.MISSING` (commit 9ff31da54, fixes #485). Splitting a dispatch file from the fixer's `--result` file, and deriving the rest, removes hand-typed completion fields.

### Success Criteria

**Acceptance Criteria:**

- [ ] For `--role dev` and `--role fix` without `--result`, the hook returns `ARGS.INVALID` and runs no command.
- [ ] A dispatch file containing a result field (`outcome`) is refused with `VARS.INVALID` naming that field, and no command runs.
- [ ] A result file containing a field that is not in the role's `result_variables_by_role` (`resolution_md` for dev) is refused with `VARS.UNKNOWN`, and no command runs.
- [ ] Given `examples/task-close-vars-<role>.json` and `examples/task-close-result-<role>.json`, a dev or fix close succeeds, the sanity assignment carries `commit`, `pr_number`, `pr_url`, `rebased_onto` and `generated_at` derived from git and the open PR, and both input files are byte-identical afterwards.
- [ ] For each role, removing any one field in `required_variables_by_role` or `result_variables_by_role` from the inputs gives `VARS.MISSING` before any command runs.
- [ ] The set of fields passed to the `task-close-vars.j2` render equals the role's required plus result fields.
- [ ] The stack bead read is the one named by `stack_bead` in the vars file.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_close_from_documented_dispatch_and_result_files_derives_handoff`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_fixer_fields_in_the_dispatch_file_are_refused_before_commands`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_result_file_rejects_fields_that_are_not_its_role_fields`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_and_fix_close_require_a_result_file`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_every_role_required_field_is_validated_before_commands`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_shared_render_uses_exact_role_fields_without_union_placeholders`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_stack_bead_id_comes_from_dispatch_vars`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0003: Contract

**Status:** Draft  
### Requirement Statement

The result is JSON on stdout and stderr, `{"ok": {...}}` or `{"err": {"code", "message", "fix"}}`, and the exit code mirrors it. Every `err` names the exact fix; there is no separate ledger.


### Rationale

A caller that is an agent needs to branch on a machine-readable result and be told the repair, not read a traceback; the 0.19.x changelog records timeout and config failures turned into typed errors "each naming the value and the fix, never a traceback". The hook keeps no separate ledger, so the result itself must carry the remedy.

### Success Criteria

**Acceptance Criteria:**

- [ ] An invalid invocation writes the same JSON document to stdout and stderr, parseable as `{"err": {...}}` with code `ARGS.INVALID`, and the process exits 1.
- [ ] A refused `outcome` returns an `err` whose keys are exactly `code`, `message` and `fix`, and `fix` names the file and the value to set.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_argument_errors_use_typed_json`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_bad_result_outcome_names_field_value_and_allowed_values_before_commands`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0004: Contract

**Status:** Draft  
### Requirement Statement

Commands that need the lead's authority (`atm task assign`) run with `ATM_IDENTITY=<lead>` and `ATM_TEAM=<team>` set on that one subprocess, `lead` from `.atm-bd/phase-<x>.toml` and the team from `.atm.toml`. Every other `bd` and `atm` write runs as the caller: `bd` writes carry `--actor "$ATM_IDENTITY"`, and `atm` writes take `ATM_IDENTITY` from the environment.


### Rationale

Only the lead may assign tasks, but borrowing the lead's identity for every command would attribute dev, sanity and QA writes to the wrong agent. The hook scopes the lead identity to the one subprocess that needs it, and the test asserts the hook leaves its own environment unchanged.

### Success Criteria

**Acceptance Criteria:**

- [ ] In a dev close, every `atm task assign` and `atm hook list` subprocess environment has `ATM_IDENTITY` equal to the lead and `ATM_TEAM` equal to the phase team; every other subprocess has the caller's `ATM_IDENTITY`.
- [ ] Every `bd` write in the recorded sequence ends with `--actor <caller>`.
- [ ] The hook's own `os.environ` is identical before and after the run.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_each_role_command_order_and_identity`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_handoff_is_immediate_and_closes_the_dev_task_as_the_dev`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0005: Contract

**Status:** Draft  
### Requirement Statement

`--skip-checks` skips the PR and stack checks only, never vars validation, derived identity validation or state writes. It appears only in `--help`: "skips the PR and stack checks. Do NOT use without permission from the phase lead." No template names it. Dev/fix still derive a non-empty HEAD and require non-empty `pr_number` and `pr_url` recorded on the checked bead before writing; an empty identity is `VARS.EMPTY` with remediation.


### Rationale

The close needs a lead-authorized escape from the PR and stack checks, but the escape must not let an empty commit or PR identity reach the bead. The flag was added with the centralized role closes (commit 32e475caf); its help text is the only place it is named so agents do not reach for it unprompted.

### Success Criteria

**Acceptance Criteria:**

- [ ] `atm-task-close.py --help` prints "skips the PR and stack checks. Do NOT use without permission from the phase lead."
- [ ] `grep -rl skip-checks templates SKILL.md roles` under `skills/atm-bd-orchestration` lists no file.
- [ ] With `--skip-checks` and an empty `git rev-parse HEAD`, the hook returns `VARS.EMPTY` naming `commit` and writes nothing.
- [ ] With `--skip-checks` or GitHub unreachable, a bead lacking recorded `pr_number` or `pr_url` returns `VARS.EMPTY` naming the field, with a `fix` containing "record", and writes nothing.
- [ ] With `--skip-checks`, no `gh` command runs, and the sanity assignment carries the recorded `pr_url`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_help_describes_the_permission_only_override`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_empty_derived_commit_never_writes_even_when_checks_are_skipped`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_offline_or_skipped_checks_require_recorded_pr_identity`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_skipped_checks_preserve_recorded_pr_identity`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0006: Contract

**Status:** Draft  
### Requirement Statement

GitHub unreachable or rate limited falls back to local git (the pushed head is on `origin/<branch>`, `origin/<current stack top>` is an ancestor of it (or `origin/<pr_target>` when the ledger is empty)). The hook uses the checked bead's recorded PR identity, records `github: unavailable`, and sanity and QA proceed only when that identity is non-empty. Missing recorded PR number or URL is `VARS.EMPTY` before any write, naming the required repair. The lead owns stack hygiene.


### Rationale

When GitHub could not be reached the close result said only `github: unavailable`; commit 5e856916a made it name the failed command and stderr so the fallback says why it was taken. The fallback must not invent PR identity, so it uses only what is recorded on the checked bead.

### Success Criteria

**Acceptance Criteria:**

- [ ] When `git ls-remote`, `git fetch` or `gh api` fails, the command is attempted 3 times and the result has `github` equal to `unavailable`.
- [ ] On fallback the hook runs `git merge-base --is-ancestor origin/<ledger top branch> <commit>` locally.
- [ ] The fallback result's `github_error` names the failed command and its stderr; a successful GitHub run has `github` equal to `ok` and no `github_error`.
- [ ] With GitHub down and `pr_number` or `pr_url` unrecorded, the hook returns `VARS.EMPTY` before any write, and a recorded PR base below the ledger top returns `BASE.PR_UNVERIFIED`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_remote_git_failures_retry_then_use_cached_local_checks`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_remote_git_fallback_names_the_failed_command_and_stderr`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_github_fallback_names_the_failed_api_call_and_error`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_github_ok_result_carries_no_github_error`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_offline_or_skipped_checks_require_recorded_pr_identity`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_offline_pr_base_below_linked_top_is_refused`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0007: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Draft  
### Requirement Statement

Checks, in order: merge and strictly validate dispatch/result vars (2); derive non-empty HEAD and the UTC generation time; the worktree is clean and HEAD is the pushed head on `origin/<branch>`; the current top from the stack bead's `layers` (its `pr_target` when the ledger is empty) is an ancestor of HEAD, read locally, deriving `rebased_onto`; exactly one open PR exists for `branch` with HEAD as its head (when GitHub is reachable), deriving its number and URL. No match is `PR.NOT_FOUND`; multiple matches are `PR.AMBIGUOUS`, never arbitrary selection. The PR base is retargeted by linking, so the hook does not check it. Finally require non-empty commit, PR number and URL before any bd/atm write, including permitted skipped-check and offline paths. Nothing else: not the whole stack, not lint or tests (the dev ran the gates before calling; sanity runs lint). The dev rebases onto the current top before every hook run, after a sanity FAIL or a rebase-required too. Result evidence records `ledger_top` and `pr_base` separately and reports differing branches; an empty ledger has no difference. Replay compares only the current assignment.


### Rationale

A close that does not verify the push, the clean tree, the stack top and the single open PR hands sanity a head that is not what the PR holds. Commits fix(task-close) 77e833858 (shared stack-top selection) and 9ff31da54 (derive HEAD, rebased_onto, PR) and the `ledger_top`/`pr_base` fields in the result record the checks as they are now run.

### Success Criteria

**Acceptance Criteria:**

- [ ] A wrong `git rev-parse HEAD` or `ls-remote` answer returns `HEAD.NOT_PUSHED`, a dirty `git status --porcelain` returns `HEAD.DIRTY`, a stack top that is not an ancestor of HEAD returns `BASE.NOT_ANCESTOR`, and an empty `gh api` pulls answer returns `PR.NOT_FOUND`; none of them writes.
- [ ] Two open PRs for the branch return `PR.AMBIGUOUS` with a `fix` naming the duplicate, and no write.
- [ ] A discovered PR whose number is `null`, `""` or `0` returns `VARS.EMPTY` naming `pr_number`, and no write.
- [ ] With two linked ledger layers the ancestor check runs against `origin/<last layer branch>` and never names the lower layer; the result records `ledger_top` and `pr_base` and a `base_difference` string when they differ.
- [ ] With a ledger-top-below PR base the hook returns `BASE.PR_UNVERIFIED` with a `fix` mentioning retargeting.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_preconditions_do_not_write`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_multiple_open_prs_at_head_are_refused_before_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_empty_discovered_pr_identity_is_refused_before_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_ledger_top_overrides_static_target`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_pr_base_below_linked_top_is_refused_before_writes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_github_ok_result_carries_no_github_error`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0008: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Draft  
### Requirement Statement

On pass, create ephemeral completion vars from dispatch plus result plus derived fields: `bd update <bead> --metadata '<full metadata JSON>'`, then `bd close <bead> --reason "dev complete at <sha>"` (`fixed at <sha>` for a fix). When a sanity assignment is due and none is already open, send the dev-complete or fix-complete report to the lead by plain `atm send --template` (not a task close) before `atm task assign <sanity member> --task-id <sanity bead> --template dev-sanity-template.xml.j2 --vars <completion file>` as the lead (4). `atm task assign` consumes `--vars` synchronously at assignment time; the file is not a path for the recipient to reopen. Delete the temporary completion files when the hook returns; persist nothing and never rewrite either input file. Report delivery is at least once: a retry after interruption before the assignment is recorded can send the report again. The hook then closes the dev's ATM task (21).


### Rationale

Commit 62cb1ad04 moved the dev task close to dev complete, after assigning sanity, so the dev gets its next queued task at once and no reminders fire on finished work. The completion vars are temporary because `atm task assign` consumes them synchronously.

### Success Criteria

**Acceptance Criteria:**

- [ ] The recorded write order for dev and fix is `bd update`, `bd close`, `atm send`, `atm task assign`, `bd update`, `atm task close`.
- [ ] The `bd close` reason is `dev complete at <sha>`.
- [ ] The `--vars` file named in `atm task assign` is `completion-vars.json`, it is not the lead's dispatch file, and it no longer exists once the hook returns.
- [ ] The dev task's last event is `complete` with outcome `completed`, and a second hook run does not close it again.
- [ ] A not_reproducible fix closes its dev task with reason `not reproducible: <evidence>`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_each_role_command_order_and_identity`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_handoff_is_immediate_and_closes_the_dev_task_as_the_dev`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_assignment_consumes_completion_vars_before_the_temporary_file_is_removed`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_rerun_after_the_task_is_closed_does_not_close_it_again`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_not_reproducible_fix_closes_its_task_with_the_evidence_reason`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0009: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Draft  
### Requirement Statement

The sanity bead is the group's: `metadata.sanity_bead` on the checked bead when present, else the open `stage:dev-sanity` bead whose `metadata.dev_bead` is the checked bead. None: `err` naming the lead, who creates it (team-lead 16).


### Rationale

The close must assign sanity on a bead the lead created at plan time; guessing or creating one would put sanity on the wrong bead. When neither lookup finds it, the hook returns `BEAD.NO_SANITY` so the lead creates it.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `metadata.sanity_bead` removed from the checked bead, the hook finds the open sanity bead whose `metadata.dev_bead` is the checked bead and succeeds.
- [ ] With neither present, the hook returns `BEAD.NO_SANITY`, its `fix` names the lead, and no write is made.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_lookup_fallback_and_actionable_missing_bead`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0010: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Draft  
### Requirement Statement

`not_reproducible` (fix only): the PR and head checks are skipped (nothing is pushed); the close reason is `not reproducible: <file:line>`; the hook sends the report before assigning sanity as in item 8, using the checked bead's branch and worktree and the checked worktree's HEAD for the sanity assignment. Sanity verifies the one deliverable, the absence at the cited line; QA's filing reviewer confirms it. No special close, no special assignment.


### Rationale

A fix that cannot reproduce a finding pushes nothing, so the PR and head checks have nothing to check; the tests show it still flows through the ordinary sanity handoff, with the base resolved from the PR target and the cited `file:line` verified.

### Success Criteria

**Acceptance Criteria:**

- [ ] A fix with outcome `not_reproducible` closes without a PR lookup and its sanity assignment has `nr` true, `base_source` equal to `pr_target`, and `base` resolved to a 40-hex commit.
- [ ] The sanity assignment's `branch`, `commit` and `worktree_path` equal the checked bead's branch and worktree and the checked worktree's HEAD.
- [ ] A cited `file:line` that does not exist returns `EVIDENCE.INVALID` naming it, with no write.
- [ ] The dev task close reason is `not reproducible: <evidence>`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_not_reproducible_dispatch_resolves_pr_target_to_commit`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_not_reproducible_uses_checked_worktree_and_its_head`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_not_reproducible_hook_verifies_the_cited_file_and_line`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_not_reproducible_fix_closes_its_task_with_the_evidence_reason`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0011: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Draft  
### Requirement Statement

Refused and cancelled closes do not go through the hook: `atm task close <id> refused --template task-refused.md.j2` as before (dev 5 and 16).


### Rationale

A refusal is not a completion and carries no commit or PR for the hook's checks. The dev and fix assignment templates keep refusals on `atm task close ... refused --template task-refused.md.j2`.

### Success Criteria

**Acceptance Criteria:**

- [ ] `atm-task-close.py --role` has no `refused` or `cancelled` value; `--role refused` returns `ARGS.INVALID`.
- [ ] `templates/dev-template.xml.j2` and `templates/fix-assignment.xml.j2` name `atm task close <id> refused --template task-refused.md.j2` as the refusal path.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_argument_errors_use_typed_json`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0012: Role dev and fix (`--role dev`, `--role fix`)

**Status:** Draft  
### Requirement Statement

After a pass the dev's task is closed and the dev starts its next queued task. A sanity FAIL re-assigns the same task id using the phase dev or fix assignment template; a rebase-required message means another layer took the top first: rebase onto the new top, push, run the hook again; `sanity_round` does not move.


### Rationale

The 0.19.x changelog (#467) records that the hook closes the dev task at dev complete so the dev can start its next queued task and no reminders fire on finished work. A sanity FAIL then re-assigns the same task id, and a rebase-required message reruns the hook without consuming a sanity round.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a successful dev run, the dev task's last event is `complete`.
- [ ] A sanity FAIL assigns the checked bead's same task id (`--task-id <checked bead>`) to its developer.
- [ ] After a `rebase-required` message and a reopened assignment, rerunning the hook at a new commit updates the same open sanity task: its last event is `assigned`, the checked bead's `commit` equals the new commit, and only one task exists for that sanity bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_handoff_is_immediate_and_closes_the_dev_task_as_the_dev`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_fail_message_contains_exact_undone_deliverables`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_rebase_required_rerun_updates_same_open_sanity_task`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0013: Role sanity (`--role sanity`)

**Status:** Draft  
### Requirement Statement

Sanity input is generated mechanically by sanity-close-vars from the split manifest, selected-vars.json and an optional stack result. It carries the selected verdict, pinned sha, checked bead, QA identity and selected undone deliverables with verbatim reasons. A PASS close does not require linking or a stack result: it closes first, then hands off to sanity-stack. A not_reproducible fix skips linking.


### Rationale

Hand-built sanity close vars were a recorded failure: the 0.19.x changelog (#671) says close-vars context "is seeded from the bead graph, never hand-stuffed" and (#821) that a sanity PASS could not be recorded until the lead hand-wrote `reviewers_round1`. `sanity-close-vars` builds them from the split manifest and the selected verdict. Closing before linking keeps a stack problem from blocking the verdict.

### Success Criteria

**Acceptance Criteria:**

- [ ] `scripts/sanity-close-vars` run on a manifest and a selected PASS result emits `verdict`, `commit` (the manifest's pinned sha), `deliverables_complete`, `carry_forward` and an empty `undone` list.
- [ ] For a FAIL, the emitted `undone` entries retain the reviewer's reason text verbatim.
- [ ] A pinned identity mismatch between manifest and selected result is rejected.
- [ ] A sanity PASS close does not update the stack bead before the sanity task close.
- [ ] A sanity PASS with no stack result closes the sanity bead.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_pass_builds_full_close_input_without_waiting_for_stack`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_fail_retains_verbatim_deliverable_reason_and_stack_result`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_sanity_close_vars.py::test_pinned_identity_mismatch_is_rejected`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_pass_closes_without_waiting_for_stack`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0014: Role sanity (`--role sanity`)

**Status:** Draft  
### Requirement Statement

PASS: `bd close <sanity bead> --reason "PASS at <sha>"`; the dev's task is already closed (21) and the dev-complete report was sent by the dev's hook; `atm task close <sanity bead> completed --template dev-sanity-complete.md.j2`; `atm task assign <qa member> --task-id <qa bead> --template qa-template.xml.j2 --vars <file>` as the lead, with `base` = the PR base, `commit`, `round`, and for a fix bead `carry_forward` = the fix bead.


### Rationale

The 0.19.x changelog (#821, #671) records QA and close context taken from the bead graph rather than copied from earlier vars; the PASS close likewise builds the QA assignment from the QA bead's current metadata and the live PR, not from stale vars.

### Success Criteria

**Acceptance Criteria:**

- [ ] A sanity PASS writes, in order, `bd close <sanity bead>`, `atm task close <sanity task> completed`, `atm task assign <qa member>`; the assign runs as the lead.
- [ ] The QA assignment's `layer`, `reviewers_round1` and `policy_path` equal the QA bead's current metadata, not the stale vars.
- [ ] For a fix bead the assignment's `carry_forward` equals the checked bead; the PR base and head are those of the current `gh pr view`.
- [ ] A dev task that is already closed is not closed again.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_each_role_command_order_and_identity`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_pass_qa_dispatch_uses_current_bead_values`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_pass_qa_dispatch_uses_current_pr_base_and_head`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_fix_pass_derives_carry_forward_from_checked_bead`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_pass_leaves_the_already_closed_dev_task_alone_then_assigns_qa`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0015: Role sanity (`--role sanity`)

**Status:** Draft  
### Requirement Statement

FAIL below the cap: append `sanity FAIL round <n> at <sha>:` and one numbered line per undone deliverable with the reviewer’s verbatim reason to the checked bead notes; reopen the checked bead retaining its assignee; set the sanity bead open and unassigned. Once those writes are applied, assign the checked bead’s same ATM task id to its developer using the phase dev or fix template and vars rebuilt from bead metadata and repository configuration. Close the sanity task. A pending journal write refuses with `BEADS.WRITE_PENDING` and a retry instruction; retry emits the assignment after writes apply. Re-closing the dev at a new sha assigns sanity again.


### Rationale

A FAIL must tell the dev exactly what was undone and put the work back with the same task id so the dev needs no new instruction; reopening retains the assignee so ownership does not move. The journaled-write retry (`BEADS.WRITE_PENDING`) came with the bd-cache close hooks (#557) so a write bd has not yet applied is applied once on rerun.

### Success Criteria

**Acceptance Criteria:**

- [ ] A sanity FAIL sets the checked bead notes to `sanity FAIL round <n> at <sha>:` followed by one `<number>. <reason>` line per undone deliverable, with the reasons verbatim.
- [ ] It reopens the checked bead, sets the sanity bead to `open` with an empty assignee, and issues exactly one `atm task assign` whose `--task-id` is the checked bead.
- [ ] It sends no `atm send` message and closes the sanity task.
- [ ] A write that bd does not take stays journaled and is applied once when the hook is rerun.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_fail_message_contains_exact_undone_deliverables`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_a_write_bd_does_not_take_stays_journaled_and_applies_once_on_rerun`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0016: Role sanity (`--role sanity`)

**Status:** Draft  
### Requirement Statement

FAIL exceeding the cap: `max_sanity_rounds` from the repo config (`.claude/project/atm-bd-orchestration.yaml`, rendered from `registry.yaml`), default 5. The hook reopens nothing: it sends the lead `SANITY.ROUND_CAP` with the undone deliverable numbers and closes the sanity task (FAIL). The dev's task stays closed until the lead rules.


### Rationale

Without a cap, a deliverable sanity keeps failing would loop between dev and sanity indefinitely. Commit c584443ed made the round-cap notice go to the lead once, and d067a0e08 kept the cap in force during dev replay.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `max_sanity_rounds` unset the cap is 5; with `max_sanity_rounds: 2` in the repo config it is 2.
- [ ] For FAIL rounds up to the cap the checked bead is reopened; the first FAIL beyond the cap returns `escalated` equal to `SANITY.ROUND_CAP`, leaves the checked bead closed, and leaves the sanity bead `in_progress`.
- [ ] Exactly one message containing `SANITY.ROUND_CAP` is sent, to the lead.
- [ ] Replaying the capped close sends no second notice.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_failure_cap_exceeds_limit_and_counts_distinct_assignments`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_round_cap_replay_sends_one_notice_and_does_not_increment_counter`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_replay_does_not_bypass_round_cap`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0017: Role sanity (`--role sanity`)

**Status:** Draft  
### Requirement Statement

CANNOT_RUN: as today (dev-sanity 31): bead open, no assignee, task `refused`; the dev's task is already closed.


### Rationale

A sanity run that could not run is not a verdict on the work: the close test shows it resets the sanity bead to open and refuses the task without notifying anyone, rather than recording a FAIL round.

### Success Criteria

**Acceptance Criteria:**

- [ ] A CANNOT_RUN verdict leaves the sanity bead `open`, closes its task with outcome `refused`, and sends no message.
- [ ] Repeating the CANNOT_RUN close is a no-op until a new assignment.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_cannot_run_resets_sanity_and_refuses_without_notice`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_cannot_run_terminal_refusal_is_a_noop_until_new_assignment`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0018: Role qa (`--role qa`)

**Status:** Draft  
### Requirement Statement

Input: the verdict, the sha, the round, the pours made. The hook closes the QA bead and task together (`bd close` first) with `qa-complete.md.j2` and sends the lead a status message, PASS or FAIL alike. It assigns nothing: quality-mgr has already poured the fix groups, and fix dispatch is the lead's judgment.


### Rationale

The lead needs every QA verdict, PASS or FAIL, as a message, but fix dispatch is the lead's judgment (quality-mgr has already poured the fix groups), so the hook reports and assigns nothing. The tests pin the order bead close, status message, task close.

### Success Criteria

**Acceptance Criteria:**

- [ ] A QA close for PASS and for FAIL writes, in order, `bd close`, `atm send`, `atm task close`.
- [ ] The message goes to the lead with body `QA <verdict> <qa bead> commit=<sha> round=<n>` and no `--template`.
- [ ] No `atm task assign` is issued.
- [ ] If the closer is the lead, no message is sent and the writes are `bd close` then `atm task close`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_qa_closes_bead_before_task_and_sends_lead_status`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_lead_closing_its_own_qa_task_skips_the_self_addressed_status`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0019: Lead and console

**Status:** Draft  
### Requirement Statement

Sanity and QA assignment are mechanical and belong to the hook. The fallback for a sanity or QA bead that `bd ready` lists with no ATM task (a hook that died between its commands) is the console or the lead assigning it as the lead; the console checks `atm task list` before assigning, and a second assign of the same id is an in-place update, never a second task.


### Rationale

The hook assigns sanity and QA mechanically, so the lead and console only fall back to assigning when a hook died between its commands. That fallback is safe only because a second assign of the same task id updates the existing task rather than creating another; the test shows the hook's own reassignment behaving that way.

### Success Criteria

**Acceptance Criteria:**

- [ ] Re-running the dev hook for the same sanity bead after a reassignment leaves one task for that bead, its last event `assigned`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_rebase_required_rerun_updates_same_open_sanity_task`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0020: Lead and console

**Status:** Draft  
### Requirement Statement

The lead does not link layers: after the PASS close hook succeeds, the sanity side links under the stack bead lock ([sanity-stack.md](sanity-stack.md)). The lead creates the stack bead with the integration branch, claims it before its own unstack, restack and land, and owns stack hygiene and every `stack_failed`. A sanity FAIL or rebase-required is fixed on the same unlinked branch.


### Rationale

SKILL.md (Stack Discipline) and phase bj moved linking to the sanity side (`sanity-stack-link`, serialized under the stack bead lock), so the lead no longer links; a layer stays unlinked until its sanity PASS, which is why a FAIL or rebase-required is fixed on the same branch.

### Success Criteria

**Acceptance Criteria:**

- [ ] A sanity PASS close does not read or update the stack bead before the sanity task closes.
- [ ] A rebase-required rerun uses the same checked bead and branch and the same sanity task.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_pass_closes_without_waiting_for_stack`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_rebase_required_rerun_updates_same_open_sanity_task`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## REQ-TCH-0021: Lead and console

**Status:** Draft  
### Requirement Statement

Dev and fix assignment stay with the lead: the hook closes the dev's own task (as the caller) at dev complete, after assigning sanity, so the dev starts its next queued task at once; a sanity FAIL re-assigns the same task id; fix beads from QA go to the dev the lead picks at the finding's difficulty.


### Rationale

Commit 62cb1ad04 moved the dev task close to dev complete so the dev starts its next queued task at once, while assignment of dev and fix work stays with the lead. When the lead itself closes a dev task it took over, ATM refuses a self-addressed send, which previously stranded the close after the bead closed (changelog 0.19.x).

### Success Criteria

**Acceptance Criteria:**

- [ ] After a dev run the sanity assignment is sent as the lead before the dev task is closed, and the dev task's last event is `complete` with outcome `completed`.
- [ ] The dev task is closed by the caller, not by the lead identity.
- [ ] When the caller is the lead, the self-addressed dev-complete message is skipped, the sanity task is still assigned, and the dev task is still closed.
- [ ] A sanity FAIL assigns the checked bead's same task id.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_dev_handoff_is_immediate_and_closes_the_dev_task_as_the_dev`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_lead_closing_its_own_dev_task_skips_only_the_self_addressed_dev_complete`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_task_close.py::test_sanity_fail_message_contains_exact_undone_deliverables`

### Implementation Notes

Sources: `scripts/atm-task-close.py`, `templates/task-close-vars.j2`,
`templates/rebase-required.xml.j2`, the dev, fix, sanity and qa templates; the stack bead ([sanity-stack.md](sanity-stack.md)).
Rulings: Rand, 2026-10-18, recorded verbatim on randlee/atm-core#1873, the
atm-core task-transition hook this script stands in for until the daemon
runs it.

## Command timeouts, retries and diagnostics

Each `bd`, `git` and `gh` call is bounded by `COMMAND_TIMEOUT` seconds (default 180, overridable with the `ATM_BD_GATE_TIMEOUT_S` environment variable). A call that times out is not retried: it fails the close with `COMMAND.FAILED` after one `COMMAND_TIMEOUT`. A `bd` call that fails with a dropped Dolt connection (output matching `invalid connection` or `i/o timeout`, seen at host load 40-55) is retried `DOLT_RETRIES = 3` times, sleeping `DOLT_RETRY_SLEEP_S = 10` seconds between attempts.

Worst case for one `bd` call that keeps dropping: `(3 + 1) x COMMAND_TIMEOUT + 3 x 10`. That is 750s at the default 180s timeout. A close makes several `bd` calls, so a fully starved close can wait that long per call. A close that times out waits one `COMMAND_TIMEOUT` (180s by default) before failing.

The hook records every attempt that was not a clean first-try success, and a success that needed a retry, under `attempts` in its JSON output: `command`, `attempt`, `timeout_s`, `elapsed_s`, `outcome` (`ok`, `dolt_drop_retry`, `failed`, `timeout`, `error`), `retries_until_now`, `total_elapsed_s`, `load_avg` (1, 5 and 15 minute `os.getloadavg`) and `cpu_pct` (1 minute load as a percentage of CPU count; `null` where `os.getloadavg` is unavailable).
