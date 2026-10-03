# atm-bd-orchestration

Bead-driven phase orchestration for ATM agent teams, as one installable package:

| Skill / agent | What it is |
| --- | --- |
| `skills/atm-beads` | the phase plan as a beads graph: plan templates, `validate-plan`, the pydantic bead schemas, `resolve-role`, the plan contract, the sprint index scripts |
| `skills/atm-bd-orchestration` | dispatch, dev-sanity, QA and stack landing driven by `bd ready`: assignment gates, dispatch and close templates, the `dev-sanity` and `quality-mgr` role sheets, sanity run history, the phase-end post-mortem (with JEV screening) |
| `skills/sprint-report`, `skills/sprint-review` | sprint status tables and dependency DAGs from live beads; the sprint review command |
| `agents/dev-sanity.md` | the dev-sanity coordinator the two directives below share |
| `agents/dev-sanity-llm.md`, `agents/sc-sanity-llm.md` | the LLM dev-sanity teammate and its per-deliverable subagent |
| `agents/dev-sanity-jev.md`, `agents/sc-sanity-jev.md` | the same pair for a Jev (typesafe.ai) sanity check |
| `assets/scripts/jev_client.py` | the Jev transport, placed at `<repo>/scripts/jev_client.py` |

The skills run repository-relative scripts (`.claude/skills/<skill>/scripts/...`)
and dispatch templates that ATM agents execute inside the consuming repository,
so the package is installed **into a repository's `.claude/` (and optionally
`.codex/`) directory**, not used from the plugin cache. Marketplace and plugin
manifests exist so Claude Code can discover it; `install.py` puts it to work.

## Install

Requirements in the consuming repository: `.atm.toml` with `[atm] default_team`,
`.claude/agents/registry.yaml` with `roles.dev-sanity` (and a `bead_prefix`, or
`issue-prefix` in `.beads/config.yaml`), a git `origin` remote, and `sc-compose`,
`atm`, `bd`, `jq`, `gh`, `python3` with PyYAML and pydantic on PATH (`prepare()` checks
sc-compose, PyYAML and pydantic). Jev sanity checks and post-mortem screening also
need `TYPESAFE_API_KEY` in the agent's environment at run time; without it
`scripts/jev_client.py --startup` reports `SANITY.JEV_UNAVAILABLE` and the LLM
directive stays in use.

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

Sources: sc-observability `develop` at f2ebe1bc plus open PR #933 at 07ad4d26
(`fix/jev-post-mortem-workflow`, the JEV post-mortem role and context workflow),
with every repository- and team-specific string replaced by an install-time value
or a neutral example. Recheck the JEV files if #933 changes before it merges.
See `CHANGELOG.md`.

## Package-only changes pending upstream

Changes below are not yet in the upstream source. The next sync keeps each one
until upstream carries it, then drops it from this list.

- Upstream PR #936 at d566149d (unmerged), applied verbatim ahead of its merge
  (issue #8): `skills/atm-beads/templates/sprint-bead.json.j2` (version 0.3.0,
  required `difficulty` rendered into `metadata`, `stage:sprint` label) and
  `skills/atm-beads/examples/sprint-bead-vars-d-{4,5}.json` (`difficulty`).
- Fix-round reviewer scope (ruling 2026-10-02; package 0.2.3). On a fix round
  (`carry_forward` set, `round` above 1, or a `fix/` branch) `req-qa`, `arch-qa`
  and `rust-qa-agent` run, and `ruthless-boundary-qa`,
  `rust-best-practices-agent` and `rust-service-hardening-agent` only re-check
  their own carried ids, scope-locked:
  - `skills/atm-bd-orchestration/templates/qa-template.xml.j2` (2.3.0): render
    guard for `round` above 1 without `carry_forward`; `fix_round` and derived
    `qa_round`; step d fixed allowlist and `fix-round-scope owned`/`filter`;
    step g runs `fix-round-scope check` before a fix-round `bd import`.
  - `skills/atm-bd-orchestration/templates/ruthless-boundary-qa-assignment.json.j2`
    (2.1.0): required `qa_round`; trimmed-scope `locked` flag; refuses
    `qa_round` above 1 without own ids.
  - `skills/atm-bd-orchestration/templates/plan-review-template.xml.j2` (1.3.0):
    step c passes `qa_round`; the fix-round clause limits `ruthless-boundary-qa`
    to carried findings it owns.
  - `skills/atm-bd-orchestration/examples/ruthless-boundary-qa-assignment-vars.json`:
    `"qa_round": 2`.
  - `skills/atm-bd-orchestration/roles/quality-mgr.md` "Reviewers": the
    fix-round sentence.
  - New `skills/atm-bd-orchestration/scripts/fix-round-scope` and
    `scripts/tests/test_fix_round_scope.py`; `FixRoundReviewerScopeTests` in
    `scripts/tests/test_templates.py`.
