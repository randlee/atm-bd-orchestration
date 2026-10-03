# Changelog

## [0.2.3] - 2026-10-02

### Changed
- Fix rounds run `req-qa`, `arch-qa` and `rust-qa-agent`; `ruthless-boundary-qa`,
  `rust-best-practices-agent` and `rust-service-hardening-agent` only re-check
  their own carried finding ids, scope-locked (ruling 2026-10-02). A fix round is
  `carry_forward` set, `round` above 1, or a `fix/` branch. `qa-template.xml.j2`
  refuses `round` above 1 without `carry_forward` and gates the fix-round
  `bd import` on `scripts/fix-round-scope check`; `ruthless-boundary-qa-assignment.json.j2`
  requires `qa_round` and refuses a fix round without its own ids;
  `plan-review-template.xml.j2` passes `qa_round`.

### Added
- `scripts/fix-round-scope` (`owned`, `filter`, `check`) and its tests; render
  tests for the fix-round rules in `scripts/tests/test_templates.py`.

Package-only, pending upstream: listed in README.md. Builds on 0.2.2 (#10).

## [0.2.2] - 2026-10-02

### Fixed
- `atm-beads/templates/sprint-bead.json.j2` renders the `difficulty` that
  `SprintBead` requires and the `stage:sprint` label, so a strict render passes
  `validate-plan` check 2 (#8). Takes upstream PR #936 at d566149d verbatim ahead
  of its merge; listed under "Package-only changes pending upstream" in README.md.
- `tests/test_skill_suites.py` renders the template with both example vars in an
  installed copy and validates the metadata against `SprintMetadata`.

## [0.2.1] - 2026-10-02

### Changed
- `references/post-mortem-context-preparation.md` follows sc-observability PR #933
  head 07ad4d26 (supersedes b1ffa1ad): an oversized compound obligation may be
  decomposed into parent-mapped subpredicates. Upstream delta applied verbatim.

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
