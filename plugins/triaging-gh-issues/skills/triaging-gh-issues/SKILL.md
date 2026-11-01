---
name: triaging-gh-issues
version: 1.0.0
description: Deploy one triage agent when its label is missing. Use for a GitHub issue or pull request that needs a bead, one label, or a close.
requires:
  cli:
    - name: bd
      minimum_version: 1.3.0
    - name: gh
---

# Triaging GitHub issues

## Step 1 — Verify CLI Installation

```bash
command -v bd && bd version
command -v gh && gh --version
```

If either is missing or `bd` is older than 1.3.0, read
[`references/installation-and-troubleshooting.md`](references/installation-and-troubleshooting.md)
and stop.

## Deploy

```bash
python3 scripts/next.py --login <login> --bead <id> --labels <comma> --priority <n> --repo .atm-bd/triage.toml
```

Deploy `data.agent` with the Agent Runner at the registry version. Write
`data.role_labels` and the agent's `data.determination` on the bead and the
GitHub issue. On `data.hold`, add the blocks edge and deploy nobody. On
`data.stop` of `duplicate`, close with `Duplicate of #N`. On `phase-done`,
add the patch label from `--version` and deploy nobody.

`--close` is the triage-close cron. `--version <x.y.z>` prints the next patch label.

| `data.agent` | When |
| --- | --- |
| `issue-import` | no bead |
| `issue-duplicate-judge` | no `dup/` |
| `issue-phase-match` | no `phase/` |
| `issue-phase-done` | `phase/<bead>` and no `phase-done/` |
| `issue-overlap-judge` | no `overlap/` |
| `issue-prpair-judge` | no `prpair/` |
| `issue-kind-classify` | no `kind/` |
| `issue-area-classify` | no `area/` |
| `issue-size-classify` | no `size/` |
| `issue-priority-classify` | no `priority/` |
| `issue-report-verify` | `status/needs-triage` |
| `issue-gap-classify` | `status/unverified` and no gap label |
| `issue-arch-classify` | no `arch/` |
| `issue-security-classify` | no `security/` |
| `issue-plan-write` | arch and security set, no `status/planned` |
| `plan-accept` | `status/planned` and no plan decision |
| `pr-author-credit` | `prpair/#N` and a replacement pull request |
| `issue-landed-record` | close cron, no pr and commit |
| `issue-close-mark` | `LANDED` and `QA-APPROVED` `items=all` |
| `issue-release-close` | release label, `status/close`, release published |

Agent instructions stay in the agent file.
