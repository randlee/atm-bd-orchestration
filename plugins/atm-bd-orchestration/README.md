# atm-bd-orchestration

Bead-driven phase orchestration for ATM agent teams, as one installable package:

| Skill / agent | What it is |
| --- | --- |
| `skills/atm-beads` | the phase plan as a beads graph: plan templates, `validate-plan`, `check-plan.jq`, `resolve-role`, the plan contract, the sprint index scripts |
| `skills/atm-bd-orchestration` | dispatch, dev-sanity, QA and stack landing driven by `bd ready`: assignment and blocking-finding gates, dispatch and close templates, the `dev-sanity` and `quality-mgr` role sheets |
| `skills/sprint-report`, `skills/sprint-review` | sprint status tables and dependency DAGs from live beads; the sprint review command |
| `agents/dev-sanity-llm.md`, `agents/sc-sanity-llm.md` | the LLM dev-sanity teammate and its per-deliverable subagent |
| `agents/dev-sanity-jev.md`, `agents/sc-sanity-jev.md` | the same pair for a jev (Codex) sanity check |

The skills run repository-relative scripts (`.claude/skills/<skill>/scripts/...`)
and dispatch templates that ATM agents execute inside the consuming repository,
so the package is installed **into a repository's `.claude/` (and optionally
`.codex/`) directory**, not used from the plugin cache. Marketplace and plugin
manifests exist so Claude Code can discover it; `install.py` puts it to work.

## Install

Requirements in the consuming repository: `.atm.toml` with `[atm] default_team`,
`.claude/agents/registry.yaml` with `roles.dev-sanity` (and a `bead_prefix`, or
`issue-prefix` in `.beads/config.yaml`), a git `origin` remote, and `sc-compose`,
`atm`, `bd`, `jq`, `python3` with PyYAML on PATH.

Standalone, from a checkout of this repository:

```bash
python3 plugins/atm-bd-orchestration/install.py --dest /path/to/repo/.claude
python3 plugins/atm-bd-orchestration/install.py --dest /path/to/repo/.codex   # skills only, no agents
python3 plugins/atm-bd-orchestration/install.py --dest /path/to/repo/.claude --print-vars
```

Through `sc-install` (synaptic-canvas), once its marketplace references this
package: `sc-install install atm-bd-orchestration --local` installs both the
`.claude` and `.codex` targets and runs `install.py` as the package's
`prepare()`/`complete()`/`cleanup()` hook.

Existing files are skipped unless `--force` is given, in both paths. Rerunning
is idempotent. A value can be overridden with `--set NAME=VALUE`; the hook reads
the same overrides from `options["args"]`.

## What install-time rendering does

`registry.yaml` is the registry of repository-specific values and of the files
they are rendered into. After the copy step, `install.py` renders those files
with `sc-compose render --strict` from the consuming repository's own config:

| Variable | Source |
| --- | --- |
| `team` | `.atm.toml` `[atm] default_team` |
| `lead` | `registry.yaml` `roles.lead` (default `team-lead`) |
| `dev_sanity_member` | `registry.yaml` `roles.dev-sanity` |
| `bead_prefix` | `registry.yaml` `bead_prefix`, else `.beads/config.yaml` `issue-prefix` |
| `workflow_issues_root` | `registry.yaml` `workflow_issues_root` (default `<bead_prefix>-workflow-issues`) |
| `repo_slug`, `repo_name` | `git remote get-url origin` |
| `repo_root`, `worktree_base` | the repository path and `../<repo_name>-worktrees` |

Everything else, including every `*.j2` dispatch template, is copied byte for
byte; the dispatch templates take their values at dispatch time from the lead's
vars files as before. `templates/workflow-issue-bead.json.j2` takes the
workflow-issues root bead as its required `parent` variable.

## Tests

```bash
cd plugins/atm-bd-orchestration
python3 -m pytest -q tests skills/atm-bd-orchestration/scripts/tests skills/atm-beads/tests skills/sprint-report/tests
python3 tests/gen_manifest.py --check   # manifest.yaml, INVENTORY and registry.yaml render list are generated
```

The install tests render into a throwaway git repository with `sc-compose` and
are skipped, with a message, when it is not on PATH.

## Provenance

Sources: sc-observability `fix/blocking-finding-gates` at 88741f937 (the top of
the stack that adds the assignment and blocking-finding gates), with every
repository- and team-specific string replaced by an install-time value. See
`CHANGELOG.md`.
