---
id: a-4
title: Review agents
difficulty: normal
relation: must_follow
depends_on: ["a-1"]
requirements: ["NONE"]
adrs: ["NONE"]
---

# a-4 — Review agents

## Goal

Add the normal-difficulty agents that verify the report and set architecture and security. Each returns one label. Models are terra, opus, sol, or sonnet. `sol` is the same class as `opus`.

## Owned paths

- `plugins/triaging-gh-issues/agents/issue-report-verify.md`
- `plugins/triaging-gh-issues/agents/issue-gap-classify.md`
- `plugins/triaging-gh-issues/agents/issue-arch-classify.md`
- `plugins/triaging-gh-issues/agents/issue-security-classify.md`

## Deliverables

| Agent | Determination |
| --- | --- |
| `issue-report-verify` | `status/verified` or `status/unverified` |
| `issue-gap-classify` | `status/needs-info`, `status/needs-repro`, or `status/needs-design` |
| `issue-arch-classify` | `arch/none`, `arch/impact`, or `arch/already-exists` |
| `issue-security-classify` | `security/none` or `security/review` |

`issue-report-verify` checks that the report is still true, including when `contributor` is set. `status/verified` is what replaces `status/needs-triage`. `issue-gap-classify` runs only after `status/unverified`.

## Acceptance

- Each agent stays at 1–3KB. Review against the phase plan's Review standard. A review that adds prose fails.
- Each file has YAML frontmatter with `name`, `version`, and a one-sentence description, and returns fenced JSON whose `data.determination` is one label.
- `issue-report-verify` does not set kind, priority, arch, or security.
- `issue-gap-classify` returns one of the three gap labels and no other status.
