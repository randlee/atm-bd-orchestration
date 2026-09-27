# atm-bd-orchestration

Bead-driven phase orchestration for ATM agent teams, as one installable package:

| Skill / agent | What it is |
| --- | --- |
| `skills/beads-workflow` | turn approved plans into self-contained beads and polish their dependency graph |
| `skills/beads-bv` | prioritize scoped work using a fresh Dolt export and BV robot analysis |
| `skills/multi-agent-swarm-workflow` | coordinate ATM workers through assignment, implementation, and review |
| `skills/beads-compliance-and-completion-verification` | verify acceptance criteria against code, tests, sanity, QA, and merge evidence |
| `skills/atm-beads` | the phase plan as a beads graph: plan templates, `validate-plan`, the pydantic bead schemas, `resolve-role`, the plan contract, the sprint index scripts |
| `skills/atm-bd-orchestration` | dispatch, dev-sanity, QA and stack landing driven by `bd ready`: assignment gates, dispatch and close templates, the `dev-sanity` and `quality-mgr` role sheets, sanity run history, the phase-end post-mortem (with JEV screening) |
| `skills/sprint-report`, `skills/sprint-review` | sprint status tables and dependency DAGs from live beads; the sprint review command |
| `agents/dev-sanity.md` | the dev-sanity coordinator the two directives below share |
| `agents/dev-sanity-llm.md`, `agents/sc-sanity-llm.md` | the LLM dev-sanity teammate and its per-deliverable subagent |
| `agents/dev-sanity-jev.md`, `agents/sc-sanity-jev.md` | the same pair for a Jev (typesafe.ai) sanity check |
| `assets/scripts/jev_client.py` | the Jev transport, placed at `<repo>/scripts/jev_client.py` |

The four job skills form a loop: plan → prioritize → execute → verify, with
confirmed gaps returned to planning. They reuse the existing schemas, gates,
and dispatch templates below. Agent configuration comes from `.atm.toml`.
The lead knows its phase; workers use their assigned worktree and the phase
information in `docs/plans/phase-<current>/`. Concurrent phases on separate
computers retain separate assignment scope.

BV analysis requires `bv` with the robot/source-authority interface (tested
with v0.25.0) and `bd` connected to the repository's Dolt server. The helper
exports live records and filters epic descendants before BV analysis, retaining
the full export for external blocker checks. It never opens the TUI or
falls back to checked-in JSONL. Dolt remote synchronization follows the
consuming repository's procedure before exporting.

The skills run repository-relative scripts (`.claude/skills/<skill>/scripts/...`)
and dispatch templates that ATM agents execute inside the consuming repository,
so the package is installed **into a repository's `.claude/` (and optionally
`.codex/`) directory**, not used from the plugin cache. Marketplace and plugin
manifests exist so Claude Code can discover it; `install.py` puts it to work.

## Install

Requirements in the consuming repository: `.atm.toml` with `[atm] default_team`,
the lead and sanity member names (`.claude/agents/registry.yaml` `roles`, or passed with `--set`) (and a `bead_prefix`, or
`issue-prefix` in `.beads/config.yaml`), a git `origin` remote, and `sc-compose`,
`atm`, `bd`, `jq`, `gh`, `python3` with PyYAML and pydantic on PATH (`prepare()` checks
sc-compose, PyYAML and pydantic). Jev sanity checks and post-mortem screening also
need `TYPESAFE_API_KEY` in the agent's environment at run time; without it
`scripts/jev_client.py --startup` reports `SANITY.JEV_UNAVAILABLE` and the LLM
directive stays in use.

The existing installer also accepts legacy `.claude/agents/registry.yaml`
defaults. When using `.atm.toml` for agent configuration, pass the selected
members explicitly; no agent registry file is required:

```bash
python3 plugins/atm-bd-orchestration/install.py --dest /path/to/repo/.claude \
  --set lead=<lead-member> --set dev_sanity_member=<sanity-member> \
  --set bead_prefix=<prefix>
```

Select those names from the repository's `.atm.toml`; the installer does not
infer semantic roles from startup prompts. Dispatch templates accept explicit
recipient vars. Legacy `resolve-role` callers still use the registry YAML.

Standalone, when those defaults are already available:

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

`assets/scripts/jev_client.py` is also placed at `<repo>/scripts/jev_client.py`
(the path `dev-sanity-jev` and `post_mortem_jev.py` call) unless one exists (`--force`
replaces it); the repository owns it from then on. Files a newer version stops
shipping are removed from the target (`DROPPED` in `install.py`). Everything else, including
every `*.j2` dispatch template, is copied byte for byte; the dispatch templates take their values at dispatch time from the lead's
vars files as before. `templates/workflow-issue-bead.json.j2` takes the
workflow-issues root bead as its required `parent` variable.

## Tests

```bash
cd plugins/atm-bd-orchestration
python3 -m pytest -q tests assets/scripts/tests
python3 tests/gen_manifest.py --check   # manifest.yaml, INVENTORY and registry.yaml render list are generated
```

`tests/test_skill_suites.py` installs the package into a throwaway repository
(bead prefix `myp`) and runs the skills' own suites there, because they resolve
paths from the repository layout and some scripts carry install-time values.
One upstream test that reads the source repository's own phase-d plan is
deselected. The install tests need `sc-compose` and are skipped, with a
message, when it is not on PATH.

## Provenance

Sources: sc-observability `develop` at f2ebe1bc plus open PR #933 at b1ffa1ad
(`fix/jev-post-mortem-workflow`, the JEV post-mortem role and context workflow),
with every repository- and team-specific string replaced by an install-time value
or a neutral example. Recheck the JEV files if #933 changes before it merges.
See `CHANGELOG.md`.

The four job skills adapt the user-supplied `beads-workflow`, `beads-bv`,
`multi-agent-swarm-workflow`, and
`beads-compliance-and-completion-verification` packages reviewed on 2026-09-27.
They preserve plan polishing, graph-aware prioritization, coordinated workers,
and criterion-level evidence verification. `br`/SQLite and Agent Mail/NTM
procedures are replaced by `bd`/Dolt and ATM. Source-specific paths, thresholds,
and incomplete audit-runner scripts are not carried over; the new BV snapshot
helper has its own regression tests. Detailed prompts and scoring guidance
remain in each skill's references.
