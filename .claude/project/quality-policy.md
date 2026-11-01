# Repository Quality Policy

This file contains repository-specific QA policy. Reusable agents and skills
must read this file rather than embedding repository names, commands, interfaces,
approval authorities, or temporary architectural exceptions in their prompts.

## Repository Baseline

- Default comparison branch: `main`
- Requirements index: `docs/requirements/README.md`; the repository requirements
  are the Markdown documents in `docs/requirements/`.
- Orchestration and bead workflow: `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/SKILL.md`
  and `plugins/atm-bd-orchestration/skills/atm-beads/SKILL.md`.
- Other plugin skill contracts: `plugins/atm-bd-orchestration/skills/prompt-rewrite-judge/SKILL.md`,
  `plugins/atm-bd-orchestration/skills/qa-report/SKILL.md`,
  `plugins/atm-bd-orchestration/skills/sprint-report/SKILL.md`, and
  `plugins/atm-bd-orchestration/skills/sprint-review/SKILL.md`.

## Reviewer Policy

- Initial implementation review (sprint QA-1): `req-qa`, `arch-qa`,
  `ruthless-boundary-qa`, `rust-qa-agent`, `rust-best-practices-agent`, and
  `rust-service-hardening-agent`.
- Fix verification is separate from sprint QA rounds 1–2: dispatch only the
  agent necessary to confirm the specific fix, normally the filing reviewer.
  Lock it to the original finding and acceptance criterion. No automatic
  req-qa/arch-qa/rust-qa or screening panel, no full sweep, and no new findings.
  Required CI remains a separate merge requirement.
- Plan review QA-1: `plan-scope-reviewer`, `req-qa`, `arch-qa`,
  `ruthless-boundary-qa`, `rust-best-practices-agent`,
  `rust-service-hardening-agent`, and `ceremony-qa`.
- Plan review QA-2 and later is fix verification: dispatch only the filing
  reviewer of each carried finding, locked to that finding and its original
  acceptance criterion. No screening panel, no full sweep, and no new findings.
- `ceremony-finding-screen` runs on sprint or plan QA rounds that have findings,
  before the report is posted; never on fix verification.
- Run `flaky-test-qa` earlier when tests changed or instability is suspected.
- Every QA round requires an open PR; post the rendered report to it each round.

## Validation Policy

- Lint: `just lint`
- Tests: `just test`

## Plan Naming

Use lower case in file names, branch names, front matter `id` values and
rendered template variables. Prose may capitalize phase names.
