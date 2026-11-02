---
id: a-2
title: Intake and duplicate agents
difficulty: fast
relation: must_follow
depends_on: ["a-1"]
requirements: ["NONE"]
adrs: ["NONE"]
---

# a-2 — Intake and duplicate agents

## Goal

Add the agents that run before any triage label. Each agent returns one determination.

## Owned paths

- `plugins/triaging-gh-issues/agents/issue-import.md`
- `plugins/triaging-gh-issues/agents/issue-duplicate-judge.md`
- `plugins/triaging-gh-issues/agents/issue-phase-match.md`
- `plugins/triaging-gh-issues/agents/issue-phase-done.md`
- `plugins/triaging-gh-issues/agents/issue-overlap-judge.md`
- `plugins/triaging-gh-issues/agents/issue-prpair-judge.md`

## Deliverables

| Agent | Determination |
| --- | --- |
| `issue-import` | bead id. Bead is in incoming, with `status/needs-triage`. |
| `issue-duplicate-judge` | `dup/none` or `dup/#N` |
| `issue-phase-match` | `phase/none` or `phase/<bead>` |
| `issue-phase-done` | `phase-done/no` or `phase-done/yes`, and on `yes` the pull request number and full commit sha |
| `issue-overlap-judge` | `overlap/none` or `overlap/<bead>` |
| `issue-prpair-judge` | `prpair/none` or `prpair/#N` |

The scan looks at other open issues, open pull requests, and each active phase: its sprint index, open beads, closed beads, and pull requests merged to its integration branch. An active phase is a `.atm-bd/phase-<x>.toml` whose root bead is open.

## Acceptance

- Each agent stays at 1–3KB. Review against the phase plan's Review standard. A review that adds prose fails.
- Each file has YAML frontmatter with `name`, `version`, and a one-sentence description, and returns fenced JSON whose `data.determination` is one label.
- `dup/#N` is the close determination. The agent does not classify kind, area, size, or priority.
- `phase-done/yes` carries the pull request number and commit. The next patch label is applied by the skill from `release-version.toml`.
- `overlap/<bead>` names the parent bead. A match with no bead is recorded and no parent is invented.
- `prpair/#N` leaves both pull requests open.
