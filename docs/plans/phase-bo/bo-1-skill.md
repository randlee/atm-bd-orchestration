---
id: bo-1
title: Skill, config, and gates
difficulty: normal
relation: root
requirements: ["NONE"]
adrs: ["NONE"]
---

# bo-1 — Skill, config, and gates

## Goal

Create the `triaging-gh-issues` plugin and the skill that deploys one agent when the label it owns is missing.

## Owned paths

- `plugins/triaging-gh-issues/.claude-plugin/`
- `plugins/triaging-gh-issues/manifest.yaml`
- `plugins/triaging-gh-issues/skills/triaging-gh-issues/`
- `plugins/triaging-gh-issues/agents/registry.yaml`

## Deliverables

1. Plugin `plugin.json` and `manifest.yaml` for `triaging-gh-issues`.
2. Skill `triaging-gh-issues` with `bd` and `gh` checked before any agent runs, and `references/installation-and-troubleshooting.md`.
3. A reader for `~/.atm-bd/config.toml` (`contributor.logins`, `approver.logins`) and `.atm-bd/triage.toml` (`contributor.logins`, `pr_target`, gate holds).
4. Gate checks from the phase plan: whitelist, approver, priority, risk. A match records a hold and the skill deploys no agent for that point.
5. `agents/registry.yaml` listing every agent named in the phase plan, with a version. This sprint does not write the agent files.

## Acceptance

- Home-file logins are not written into the repo.
- A login on global `approver.logins` is `approver` and `contributor`. A login on either contributor list is `contributor`. Any other login stays blank.
- `contributor` absent holds at `gates.whitelist.holds`. `approver` holds only when `gates.approver.holds` is non-empty.
- The skill deploys from a missing label. It stops when the bead is closed or `phase-done/yes` is set.
- Label writes on the bead are mirrored to the linked GitHub issue or pull request.
