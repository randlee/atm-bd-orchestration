---
id: bo-6
title: Close and credit agents
difficulty: fast
relation: must_follow
depends_on: ["bo-1"]
requirements: ["NONE"]
adrs: ["NONE"]
---

# bo-6 — Close and credit agents

## Goal

Add the agents that record landed work, mark `status/close`, close at the patch release, and credit a rewritten pull request.

## Owned paths

- `plugins/triaging-gh-issues/agents/issue-landed-record.md`
- `plugins/triaging-gh-issues/agents/issue-close-mark.md`
- `plugins/triaging-gh-issues/agents/issue-release-close.md`
- `plugins/triaging-gh-issues/agents/pr-author-credit.md`

## Deliverables

| Agent | Determination |
| --- | --- |
| `issue-landed-record` | pull request number and full commit sha, or `landed/none` |
| `issue-close-mark` | `status/close` |
| `issue-release-close` | `closed`, or the missing check |
| `pr-author-credit` | `Credits: @login in #<original>` |

`issue-landed-record` writes `LANDED: pr=#<n> commit=<full-sha>` when the work has a merged pull request and those two values are missing.

`issue-close-mark` returns `status/close` only when `LANDED` and `QA-APPROVED` with `items=all` are both present.

`issue-release-close` closes when the patch release is published, the issue has that release label and `status/close`, `QA-APPROVED` has `items=all` and the pull request merged, and `FIXED-RELEASED` shows that commit in the release. Otherwise it reports which check is missing and leaves the issue open.

`pr-author-credit` runs when `prpair/#N` is set and a replacement pull request is opened. Replacement commits include `Co-authored-by` from the original author.

## Acceptance

- Each file has YAML frontmatter with `name`, `version`, and a one-sentence description, and returns fenced JSON with one determination.
- `issue-close-mark` does not close the issue.
- `issue-release-close` does not add `status/close`.
- `pr-author-credit` does not close either pull request.
