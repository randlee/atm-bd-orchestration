# console

**ID Range:** REQ-CON-0001 through REQ-CON-0015  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-18  
**Last Updated:** 2026-10-24  
**Owner:** Rand Lee  

---

## REQ-CON-0001: Identity (ADR-066)

**Status:** Draft  
### Requirement Statement

Every ATM message the console sends is a REQ-CORE-0018 notification, and the console's tool identity is the constant address `atm-bd@tool`. The only override is one optional key, `tool_identity: <identity>@<team>`, in the repository's `.claude/project/atm-bd-orchestration.yaml`.


### Rationale

Console notifications used to go out under whichever ATM identity the caller's shell held; commit 63bcc2322 (finding atm-phase-bi.7) introduced a dedicated tool identity so they come from one constant address.

### Success Criteria

**Acceptance Criteria:**

- [ ] `load_config` on a repository with no `tool_identity` key returns `notification_sender == "atm-bd@tool"`.
- [ ] With `tool_identity: "notify@automation"` in `.claude/project/atm-bd-orchestration.yaml`, `load_config` returns `notification_sender == "notify@automation"`.
- [ ] A `tool_identity` value that is not exactly `<identity>@<team>` (for example `notify`, `@tool`, `notify@tool@other`) makes `load_config` return a `ConfigInvalid` error whose key is `tool_identity`.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_config.py::test_notification_sender_only_uses_repo_yaml_not_environment_or_console_toml`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18). Shared rule: REQ-CORE-0018.

## REQ-CON-0002: Identity (ADR-066)

**Status:** Draft  
### Requirement Statement

The console never takes its sender from `ATM_IDENTITY`, from a flag, or from the phase file. `ATM_TEAM` may select the team the console executes against; it is never the sender's team.


### Rationale

Commit 747354d88 (finding atm-phase-bi.7) isolated the notification identity so that the caller's environment, which differs per shell, cannot change who a console message is from.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `ATM_IDENTITY=wrong`, `ATM_TEAM=source` and `[console] notification_sender = 'wrong@source'` in `console.toml`, `load_config` returns `notification_sender == "atm-bd@tool"`.
- [ ] The console's `atm send` argv carries `--as atm-bd --team tool`, with the lead team only in the recipient address.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_config.py::test_notification_sender_only_uses_repo_yaml_not_environment_or_console_toml`
- `apps/atm-bd-console/tests/test_monitor.py::test_cron_dry_run_never_sends_and_live_tick_sends_only_decided_action`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0003: Identity (ADR-066)

**Status:** Draft  
### Requirement Statement

The environment the console sets on its own `atm` subprocesses derives from 1 and is internal; it is not an input.


### Rationale

The tool-identity commits (63bcc2322, 747354d88) keep the sender fixed by config; the environment handed to `atm` subprocesses is only the mechanism that carries that choice, so it must not become a second way to set it.

### Success Criteria

**Acceptance Criteria:**

- [ ] `command.py` documents `overrides` (`ATM_IDENTITY`, `ATM_TEAM`) as replacing the caller's values for a subprocess, and no CLI flag or configuration key in `config.py` reads those variables to choose the sender.
- [ ] With `ATM_IDENTITY=wrong` and `ATM_TEAM=source` set in the caller's environment, `load_config` still returns `notification_sender == "atm-bd@tool"`.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_config.py::test_notification_sender_only_uses_repo_yaml_not_environment_or_console_toml`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0004: Identity (ADR-066)

**Status:** Draft  
### Requirement Statement

The `tool` team with member `atm-bd` exists before the console sends: the install creates it when missing (`atm teams add-member tool atm-bd`), and the console reports a typed startup error naming that step if the address does not resolve.


### Rationale

Commit 747354d88 (finding atm-phase-bi.7) added install-time provisioning of the `tool` team's `atm-bd` member because a send from an address that does not resolve fails.

### Success Criteria

**Acceptance Criteria:**

- [ ] Running `provision_tool_identity` when the member is missing invokes `atm teams add-member tool atm-bd --agent-type tool --model none`.
- [ ] Running it when `atm members --team tool --json` already lists `atm-bd` with `agent_type` `tool` adds no second member and does not fail.
- [ ] When the sender address does not resolve, the console startup shows a `NotFound` error naming `atm-bd@tool` with the fix `run atm teams add-member`.

**Test Evidence:**

- `apps/atm-bd-console/tests/../../plugins/atm-bd-orchestration/tests/test_install.py::test_provision_tool_identity_adds_member_and_accepts_verified_existing`
- `apps/atm-bd-console/tests/test_app.py::test_startup_atm_members_error_is_not_repeated_by_the_tick_that_reads_the_same_command`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0005: Identity (ADR-066)

**Status:** Draft  
### Requirement Statement

`atm task assign` stays `--as` the phase lead until atm-core allows cross-team task commands for tool members (atm-core #1870); sends do not wait on it.


### Rationale

Commit 5ff0a67fe (merge of fix/bi-px-7-notify-tool-identity) moved sends to the tool identity, but task commands act on the lead's team and the REQ's own text records atm-core #1870 as the missing cross-team support, so task assignment kept the lead identity.

### Success Criteria

**Acceptance Criteria:**

- [ ] The console's `atm task list` runs with `--as <phase lead>` and `ATM_IDENTITY=<phase lead>`, not `atm-bd`.
- [ ] The console's `atm send` runs with `--as atm-bd --team tool` and does not depend on any task command succeeding.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_queues.py::test_the_phase_decides_team_identity_and_bd_database_not_the_callers_env`
- `apps/atm-bd-console/tests/test_monitor.py::test_cron_dry_run_never_sends_and_live_tick_sends_only_decided_action`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0006: Time (ADR-065)

**Status:** Draft  
### Requirement Statement

Every time shown to a person (header, rows, PR sheet, Diagnostics view, cron digest) is 24-hour local time from the program's one display formatter. Every time written to a file, snapshot or log is UTC ISO-8601 with a `Z` suffix.


### Rationale

Commit 971f4ce0c (finding atm-phase-bi.9, "Render console diagnostics in local time") fixed diagnostics that showed UTC to a person while files and logs must stay unambiguous; `timefmt.clock` is the single local formatter.

### Success Criteria

**Acceptance Criteria:**

- [ ] With `TZ=Etc/GMT+8` and a snapshot generated at 12:00 UTC, the dashboard header, a dispatch row and the PR sheet show `04:00` in 24-hour form.
- [ ] The Diagnostics view prints a stored UTC timestamp `2026-10-18T12:00:00+00:00` as `04:00:00`.
- [ ] Every datetime in `snapshot.json` and `actions.jsonl` matches `YYYY-MM-DDTHH:MM:SSZ`, and every stored log event timestamp ends in `Z`.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_app.py::test_display_clocks_are_local_and_structured_log_stays_zulu`
- `apps/atm-bd-console/tests/test_app.py::test_diagnostic_line_uses_local_clock_and_preserves_message`
- `apps/atm-bd-console/tests/test_state.py::test_written_files_store_datetimes_only_in_utc_z_form`
- `apps/atm-bd-console/tests/test_log.py::test_events_are_retained_without_console_output`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0007: Operational log (ADR-067)

**Status:** Draft  
### Requirement Statement

The console writes one structured log through the sc-observability logger and no diagnostics or error file beside it. `diagnostics.log` and the code that wrote it are gone.


### Rationale

Commit 5e432a93d (finding atm-phase-bi.13) moved Diagnostics onto the sc-observability log, and ff75a4ad7 ("remove stale diagnostics writer") deleted the parallel `diagnostics.log` writer that duplicated it.

### Success Criteria

**Acceptance Criteria:**

- [ ] After a raised tick failure, the failure appears in the Diagnostics view and `<state_dir>/diagnostics.log` does not exist.
- [ ] `ConsoleApp` has no `diagnostics_path` or `_record_error` attribute.
- [ ] `create_console_logger` emits nothing on stdout or stderr while retaining events.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_app.py::test_raised_tick_failure_is_logged_and_diagnostics_file_is_removed`
- `apps/atm-bd-console/tests/test_app.py::test_display_clocks_are_local_and_structured_log_stays_zulu`
- `apps/atm-bd-console/tests/test_log.py::test_events_are_retained_without_console_output`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0008: Operational log (ADR-067)

**Status:** Draft  
### Requirement Statement

The writer sets the real level on every entry and composes a one-line message. A failed command logs at level error with `<fix in backticks> <command words> [<exit code>] <first stderr line>`, where the command words are the executable and its subcommand.


### Rationale

Commit 5e432a93d (finding atm-phase-bi.13) states that error writers now set explicit levels and messages, so a Diagnostics line reads as one actionable sentence instead of a raw record.

### Success Criteria

**Acceptance Criteria:**

- [ ] `ConsoleLogger.event("error", level="error", message="useful failure")` is returned by a query for level `error` with that level and message, and an event logged without a level has level `info`.
- [ ] `error_message` for a `command_failed` error with argv `gh api graphql --paginate`, code 1, fix `check gh and retry` and a two-line stderr returns exactly ``"`check gh and retry` gh api graphql [1] first stderr line"``.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_log.py::test_event_level_and_message_are_explicit_and_default_to_info`
- `apps/atm-bd-console/tests/test_log.py::test_error_message_formats_boundary_errors_as_one_line`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0009: Operational log (ADR-067)

**Status:** Draft  
### Requirement Statement

The Diagnostics view reads the sc-observability log, extracts the timestamp (rendered per 6) and the level, and prints the entry's message unchanged. It parses nothing else.


### Rationale

Commit 5e432a93d (finding atm-phase-bi.13) made Diagnostics read warning and error events from sc-observability; the view only presents what the writer composed, so the format has one owner.

### Success Criteria

**Acceptance Criteria:**

- [ ] A logged error with message ``"`retry` timeout after 10s"`` appears in the Diagnostics view with that message unchanged after a time and the word `error:`.
- [ ] The Diagnostics line for an event stamped `2026-10-18T12:00:00+00:00` with level `error` is `04:00:00 error: <message>` in `Etc/GMT+8`, with the message text byte-for-byte as stored.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_app.py::test_diagnostics_view_reads_structured_log_entries`
- `apps/atm-bd-console/tests/test_app.py::test_diagnostic_line_uses_local_clock_and_preserves_message`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0010: Operational log (ADR-067)

**Status:** Draft  
### Requirement Statement

One failure, one entry. A cached failure still on display (the last GitHub error kept with cached PR data) is a sheet status, never a new entry per tick.


### Rationale

Commit 5e432a93d (finding atm-phase-bi.13) records that cached GitHub failures are not repeated as new tick errors, because a failure kept with cached PR data would otherwise be logged on every tick.

### Success Criteria

**Acceptance Criteria:**

- [ ] A tick whose `GhStatus.error` is a cached timeout leaves that error in `snapshot.gh.error` and does not add it to `snapshot.errors`.
- [ ] A forced GitHub read that times out writes exactly one `error` event to the log.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_model.py::test_cached_github_error_is_not_readded_as_a_new_tick_error`
- `apps/atm-bd-console/tests/test_runner.py::test_forced_github_timeout_is_visible_and_logged_once`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0011: GitHub polling (bead atm-phase-bi.12)

**Status:** Draft  
### Requirement Statement

The GitHub poll interval defaults to 10 minutes and is set in the repository configuration and overridable on the command line; the status bar shows it.


### Rationale

Commit e08c9ea00 ("guard and schedule GitHub polling", finding atm-phase-bi.12) added a configurable GitHub cadence separate from the console tick so a 60-second tick does not spend GitHub quota every minute.

### Success Criteria

**Acceptance Criteria:**

- [ ] `load_config` without a `github_poll_interval` key sets `github_poll_interval_s` to 600, and a value passed on the command line overrides the configured value.
- [ ] `github_poll_interval` below 1 or not an integer makes `load_config` return a `ConfigInvalid` error naming `github_poll_interval`.
- [ ] With `poll_interval_s=120`, the status bar text contains `gh poll 120s / 50%`.
- [ ] With a poll interval of N seconds, a second runner step N-1 seconds after a GitHub read makes no GitHub call, and a step at N seconds does.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_runner.py::test_github_interval_is_independent_and_paused_refresh_keeps_cache`
- `apps/atm-bd-console/tests/test_render.py::test_status_bar_reports_paused_quota_and_local_reset`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0012: GitHub polling (bead atm-phase-bi.12)

**Status:** Draft  
### Requirement Statement

One refresh fetches up to 100 PRs per GraphQL page with few fields and pages past 100 rather than dropping PRs. GraphQL is the default mode.


### Rationale

Commit e08c9ea00 (finding atm-phase-bi.12) made GraphQL paginate under the quota guard; before it, a repository with more than one page of open PRs lost the rest.

### Success Criteria

**Acceptance Criteria:**

- [ ] With 101 open PRs, a GraphQL refresh requests the second page by `cursor=page-one` and returns 101 PRs with `truncated` false.
- [ ] The open-PR GraphQL query in `github_source.py` uses `first: 100` and a `$cursor` argument.
- [ ] `open_prs("graphql", ...)` runs the GraphQL command, not the REST `pulls` command, when mode is `graphql`.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_github_quota.py::test_graphql_paginates_and_checks_shared_quota_before_every_page`
- `apps/atm-bd-console/tests/test_pr_query_bound.py::test_one_graphql_call_per_poll_on_a_2250_pr_repository`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0013: GitHub polling (bead atm-phase-bi.12)

**Status:** Draft  
### Requirement Statement

Before each refresh the console reads the live remaining quota for its mode's resource (`graphql` or `core`) with `gh api rate_limit`. Below the configured threshold (default 50 percent of the limit) it skips the refresh, keeps cached PR data, shows a paused status with the numbers and the local reset time, refuses forced refreshes, and resumes on the first cycle at or above the threshold after reset. The quota is per token and shared across consoles, so the check never counts the console's own calls.


### Rationale

Commit e08c9ea00 (finding atm-phase-bi.12) added a live quota guard so several consoles sharing one GitHub token stop polling before one of them exhausts it; the commit message names the shared live quota guard.

### Success Criteria

**Acceptance Criteria:**

- [ ] With 2450 of 5000 `graphql` remaining and a 50 percent threshold, `open_prs` returns an error, sets `paused`, and runs only the `gh api rate_limit` command.
- [ ] With 2500 of 5000 remaining after the reset time, `open_prs` runs the GraphQL query and clears `paused`; before the reset time it stays paused with no GraphQL call.
- [ ] The status bar shows `GitHub paused: 2450/5000 graphql remaining, below 50 percent, resets 08:14` with the reset in local time.
- [ ] After a `RATE_LIMITED` response, `open_prs` makes no GitHub call until the reset time.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_github_quota.py::test_pauses_at_49_percent_and_recovers_at_threshold`
- `apps/atm-bd-console/tests/test_github_quota.py::test_rate_limit_error_locks_out_until_reset`
- `apps/atm-bd-console/tests/test_render.py::test_status_bar_reports_paused_quota_and_local_reset`
- `apps/atm-bd-console/tests/test_runner.py::test_closed_phase_forced_refresh_respects_pause_and_keeps_cached_prs`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0014: Dashboard rows (bead atm-phase-bi.10)

**Status:** Draft  
### Requirement Statement

An agent task row reads `<sprint or fix id>: <bead title>`, truncated to the pane width; never `<phase>: <ATM message text>`.


### Rationale

Finding atm-phase-bi.10 named the dashboard row prefix; the poured bead title (for example `bi-6: Fix the row prefix`) tells an operator the task, where the ATM message text did not.

### Success Criteria

**Acceptance Criteria:**

- [ ] For a dev step in sprint `bi-6` titled `Fix the row prefix`, the dashboard row ends with `bi-6: Fix the row prefix`.
- [ ] A 300-character title is cut with a trailing `…` so the row's cell width does not exceed the pane width at 60, 100 and 160 columns.
- [ ] A title already poured as `bj-2: dev` for sprint `bj-2` renders `bj-2: dev` with no repeated `bj-2: bj-2:`.

**Test Evidence:**

- `apps/atm-bd-console/tests/test_render.py::test_agent_row_cuts_only_the_title_to_pane_width`
- `apps/atm-bd-console/tests/test_render.py::test_agent_row_that_fits_is_unchanged_by_pane_width`
- `apps/atm-bd-console/tests/test_render.py::test_agent_row_does_not_double_the_sprint_prefix_of_a_poured_title`

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## REQ-CON-0015: Dashboard rows (bead atm-phase-bi.10)

**Status:** Draft  
### Requirement Statement

When Jev returned no evaluation for a deliverable (a Jev error rather than an answer), the console shows a red circle with a diagonal line do-not-enter icon on that deliverable, distinct from a negative verdict (candidate `nf-fa-ban` U+F05E, not `nf-md-minus_circle`; Rand, 2026-10-21). Not yet implemented (phase bl).


### Rationale

Commit 3c5baf412 records Rand's 2026-10-21 request next to the dev-sanity rule that Jev returns one exhaustive error enum, so a Jev error is a different outcome from a FAIL verdict and must not be drawn as one.

### Success Criteria

**Acceptance Criteria:**

- [ ] For a deliverable whose Jev result is an error and not a PASS or FAIL, the rendered deliverable shows the U+F05E glyph in red.
- [ ] That glyph differs from the glyph and colour the same view draws for a Jev `FAIL` verdict (`\U000f01a6`, `#F85149`).

### Implementation Notes

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## Unresolved

- `input.log`, the console's hand-written input trace, is a second file outside the structured log. ADR-067 reviews it against D1; whether it is folded into the log or removed awaits a ruling.
- Cross-team `atm task assign` for tool members (requirement 5) is an atm-core change (#1870); until it lands requirement 1 covers sends only.
