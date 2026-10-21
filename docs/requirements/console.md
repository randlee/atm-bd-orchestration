# console

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

## Requirements

### Identity (ADR-066)

1. Every ATM message the console sends goes out as the constant address `atm-bd@tool`. The only override is one optional key, `tool_identity: <identity>@<team>`, in the repository's `.claude/project/atm-bd-orchestration.yaml`.
2. The console never takes its sender from `ATM_IDENTITY`, from a flag, or from the phase file. `ATM_TEAM` may select the team the console executes against; it is never the sender's team.
3. The environment the console sets on its own `atm` subprocesses derives from 1 and is internal; it is not an input.
4. The `tool` team with member `atm-bd` exists before the console sends: the install creates it when missing (`atm teams add-member tool atm-bd`), and the console reports a typed startup error naming that step if the address does not resolve.
5. `atm task assign` stays `--as` the phase lead until atm-core allows cross-team task commands for tool members (atm-core #1870); sends do not wait on it.

### Time (ADR-065)

6. Every time shown to a person (header, rows, PR sheet, Diagnostics view, cron digest) is 24-hour local time from the program's one display formatter. Every time written to a file, snapshot or log is UTC ISO-8601 with a `Z` suffix.

### Operational log (ADR-067)

7. The console writes one structured log through the sc-observability logger and no diagnostics or error file beside it. `diagnostics.log` and the code that wrote it are gone.
8. The writer sets the real level on every entry and composes a one-line message. A failed command logs at level error with `<fix in backticks> <command words> [<exit code>] <first stderr line>`, where the command words are the executable and its subcommand.
9. The Diagnostics view reads the sc-observability log, extracts the timestamp (rendered per 6) and the level, and prints the entry's message unchanged. It parses nothing else.
10. One failure, one entry. A cached failure still on display (the last GitHub error kept with cached PR data) is a sheet status, never a new entry per tick.

### GitHub polling (bead atm-phase-bi.12)

11. The GitHub poll interval defaults to 10 minutes and is set in the repository configuration and overridable on the command line; the status bar shows it.
12. One refresh fetches up to 100 PRs per GraphQL page with few fields and pages past 100 rather than dropping PRs. GraphQL is the default mode.
13. Before each refresh the console reads the live remaining quota for its mode's resource (`graphql` or `core`) with `gh api rate_limit`. Below the configured threshold (default 50 percent of the limit) it skips the refresh, keeps cached PR data, shows a paused status with the numbers and the local reset time, refuses forced refreshes, and resumes on the first cycle at or above the threshold after reset. The quota is per token and shared across consoles, so the check never counts the console's own calls.

### Dashboard rows (bead atm-phase-bi.10)

14. An agent task row reads `<sprint or fix id>: <bead title>`, truncated to the pane width; never `<phase>: <ATM message text>`.

### Collector, state, and event pipeline (phase bl)

15. "collect-data (cron and/or tui) and save to db -> process data (determine state) and save to db -> fire events (after debouncing & aggregation)" describes the console architecture. Its persistence is JSON files in the phase state directory; it does not introduce a database.
16. "we do NOT need to collect data from all sources at the same rate." BD/dolt, ATM, and GitHub are separate collectors with their own rules and persisted freshness/error records. Their default eligible periods are BD/dolt 60 seconds, ATM 60 seconds, and GitHub 600 seconds; GitHub rate limiting and BD/dolt command deadlines remain source-specific rules.
17. A collector records its current value plus last successful collection, last attempt, typed error, and failure-since time. Only a successful collection suppresses its next eligible attempt. A failed or partial collection remains eligible on the next request and never makes prior valid data look current.
18. Cron and the TUI may request the same collector. Per-collector nonblocking deduplication prevents duplicate bd/dolt, ATM, or GitHub load; a request that does not collect returns the current persisted information and its freshness/error state. Cron therefore prints the same current information even when it did not collect it, including data a running TUI collected.
19. A state stage reads current collector records and writes aggregate state for display. Carried valid data shows its age and typed reason; never-read or invalid data has a labelled placeholder and is not forced into an error.
20. "ATM messages occur on a specified schedule based on timing... nothing to do with either tui or cron." State transitions create durable ATM message requests; a separate delivery schedule aggregates and debounces those requests, sends due messages, and records the outcome. Collection and TUI display never send ATM messages.
21. "multiple collectors each in separate module governed by it's own rules (i.e. gh rate limited, dolt timeouts, atm no limits today). state evaluation based on current state. specific state transitions would trigger 'atm message request'." No rule requires all collectors to refresh together or requires a fresh BD-and-ATM read before an event request.

## Unresolved

- `input.log`, the console's hand-written input trace, is a second file outside the structured log. ADR-067 reviews it against D1; whether it is folded into the log or removed awaits a ruling.
- Cross-team `atm task assign` for tool members (requirement 5) is an atm-core change (#1870); until it lands requirement 1 covers sends only.
