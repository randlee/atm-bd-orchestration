# planner

**ID Range:** REQ-PLAN-0001 through REQ-PLAN-0058  
**Version:** 1.0.0  
**Status:** Approved  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-26  
**Owner:** Rand Lee  

---

## REQ-PLAN-0001: Start

**Status:** Approved  
### Requirement Statement

Check `bd`, `atm`, `sc-compose`, `jq` at the skill's minimum versions; missing or old: stop, tell the user which and its install line; never work around it.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0002: Start

**Status:** Approved  
### Requirement Statement

`ATM_IDENTITY` must equal `BEADS_ACTOR` (bare pane name); otherwise no bead writes until fixed; pass `--actor "$ATM_IDENTITY"` on every `bd` write.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0003: Start

**Status:** Approved  
### Requirement Statement

`bd doctor` error: stop, report to the lead.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0004: Start

**Status:** Approved  
### Requirement Statement

Keep scratch (vars, renders, `plan.jsonl`) outside the repository; take repository values from `.claude/project/atm-bd-orchestration.yaml`, a missing file or key is an error, never a default.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0005: Shape the plan

**Status:** Approved  
### Requirement Statement

Write the boundary map into the root's design first (crates/manifests changed, contract change, allowed edges); cut sprints from it.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0006: Shape the plan

**Status:** Approved  
### Requirement Statement

Cut for the shortest critical path with the fewest sprints; concurrent sprints have disjoint `owned_paths`; sprints sharing a path are ordered.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0007: Shape the plan

**Status:** Approved  
### Requirement Statement

Cross-boundary track: contract sprint, parallel layer sprints, one integration sprint per track; no phase-wide integration checkpoint.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0008: Shape the plan

**Status:** Approved  
### Requirement Statement

Cut by layer only when it creates parallel work; a thin contract with one implementer and one consumer is one sprint with `vertical_rationale`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0009: Shape the plan

**Status:** Approved  
### Requirement Statement

No thin sprints: fold pass-through edits into the adjacent sprint's `owned_paths`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0010: Shape the plan

**Status:** Approved  
### Requirement Statement

One `closure_type` (`contract`, `boundary`, `integration`, `docs`) and one `target_boundary` per sprint; split mixed closure, >1 boundary without `vertical_rationale`, doubtful or twice-planned deliverables.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0011: Shape the plan

**Status:** Approved  
### Requirement Statement

List behaviour through other crates under "This Sprint Does Not Close", naming the integration sprint that owns it.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0012: Shape the plan

**Status:** Approved  
### Requirement Statement

Contract/boundary criteria rooted at the boundary or ADR; `req:<ID>` criteria only in integration sprints; each feature-level criterion in exactly one integration sprint.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0013: Shape the plan

**Status:** Approved  
### Requirement Statement

`must_follow` only for a named, unhoistable contract artifact; never for a shared file (re-cut); default `parallel_safe`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0014: Shape the plan

**Status:** Approved  
### Requirement Statement

Publish the wave table in the root design (tracks, waves, `target_boundary`, `owned_paths`, critical path, width, count); justify every edge past a critical path of three.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0015: Shape the plan

**Status:** Approved  
### Requirement Statement

Add a process artifact only with its consumer, gated capability, observed defect and retirement.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0016: Shape the plan

**Status:** Approved  
### Requirement Statement

Put contract code samples in the contract sprint's design; layer sprints reference them.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0017: Shape the plan

**Status:** Approved  
### Requirement Statement

Plan-time beads carry `difficulty` only, never an assignee; the lead picks the agent at dispatch.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0018: Shape the plan

**Status:** Approved  
### Requirement Statement

Naming per "Plan Naming" at `policy_path`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0019: Write the beads

**Status:** Approved  
### Requirement Statement

Render one root bead (`plan-root`) and one sprint container per sprint (`sprint-bead`); the root's `integration_branch` comes from `integration_branch_pattern`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0020: Write the beads

**Status:** Approved  
### Requirement Statement

Sprint description: goal, numbered `## Deliverables` from 1 (each naming its REQ/NFR), required work, non-closure, paths to delete; design: contract, types, samples, targets; acceptance: criteria + validation commands.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0021: Write the beads

**Status:** Approved  
### Requirement Statement

Sprint metadata includes `owned_paths`, `closure_type`, `target_boundary`, `difficulty`, `branch`, `worktree`, `layer` and `pr_target`: the branch of the nearest `must_follow` prerequisite it builds on, never a parallel sibling; none: the root's `integration_branch`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0022: Write the beads

**Status:** Approved  
### Requirement Statement

Ordering is the plan file's `depends_on`; `bead-groups` blocks the dependent's dev bead on each prerequisite's sanity bead, never its dev bead.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0023: Write the beads

**Status:** Approved  
### Requirement Statement

`requirements` and `adrs`: every governing id or exactly `["NONE"]`; never empty, never mixed.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0024: Write the beads

**Status:** Approved  
### Requirement Statement

A not-yet-existing id only when its document is in `owned_paths` and a deliverable says the sprint adds it.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0025: Write the beads

**Status:** Approved  
### Requirement Statement

No dev, sanity or QA bead is planned: `bead-groups --phase <x>` pours each sprint's dev ← sanity ← qa group under its container after import; no assignee.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0026: Write the beads

**Status:** Approved  
### Requirement Statement

Stop on any render failure; never let a failed render drop a bead.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0027: Write the beads

**Status:** Approved  
### Requirement Statement

Hand-write the plan file `<plans_dir>/phase-<x>.jsonl` (one `{"sprint", optional "depends_on"}` line per sprint). Create `.atm-bd/phase-<x>.toml` before validation or pouring with `phase-config init --phase <x> --lead <appointed-lead>`: explicit lead, repository-derived plan/root/integration branch, and seven existing installed template paths (`dev`, `dev_fix`, `fix`, `sanity`, `qa`, `plan_review`, `review`). The writer refuses to overwrite an existing phase; neither file is generated from beads, nor beads from it.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0028: Write the beads

**Status:** Approved  
### Requirement Statement

`validate-plan` on the rendered plan; exit 5: fix every problem and re-render.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0029: Write the beads

**Status:** Approved  
### Requirement Statement

`bd import --dry-run`, then `bd import`, then `bead-groups --phase <x>`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0030: Write the beads

**Status:** Approved  
### Requirement Statement

At once create `<root>-plan-qa` (no assignee, parent root); every sprint container blocks on it.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0031: Write the beads

**Status:** Approved  
### Requirement Statement

Run `sprint-review --root <root>`: it writes the phase DAG HTML `<plans_dir>/phase-<x>/phase-<x>-dag.html` from the plan file in the working tree (the script never commits or pushes); no `--view` unless asked.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0032: Write the beads

**Status:** Approved  
### Requirement Statement

Commit the plan file, the phase file and the DAG together with the plan and push them to the `integration_branch`, then open a PR from it to the repository trunk before plan review; on a plan change, re-run `sprint-review` and commit the DAG with it, updating that PR.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0033: Write the beads

**Status:** Approved  
### Requirement Statement

`validate-plan --phase <x>`; exit 0 or stop and report.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0034: Write the beads

**Status:** Approved  
### Requirement Statement

Hand to plan review; nothing is dispatched until it passes.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0035: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Find the root; exists: no new root, import under it, report root fields missing from the phase plan.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0036: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Map fields by the Mapping table (translation, never rewrite); `difficulty` from frontmatter, missing or invalid is blocking; drop merge-forward triggers, PR-completion trigger, per-sprint `base`, frontmatter `assignee`, `status`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0037: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Run every Checks row except id-exists before rendering; collect all gaps; any blocking: send the plan's author one line `<doc>: <field>: <problem>` per gap, blocking first; import nothing.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0038: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Render and validate as 26-28; any problem stops the import.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0039: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Any id already exists: stop, use `bd update`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0040: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Import, then append `imported from <doc path>@<short sha>` to each sprint bead's notes, then `bead-groups --phase <x>`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0041: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Plan-review bead as 30; into a running phase: `<root>-plan-qa-<n>` (next free), blocking every new sprint container.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0042: Import a markdown plan

**Status:** Approved  
### Requirement Statement

As 31-33; then `bd ready -l phase-<x> -n 0` lists the plan-review bead and no imported dev bead, and `bd ready --explain` shows the rest blocked by plan review or prerequisite sanity beads.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0043: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Run `bd sync`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0044: Import a markdown plan

**Status:** Approved  
### Requirement Statement

Never edit, move or delete the markdown; never run the phase from both.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0045: Plan review FAIL

**Status:** Approved  
### Requirement Statement

Fix the beads with `bd update`; next round with the same task id; at most three rounds.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0046: Replanning

**Status:** Approved  
### Requirement Statement

The plan file is the minimum set of sprint edges. Fix a DAG problem only by replanning: edit the plan file in a `/sc-git-worktree` branch off the `integration_branch`, merge the plan PR into it; beads and the plan file change in one commit.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0047: Replanning

**Status:** Approved  
### Requirement Statement

While the phase runs the sprint set is frozen; only the lead adds edges: to phase-created fix beads, and any dependency discovered in motion (sprint beads included), never a replan.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0048: Replanning

**Status:** Approved  
### Requirement Statement

Keep `validate-plan --root <root>` green from plan approval to phase end.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0049: Never

**Status:** Approved  
### Requirement Statement

Never create a gate bead or its edges without the user's explicit instruction for that gate.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0050: Never

**Status:** Approved  
### Requirement Statement

Never repair the graph with `bd dep` or `--parent`, beyond adding a dependency discovered in motion.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0051: Never

**Status:** Approved  
### Requirement Statement

Never re-import to update a bead.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0052: Never

**Status:** Approved  
### Requirement Statement

Never put findings, fixes, QA, tasks, branches or gates in the plan file.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0053: Never

**Status:** Approved  
### Requirement Statement

Never mark an unimplemented sprint bead `closed`.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0054: Never

**Status:** Approved  
### Requirement Statement

Never edit the script, the plan or the graph to make validation pass.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0055: Never

**Status:** Approved  
### Requirement Statement

Root children: only the sprint containers, `stage:plan*` beads, gate beads, folded sprints and important or minor finding beads.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0056: Scripts

**Status:** Approved  
### Requirement Statement

`validate-plan` problems (exit 5), and nothing else: a plan file line off the schema or a `depends_on` naming an unknown sprint, a sprint container failing SprintBead or a poured sanity bead failing SanityBead; a plan sprint without its container; a `stage:sprint` container the plan does not list; the phase file's `integration_branch` differing from the root's; a `depends_on` with no `blocks` edge from the dependent's dev bead (or container) to the predecessor's sanity bead or container. Everything else is a stderr warning (`bd doctor` errors, open non-epic top-level beads since the root, a plan-time assignee in `--file`, a sanity `dev_bead` that is not its group's dev bead, a group not poured yet).

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0057: Scripts

**Status:** Approved  
### Requirement Statement

`validate-plan` reads the plan file from `origin/<integration_branch>` as the phase file names it (or `--index`); exit 0 valid, 5 problems, 2 cannot run (no phase file, fetch failure, plan file missing); `--phase` or `--root` required.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

**Key Considerations:**


### Test Strategy



**Test Types:**


### Related Documents



**Requirements:**

**Architecture Decisions:**

**Design Documents:**

**Work Items:**

**External References:**

## REQ-PLAN-0058: Scripts

**Status:** Approved  
### Requirement Statement

Not scripted, checked by plan review: ids exist and govern the work, disjoint `owned_paths`, `relation`/`layer`/`pr_target` agree.

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

Sources: `plugins/atm-bd-orchestration/skills/`: `atm-beads/` (SKILL.md, resources/planning.md, atm-beads-plan-guidelines.md, importing-md-plan.md, troubleshooting.md, references/installation-and-troubleshooting.md, templates/*.json.j2, scripts/*), `atm-bd-orchestration/SKILL.md` (Repository configuration, Gate Beads, Plan Gate, Loop), `atm-bd-orchestration/scripts/bead-groups`.

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

None.
