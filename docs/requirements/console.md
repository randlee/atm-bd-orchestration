# console

**ID Range:** REQ-CON-0001 through REQ-CON-0015  
**Version:** 1.0.0  
**Status:** Approved  
**Created:** 2026-10-18  
**Last Updated:** 2026-10-24  
**Owner:** Rand Lee  

---

## REQ-CON-0001: Identity (ADR-066)

**Status:** Approved  
### Requirement Statement

Every ATM message the console sends goes out as the constant address `atm-bd@tool`. The only override is one optional key, `tool_identity: <identity>@<team>`, in the repository's `.claude/project/atm-bd-orchestration.yaml`.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0002: Identity (ADR-066)

**Status:** Approved  
### Requirement Statement

The console never takes its sender from `ATM_IDENTITY`, from a flag, or from the phase file. `ATM_TEAM` may select the team the console executes against; it is never the sender's team.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0003: Identity (ADR-066)

**Status:** Approved  
### Requirement Statement

The environment the console sets on its own `atm` subprocesses derives from 1 and is internal; it is not an input.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0004: Identity (ADR-066)

**Status:** Approved  
### Requirement Statement

The `tool` team with member `atm-bd` exists before the console sends: the install creates it when missing (`atm teams add-member tool atm-bd`), and the console reports a typed startup error naming that step if the address does not resolve.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0005: Identity (ADR-066)

**Status:** Approved  
### Requirement Statement

`atm task assign` stays `--as` the phase lead until atm-core allows cross-team task commands for tool members (atm-core #1870); sends do not wait on it.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0006: Time (ADR-065)

**Status:** Approved  
### Requirement Statement

Every time shown to a person (header, rows, PR sheet, Diagnostics view, cron digest) is 24-hour local time from the program's one display formatter. Every time written to a file, snapshot or log is UTC ISO-8601 with a `Z` suffix.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0007: Operational log (ADR-067)

**Status:** Approved  
### Requirement Statement

The console writes one structured log through the sc-observability logger and no diagnostics or error file beside it. `diagnostics.log` and the code that wrote it are gone.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0008: Operational log (ADR-067)

**Status:** Approved  
### Requirement Statement

The writer sets the real level on every entry and composes a one-line message. A failed command logs at level error with `<fix in backticks> <command words> [<exit code>] <first stderr line>`, where the command words are the executable and its subcommand.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0009: Operational log (ADR-067)

**Status:** Approved  
### Requirement Statement

The Diagnostics view reads the sc-observability log, extracts the timestamp (rendered per 6) and the level, and prints the entry's message unchanged. It parses nothing else.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0010: Operational log (ADR-067)

**Status:** Approved  
### Requirement Statement

One failure, one entry. A cached failure still on display (the last GitHub error kept with cached PR data) is a sheet status, never a new entry per tick.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0011: GitHub polling (bead atm-phase-bi.12)

**Status:** Approved  
### Requirement Statement

The GitHub poll interval defaults to 10 minutes and is set in the repository configuration and overridable on the command line; the status bar shows it.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0012: GitHub polling (bead atm-phase-bi.12)

**Status:** Approved  
### Requirement Statement

One refresh fetches up to 100 PRs per GraphQL page with few fields and pages past 100 rather than dropping PRs. GraphQL is the default mode.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0013: GitHub polling (bead atm-phase-bi.12)

**Status:** Approved  
### Requirement Statement

Before each refresh the console reads the live remaining quota for its mode's resource (`graphql` or `core`) with `gh api rate_limit`. Below the configured threshold (default 50 percent of the limit) it skips the refresh, keeps cached PR data, shows a paused status with the numbers and the local reset time, refuses forced refreshes, and resumes on the first cycle at or above the threshold after reset. The quota is per token and shared across consoles, so the check never counts the console's own calls.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0014: Dashboard rows (bead atm-phase-bi.10)

**Status:** Approved  
### Requirement Statement

An agent task row reads `<sprint or fix id>: <bead title>`, truncated to the pane width; never `<phase>: <ATM message text>`.

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-CON-0015: Dashboard rows (bead atm-phase-bi.10)

**Status:** Approved  
### Requirement Statement

When Jev returned no evaluation for a deliverable (a Jev error rather than an answer), the console shows a red circle with a diagonal line do-not-enter icon on that deliverable, distinct from a negative verdict (candidate `nf-fa-ban` U+F05E, not `nf-md-minus_circle`; Rand, 2026-10-21). Not yet implemented (phase bl).

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

Package sources: `apps/atm-bd-console` (`atm-bd console`, `atm-bd cron`); `.claude/project/atm-bd-orchestration.yaml`; `.atm-bd/phase-<x>.toml`. Authority: atm-core ADR-065 (time), ADR-066 (tool identity), ADR-067 (one structured log); anchors ANC-041 to ANC-050 in atm-core `docs/plans/phase-bi/anchors.json`; Rand's rulings quoted verbatim on beads atm-phase-bi.7, .9, .10, .12 and .13 (2026-10-18).

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## Unresolved

- `input.log`, the console's hand-written input trace, is a second file outside the structured log. ADR-067 reviews it against D1; whether it is folded into the log or removed awaits a ruling.
- Cross-team `atm task assign` for tool members (requirement 5) is an atm-core change (#1870); until it lands requirement 1 covers sends only.
