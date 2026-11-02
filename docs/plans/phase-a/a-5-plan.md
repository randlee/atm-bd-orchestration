---
id: a-5
title: Plan agents
difficulty: hard
relation: must_follow
depends_on: ["a-1"]
requirements: ["NONE"]
adrs: ["NONE"]
---

# a-5 — Plan agents

## Goal

Add the agents that write the plan bead and accept it. `issue-plan-write` is hard: fable, opus, sol, or astra. `sol` is the same class as `opus`.

## Owned paths

- `plugins/triaging-gh-issues/agents/issue-plan-write.md`
- `plugins/triaging-gh-issues/agents/plan-accept.md`

## Deliverables

| Agent | Determination |
| --- | --- |
| `issue-plan-write` | `status/planned` and the new plan bead id |
| `plan-accept` | `status/plan-accepted` or `status/plan-rejected` |

`issue-plan-write` places the plan bead in `backlog-product`, `backlog-skills`, or `backlog-workflows` from the `area/` label. The skill deploys it only when `arch/` and `security/` are set and no gate holds `plan`.

`plan-accept` is the quality-mgr determination. It does not open a pull request.

## Acceptance

- Each agent stays at 1–3KB. Review against the phase plan's Review standard. A review that adds prose fails.
- Each file has YAML frontmatter with `name`, `version`, and a one-sentence description, and returns fenced JSON whose `data.determination` is one label.
- `issue-plan-write` returns one plan bead id. It does not set `status/plan-accepted`.
- `plan-accept` returns only `status/plan-accepted` or `status/plan-rejected`.
