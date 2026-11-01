---
id: bo-3
title: Classification agents
difficulty: fast
relation: must_follow
depends_on: ["bo-1"]
requirements: ["NONE"]
adrs: ["NONE"]
---

# bo-3 — Classification agents

## Goal

Add the four fast agents that set kind, area, size, and priority. Each returns one label.

## Owned paths

- `plugins/triaging-gh-issues/agents/issue-kind-classify.md`
- `plugins/triaging-gh-issues/agents/issue-area-classify.md`
- `plugins/triaging-gh-issues/agents/issue-size-classify.md`
- `plugins/triaging-gh-issues/agents/issue-priority-classify.md`

## Deliverables

| Agent | Determination |
| --- | --- |
| `issue-kind-classify` | `kind/bug`, `kind/feature`, `kind/docs`, or `kind/question` |
| `issue-area-classify` | `area/product`, `area/skills`, or `area/workflows` |
| `issue-size-classify` | `size/s`, `size/m`, `size/l`, or `size/xl` |
| `issue-priority-classify` | `priority/p1`, `priority/p2`, `priority/p3`, or `priority/p4` |

`issue-priority-classify` returns `priority/p1` when the bead has `contributor` and the issue already says `p1`. It does not require `approver`. It never returns `p0`.

## Acceptance

- Each file has YAML frontmatter with `name`, `version`, and a one-sentence description, and returns fenced JSON whose `data.determination` is exactly one label from its family.
- No agent in this sprint sets `dup/`, `phase/`, `arch/`, `security/`, or `status/verified`.
