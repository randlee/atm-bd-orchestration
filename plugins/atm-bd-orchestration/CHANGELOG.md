# Changelog

## [0.2.0] - 2026-10-02

### Changed
- Skills and agents re-mirrored from sc-observability `develop` at f2ebe1bc plus
  open PR #933 at b1ffa1ad: every in-scope file is the upstream file verbatim
  except repository-specific names and paths, replaced by install-time values or
  neutral examples. Skill, agent and template header versions are upstream's.
- The sprint index is the phase JSONL (`docs/plans/phase-<x>/sprints.jsonl`)
  validated in code and by `schemas/*.schema.json`; the sprint index schema asset
  is gone, as upstream deleted `docs/plans/sprints.schema.json`.

### Added
- `agents/dev-sanity.md`, sanity run history and record templates, the
  phase-end post-mortem with JEV screening and context collection
  (`references/post-mortem*.md`, `post_mortem_jev.py`, `post_mortem_context.py`,
  `check-review-completion.py`), `blocking-findings-guidelines.md`, the pydantic
  bead schemas (`atm-beads/scripts/bead_schema.py`, `schemas/`).
- `assets/scripts/jev_client.py`, placed at `<repo>/scripts/jev_client.py`, and its tests.
- `tests/test_skill_suites.py` runs the skills' suites in an installed copy.
- `prepare()` checks that `python3` imports pydantic and PyYAML.

### Removed
- `blocking-finding-gates.py`, `check-plan.jq`, `migrate-phase-contract`,
  `phase_contract_check.py`, `export-sprint-index`, `report-detailed.md.j2` and
  their tests and fixtures, removed upstream; `complete()` deletes them from an
  existing install.

## [0.1.0] - 2026-09-26

### Added
- First shared copy of the `atm-beads`, `atm-bd-orchestration` and `sprint-report`
  skills and the `dev-sanity-llm`, `sc-sanity-llm`, `dev-sanity-jev` and
  `sc-sanity-jev` agents, taken from sc-observability `develop` at 9ac5cd4
  (the merge of PRs #263, #262, #266 and #267: phase contract validator,
  assignment gates with enumerated refusal codes, blocking-finding R16 gates,
  epic-only top level with QA and finding beads under their sprint) with every
  repository- and team-specific string replaced by an install-time value (see
  `registry.yaml`).
- `assets/docs/plans/sprints.schema.json`, the sprint index schema; `install.py`
  also places it at `<repo>/docs/plans/sprints.schema.json` when missing.
- `install.py`: sc-install `prepare()`/`complete()`/`cleanup()` hook and standalone
  installer that renders the repository values with `sc-compose render --strict`.
- `templates/workflow-issue-bead.json.j2` takes `parent` (the repository's
  workflow-issues root bead) as a required variable instead of a hard-coded id.
