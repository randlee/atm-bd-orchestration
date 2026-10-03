# Changelog

## [0.6.1] - 2026-10-03

### Changed
- `roles.dev-sanity` (`dev_sanity_member`) names a team member, which may have
  no agent file (atm-core's `atm-sanity`, a roster member running the
  dev-sanity directive). The installer no longer checks it against
  `.claude/agents/<name>.md`; `qa_member` and `reviewers_round1` keep the
  check. There is no ATM roster lookup (CI has no ATM). Rand ruling 2026-10-03.

### Migration from 0.6.0
Rerun the install.

## [0.6.0] - 2026-10-03

### Changed
- Dev sanity triages reviewer findings and disagreements before close
  (upstream sc-observability PR #966 at 05367233, unmerged; applied as close to
  verbatim as the package allows). Every sanity run executes both reviewers
  (`sanity-llm`, `sanity-jev`), then a `sanity-selected` merge picks one
  whole reply per deliverable from a strict selection array; only the selected
  result creates finding children (`sanity-create-findings --reviewer
  sc-sanity-selected`), and checker defects create none. `sanity-split` no
  longer takes `--reviewers`; its manifest always lists all three reviewers.
  Reviewer assignments carry a `context` array.
  - `dev-sanity-template.xml.j2` 2.2.0: `reviewers` is no longer a variable
    (upstream 1.9.0 removed it; the package's config-driven `lead`, `cc` and
    `lint_command` stay required). `dev-sanity-assignment.json.j2` 1.1.0,
    `dev-sanity-complete.md.j2` 1.2.0, `sanity-run-record.json.j2` 2.0.0,
    `sanity-run-table.md.j2` 1.5.0 (upstream's numbers; `sanity-run-record` is
    major for its new required variables, as upstream 05367233).
  - Sanity ledger (OTel log contract, upstream format): history is appended in
    order LLM, JEV, SEL with the selected `final_verdict` on every row; records
    add `final_verdict` and `selection` (null except on SEL rows); the run
    table adds `Pick` and `Match` columns.
  - `agents/dev-sanity.md`, `dev-sanity-llm.md`, `dev-sanity-jev.md`,
    `sc-sanity-llm.md`, `sc-sanity-jev.md` and `roles/dev-sanity.md` follow.
  - Tests: `scripts/tests/test_sanity_selected.py` (new); upstream's root
    `scripts/tests/test_sanity_{merge,run_history,split}.py` now ship beside
    the skill's `scripts/tests` with import paths adjusted.
- Fix verification wording from upstream #967, merged into #966 at 05367233
  (filing-reviewer-only fix verification, now with plan-review text). The
  package's 0.5.0 rule stays in force; upstream's wording replaces the
  package's where both say the same thing, and the package-only enforcement
  (`fix-round-scope` checks, plan finding lines naming their reviewer,
  plan-scope-reviewer `round_index` wiring) stays.
  - `qa-template.xml.j2` 4.2.0: in a fix verification (`carry_forward` set) steps
    f and g1 do not render; steps b, e, g and i take upstream's fix-verification
    text; stack-discipline adds upstream's fix-verification sentence. The fixer
    closes a carried finding; fix verification confirms it or reopens it and no
    longer closes it itself. A fix-round PASS is a PASS from the filing reviewer
    and every carried finding confirmed fixed and closed (no deliverable
    completion term). `<fix-verification-precedence>` names only the steps that
    render in a fix round (c, e, g, i). Required variables unchanged.
  - `plan-review-template.xml.j2` 3.2.0: every dev bead and the root are piped
    before the branch, and a fix round's filing reviewers read all of them
    (still locked to their own ids); step d does not render in a fix round;
    round 1's plan-scope-reviewer "runs in full"; `<fix-verification-precedence>`
    names steps c and e.
  - `plan-scope-reviewer-assignment.json.j2` 1.1.1: upstream's description.
  - `roles/quality-mgr.md`: upstream's fix-round paragraph under "Fix
    verification takes precedence" (QA no longer closes the original finding),
    upstream's carried-finding line, refusal paragraph and Findings scope line; `SKILL.md`: upstream's qa-complete row and plan-scope-reviewer row.

### Migration from 0.5.0
Rerun the install. A lead that passed `reviewers` to `dev-sanity-template.xml.j2`
drops it.

## [0.5.0] - 2026-10-03

Breaking: the configuration contract and `qa-template.xml.j2` required
variables changed.

### Changed
- Fix verification is filing-reviewer-only (ruling 2026-10-03; upstream
  sc-observability 18d7158f). A review of an assigned fix is not a sprint
  review, regardless of round number or inherited `review_mode`: only the agent
  that filed the carried finding (`metadata.reviewer`) is dispatched, locked to
  its `metadata.finding_ref` and acceptance criterion. It reports
  fixed/open/regressed for that finding and files no new findings; no automatic
  `req-qa`/`arch-qa`/`rust-qa-agent`, no `ceremony-finding-screen`, no sprint
  sweep. Required CI stays a separate merge requirement. On verified PASS,
  quality-mgr reconciles the original finding bead's closure, not only the QA
  task. This replaces the 0.2.3 fix-round rule.
  - `roles/quality-mgr.md` "Reviewers": the upstream "Fix verification takes
    precedence" text; sprint rounds 1–2 stay sprint reviews with
    `reviewers_round1`.
  - `qa-template.xml.j2` 4.0.0: `reviewers_fix_round` and
    `reviewers_scope_locked` are no longer variables; adds upstream's
    `<fix-verification-precedence>`. A fix verification is `carry_forward`
    set, whatever the round or branch; `round` above 1 or a `fix/` branch no
    longer makes one (the `FIX_ROUND_WITHOUT_CARRY_FORWARD` render guard is
    gone), so a sprint round 2 or a parallel quick fix, which has no original
    finding to verify, renders as a sprint review with `reviewers_round1`. Step g files no finding bead in a fix verification; step i's PASS
    is every carried finding verified fixed. The `.sc/qa-log` rows are
    unchanged (`tested` is still the carried finding_refs).
  - `scripts/fix-round-scope`: no longer reads the configuration. `owned`
    prints every carried finding's filing reviewer with its own ids (a carried
    finding without `metadata.reviewer`/`finding_ref` is an error); `check
    --carried --dispatch` exits 5 (`FIX_ROUND_DISPATCH_MISMATCH`) unless the
    dispatch set is exactly those reviewers; `filter` accepts any filing
    reviewer. `check --findings` is gone (a fix verification imports nothing).
  - `config/atm-bd-orchestration.yaml.j2` 1.0.0: `reviewers_fix_round` and
    `reviewers_scope_locked` removed; `reviewers_round1` is the only reviewer
    list.
- Plan-review fix rounds are filing-reviewer-only too (ruling 2026-10-03).
  From plan round 2 on, `req-qa` and `arch-qa` are not re-run and
  `plan-scope-reviewer` does not run in full: only the filing reviewer of each
  carried finding runs, locked to it, with no ceremony screen and no new
  findings; `validate-plan` still runs, like required CI.
  `plan-review-template.xml.j2` 3.0.0 (`reviewers_scope_locked` is no longer a
  variable) adds a `<fix-verification-precedence>` block. Plan findings stay
  report lines, not beads, and now name their filing reviewer:
  `<bead> <severity> <reviewer> <field>: <what is wrong>` (`validate-plan` for
  step b findings). `scripts/fix-round-scope --plan` reads the carried lines,
  and `check --plan --dispatch` refuses any set other than their filing
  reviewers (`validate-plan` itself is step b, never dispatched).
  `plan-scope-reviewer-assignment.json.j2` 1.1.0 (as atm-core 2676a514)
  locks a round after the first to the reviewer's own carried ids, sets
  `findings_scope_locked`, and refuses to render
  (`FIX_ROUND_SCOPE_LOCK_REQUIRED`) without them; `plan-review-template.xml.j2`
  3.0.1 step c passes it `round_index` and those ids.
- Orchestration refusals reuse workflow class beads (upstream
  sc-observability 87a26739, #954). The refusal paths of `dev-template.xml.j2`
  3.1.0, `dev-fix.xml.j2` 1.1.0, `fix-assignment.xml.j2` 3.1.0,
  `dev-sanity-template.xml.j2` 2.1.0, `qa-template.xml.j2` 4.0.0,
  `plan-review-template.xml.j2` 2.1.0 and `review-template.xml.j2` 3.1.0 no
  longer render and import a new `<task>-wf-<CODE>` bead per task: they append
  the task id, head, command and failure evidence to an existing workflow class
  bead for the same failure signature and cite it, or, when no class matches,
  report the signature to the lead for classification and cite that message.
  Required variables unchanged (minor bumps).
  The `roles/quality-mgr.md` and `roles/dev-sanity.md` refusal paragraphs
  say the same.

### Removed
- Source-repository text: the roster model names in
  `atm-beads/resources/dev-sanity.md`, "this phase-D run" in
  `references/post-mortem-jev.md`, "Phase D" in
  `blocking-findings-guidelines.md`, and the `omega-prime` decision owner in
  `blocking-findings-guidelines.md` and `SKILL.md` (now "the user or their
  delegate").

### Migration from 0.4.0
Rerun the install. `reviewers_fix_round` and `reviewers_scope_locked` are no
longer configuration variables: the installer reads only declared variables
from registry.yaml, so leftover keys there are ignored (delete them at
leisure), and the rendered `.claude/project/atm-bd-orchestration.yaml` no
longer carries them. `--set reviewers_fix_round=...` or
`--set reviewers_scope_locked=...` is now an install error (unknown `--set`
variable). A lead that dispatches `qa-template.xml.j2` or
`plan-review-template.xml.j2` with a var file built from `repo_config.py json`
still renders: the extra keys are ignored. Plan finding lines carried into a
round-2 plan review must name their reviewer; a line from a 0.4.0 round 1
report needs the reviewer added (its `reviewers_md` says which).

## [0.4.0] - 2026-10-02

Breaking: the install contract changed. Configuration is one rendered file, the
installer owns only what it recorded, and there are no defaults.

### Changed
- Configuration: the inputs are the `required_variables` of the new
  `config/atm-bd-orchestration.yaml.j2` (`bead_prefix`, `lead`,
  `dev_sanity_member`, `qa_member`, `worktree_base`, `test_command`,
  `lint_command`, `integration_branch_pattern`, `plans_dir`,
  `requirements_globs`, `adr_globs`, `policy_path`, `reviewers_round1`,
  `reviewers_fix_round`, `reviewers_scope_locked`), read from the consuming
  repository's `.claude/agents/registry.yaml` (top-level key of the same name;
  the three members from `roles.lead`, `roles.dev-sanity`,
  `roles.quality-mgr`) or `--set`. Install renders it with
  `sc-compose render --strict` into `.claude/project/atm-bd-orchestration.yaml`;
  a missing variable fails the install and is named with the registry key that
  sets it. Unknown `--set` keys are rejected.
- No defaults or guesses: `lead` no longer defaults to `team-lead`,
  `worktree_base` is no longer guessed, `bead_prefix` no longer falls back to
  `.beads/config.yaml`, and `team` (rendered nowhere) is no longer an input.
  `.atm.toml` is no longer read.
- The resolved `lead`, `dev_sanity_member` and `qa_member` are written into
  `roles:` of registry.yaml (the rest of the file is kept as written), so
  `resolve-role` works after any successful install.
- Ownership: `.claude/project/atm-bd-orchestration.lock.json` records the
  version and the sha256 of every file the install wrote (skills, agents,
  `scripts/jev_client.py`, the config file). A rerun replaces recorded files the
  user has not modified, removes unmodified files the new version no longer
  ships, and fails naming every modified file. It never writes over a file it
  does not own and fails when a target skill directory exists that it does not
  own. A failed install writes nothing. `--force`, `--print-vars`, `DROPPED` and
  `INVENTORY` are gone.
- Install fails unless `.beads/metadata.json` shows `dolt_mode: server`
  (`BEADS_NOT_SERVER_MODE`), and unless every agent named in `qa_member`,
  `dev_sanity_member` and the three reviewer lists has `.claude/agents/<name>.md`
  (in the repository or shipped by this package).
- `--dest` must be a repository's `.claude` or `.codex` directory.

### Added
- `config/legacy-owned.json` (generated by `tests/gen_legacy_owned.py`): the
  sha256 of every file 0.1.0-0.2.3 shipped, used once to migrate an install that
  has no lock file. Delete it once no repository carries a pre-0.4.0 install.
- `conftest.py` (test path setup; keeps pytest out of the uninstalled skill
  suites) and CI: `.github/workflows/tests.yml` runs the package tests on
  ubuntu and macos with sc-compose 1.6.1.

### Migration from 0.x
Add the variables above to `.claude/agents/registry.yaml` (the install error
lists every missing one), then rerun the install. The first 0.4.0 install finds
no lock file and adopts existing files whose bytes are what 0.4.0 installs or
what some 0.x version shipped; it fails, naming them, on any other file at a
path it ships, and on a skill directory with no such file. A rendered file (one
listed under `render:`) from 0.x is adopted only when it equals what 0.4.0
renders with the current values; if you did not edit a refused file, delete it
and rerun. A copy that was synced from upstream rather than installed by the
package matches no shipped bytes: remove the package's skill directories and
agents and install fresh.

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
