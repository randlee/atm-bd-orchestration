# adr-core - Decisions shared by every atm-bd package

**ID Range:** ADR-CORE-0001 through ADR-CORE-0007  
**Version:** 0.1.0  
**Status:** Draft  
**Created:** 2026-11-08  
**Last Updated:** 2026-11-08  
**Decision Date:** 2026-11-08  
**Owner:** Rand Lee  

## Context

atm-bd's rulebook moved from atm-core to this repository during the
2026-11-07/08 rulings session. These decisions apply to every atm-bd
package (atm-bd-lite, atm-bd-orchestration and later packages). Package
decisions live in the package's own ADR file.

---

## ADR-CORE-0001: atm-bd's requirements and ADRs live in this repository

**Status:** Draft  

### Context

ADR-066 and ADR-068 in atm-core, and anchors in atm-core's phase-bi, bj and
bo plans, still govern parts of atm-bd. Several conflict with the
2026-11-07 rulings.

### Decision

Every atm-bd requirement and ADR lives in atm-bd-orchestration
(`docs/requirements`, `docs/adr`). Where an atm-core ADR or anchor about
atm-bd conflicts with a record here, the record here governs. atm-core
records about atm-core's own runtime (for example the hook time limit) are
external constraints that atm-bd cites.

### Rationale

Rand (2026-11-08): "all of the REQ/ADR are to be on atm-bd-orchestration
repo, not on atm-core."

### Consequences

**Positive:**

- One rulebook for atm-bd, checked by one Raptor import.

**Negative:**

- ADR-066 D3/D5 (`ATM_TEAM` may select the team) and phase-bj ANC-051..053
  (messages to the phase lead) are superseded here and must be marked so in
  atm-core.

## ADR-CORE-0002: Lock atm-bd-lite down first, then rewrite atm-bd-orchestration

**Status:** Draft  

### Context

atm-bd-orchestration has more than 10,000 lines of scripts and about 300
requirement records.

### Decision

atm-bd-lite is specified completely by requirements first and rewritten
against them. atm-bd-orchestration is then rewritten on the same shared
core, and its replaced code is deleted.

### Rationale

Rand (2026-11-07): "The goal is to get atm-bd-lite locked down w/
requirements, then rewrite atm-bd-orch and remove 90% of needless code."

### Consequences

**Positive:**

- The shared core is proven on the smaller package before orchestration
  depends on it.

**Negative:**

- Orchestration records are an audit baseline until the rewrite, not a
  target.

## ADR-CORE-0003: One small entry point per hook and command

**Status:** Draft  

### Context

Applying hundreds of requirements to thousands of lines of code cannot be
done or checked reliably.

### Decision

Each hook, cron function and CLI command is its own small file that names
the requirement ids it implements. Rules that several entry points share
live in small shared modules. Each (requirement, entry point) pair is
checked on its own.

### Rationale

Rand (2026-11-08): "the pattern I am seeing here is that the complexity of
atm-bd is FAR too large for us to make these changes reliably. This is why
I keep pushing for a simple implementation that isolates every
hook/command against requirements. trying to apply 100's of requirements
against 10000+ lines of code is not going to be easy"

### Consequences

**Positive:**

- Every requirement has a small, named place to be judged.

**Negative:**

- A requirement that cannot be placed in one or two files is a defect in
  the requirement or the design and must be fixed first.

## ADR-CORE-0004: Context comes from the launch folder, never the environment

**Status:** Draft  

### Context

When omega-prime@hermes ran atm-bd for team atm-dev, `ATM_TEAM` leaked team
hermes into atm-bd.

### Decision

Every atm-bd entry point takes its team, identity, phase and configuration
from the repository or folder it was launched from and the phase file
there. Caller environment variables never select them.

### Rationale

Rand (2026-11-07): "atm-bd should not get team or identity from
environment. It should come from folder where phase config is loaded."
Rand (2026-11-08): "the original 'use ATM_TEAM' became a problem when
orchestrator omega-prime@hermes became involved. all atm-bd cli tools
should get all info from repo/folder it was launched from."

### Consequences

**Positive:**

- An orchestrator from another team cannot redirect atm-bd.

**Negative:**

- Supersedes ADR-066's allowance for `ATM_TEAM`.

## ADR-CORE-0005: Task facts come from ATM tasks; messages go to the assigner

**Status:** Draft  

### Context

The phase lead can change mid-phase, for example when a lead runs out of
tokens.

### Decision

atm-bd reads assigner, assignee and state from `atm task` queries and uses
the phase file only as a fallback. Review tasks take the assigner of the
dev task they review. Reports and escalations go to the task's assigner.

### Rationale

Rand (2026-11-08): "I would like all of atm-bd to move toward getting
information from existing 'atm task' queries w/ fallback of atm-bd
config." Rand (2026-11-07), on messages to the assigner: "this is even more
important, because sometimes lead transitions mid phase (i.e. out of
tokens)."

### Consequences

**Positive:**

- A lead handover needs no reconfiguration of open tasks.

**Negative:**

- The phase file's `lead` must still be updated on a handover, because it
  is the fallback.

## ADR-CORE-0006: bd-cache is the phase's source of truth

**Status:** Draft  

### Context

`bd` calls take seconds on a loaded host or a remote Dolt server. Hooks
have a 2.5 s limit (atm-core ADR-068).

### Decision

All bead access goes through bd-cache, which is the source of truth for
the phase and matches the bd JSON API. Its drain to bd is replication.
atm-bd's bead needs are met by beads-cache's API, never by an atm-bd
layer.

### Rationale

Rand (2026-11-08): "everything in atm-bd (including agent 'bd'
instructions) need to use bd-cache". "I expect that the cache matches the
bd api as closely as possible (json). I would expect changes 'from
upstream' to be rare. the bd-cache should be the source of truth for the
phase. beads-cache (rust daemon using tokio is already in development based
on requirements coming from atm-bd) and changes must align w/ beads-cache
api."

### Consequences

**Positive:**

- Hooks and agents read their own writes at once, within the hook limit.

**Negative:**

- Bead create (finding pour) waits on beads-cache #104.

## ADR-CORE-0007: Requirements and ADRs are shared or package-specific

**Status:** Draft  

### Context

atm-bd-lite and atm-bd-orchestration share most rules, and more packages
will follow.

### Decision

Shared records live in `docs/requirements/core.md` and
`docs/adr/adr-core.md`; package records in package files. No statement
conditions on which package runs.

### Rationale

Rand (2026-11-07): "Do NOT write requirements with IF orch ELSE lite in
them. I expect we will write dozens of packages and they should have shared
or individual req/adr, not hybrid."

### Consequences

**Positive:**

- A new package reuses the shared records unchanged.

**Negative:**

- Shared rules now in orchestration files must move to core.
