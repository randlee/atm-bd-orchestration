# Bead relationship diagrams (for review)

These diagrams are for Rand to review. They change no code. Nothing in them is
adopted until Rand approves it. Rand's rulings are listed under "Decided".
Every choice still open is listed under "Open decisions" and is drawn on the
diagram it affects.

The to-be diagrams draw Rand's target model. The sprint bead is a container
with three children: the assigned dev task, the sanity task and the QA task.
Blocking findings from a failed QA become children of the sprint bead, so the
sprint cannot close until they are fixed. Each blocking finding gets its own
fix, sanity and QA group. Important and minor findings are filed against the
phase instead and never block a sprint. A dependent sprint `blocks` either on
the predecessor's initial sanity bead ("normal") or on its sprint bead
("tight"). An sc-compose beads formula pours both kinds of group. A mock
script stands in for sc-compose until its attach operation exists. A
post-pour script then adds the edges a formula cannot express.

The starting point is the existing schema and validator:
`plugins/atm-bd-orchestration/skills/atm-beads/scripts/bead_schema.py`
(`SprintBead`, `SanityBead`) and `validate-plan`. The validation work these
diagrams prepare is to extend that schema with finding (including severity)
and QA models, and to add an ATM-to-bead alignment check.

| File | Level | Shows |
| --- | --- | --- |
| [01-phase-as-is.md](01-phase-as-is.md) | phase | root, sprints, cross-sprint edges, plan review, phase-end review, release, workflow-issue beads, `sprints.jsonl`, as they are today |
| [02-phase-to-be.md](02-phase-to-be.md) | phase | the same with sprint containers, poured groups, "normal" and "tight" edges, the phase-level home of important and minor findings, `current-phase.toml` |
| [03-sprint-as-is.md](03-sprint-as-is.md) | sprint | phase-d data for one sprint, and what the package templates and scripts create today |
| [04-sprint-to-be.md](04-sprint-to-be.md) | sprint | the sprint triple, the blocking-finding triple, a second fix round, with schema models |
| [05-lifecycle.md](05-lifecycle.md) | sprint | ready, claim and close order; where verdict, severity and round are written; where the logs are appended; edge-per-pair options A, B and C |
| [06-correlation.md](06-correlation.md) | phase | bead id equals ATM task id, `current-phase.toml`, the ATM-to-bead alignment check |
| [07-sc-compose-formula.md](07-sc-compose-formula.md) | detail | the three stages (sc-compose pour, post-pour script, hand or script), formula inputs, package location and future repo override, the exact beads and edges poured for a sprint and for a blocking finding, resume-safe attach |

## Conventions used in every diagram

- `p` is a neutral bead prefix. The example data is sc-observability phase-d,
  where `p` is `obs` (for example `p-d-29` is `obs-d-29`).
- An arrow goes from the bead that holds the dependency record to the bead it
  depends on, and its label is the exact bd dependency type. `A -->|blocks| B`
  means A waits for B. `A -->|parent-child| B` means A is a child of B.
  `A -->|discovered-from| B` means A was found while working B.
- Who creates a bead or edge. There are three stages:
  1. **poured by sc-compose (mock for now)**: a dashed, bold purple node
     inside a subgraph titled "poured by sc-compose (mock): `<formula>`". A
     thick arrow (`==>`) is an edge the formula pours. A formula can pour only
     `parent-child` (attach) and `blocks` between its own steps.
  2. **added by the post-pour script**: a dotted arrow (`-.->`) labeled with a bd
     type. The post-pour script runs right after the pour and adds `validates`,
     `discovered-from` and cross-sprint `blocks`.
  3. **created by hand or by a script**: solid nodes and solid arrows (`-->`).
     This covers a template rendered and loaded with `bd import`, a package
     script such as `sanity-create-findings`, and the lead running `bd create`
     or `bd dep add`. Node colors say which: blue for a template, green for a
     script, orange for hand.
  - Files (not beads) are drawn as parallelograms. A dashed arrow whose label
    is not a bd type, to or from a file, is a lookup, not a bd edge.
- bd facts verified on bd 1.3.0 (5f99d05f) in a scratch database on
  2026-10-03:
  - bd keeps one dependency type per bead pair. Adding `blocks` where
    `validates` exists fails with "dependency already exists with type".
  - `validates` does not gate readiness.
  - A parent with an open `blocks` dependency hides its children from
    `bd ready`. The container itself appears in `bd ready` once it is
    unblocked, even while its children are open.
  - `bd close` refuses a parent that has open children unless `--force` is
    passed.

## Decided (Rand, 2026-10-03)

| # | Decision | Ruling | On |
| --- | --- | --- | --- |
| Q1 | Fix groups for blocking findings | Every blocking finding gets its own fix bead, plus its own sanity and QA beads, independent of every other finding: one finding, one fix, as in the old triage/TTL model. The group attaches under the finding (confirmed). The sc-compose beads formula will be extended for "advanced pouring", building on the formula's existing YAML variable header; that extension lands in sc-compose. | 04, 07 |
| Q2 | Important and minor findings | Filed against the phase, normally under a feature bead, not under the sprint. Idle dev agents pick them up by priority. They never block a sprint from closing. | 02, 04 |
| Q3 | Sanity-FAIL findings | bd will not close a bead while any child is open. Sanity findings are children of the dev bead, so they hold the dev bead open, and the dev bead holds its sprint open. | 03, 04, 05 |
| Q4 | Who closes the sprint bead | The team lead closes it once all of its blocking findings are closed. | 02, 04, 05 |
| N1 | Where formulas live | In the package for now: `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/formulas/`. Later (future), a repo may hold an override of the package default. | 07 |
| N4 | Who adds the edges a formula cannot express | sc-compose pours each formula (a mock script for now, while a separate agent writes it). A post-pour script then adds `validates`, `discovered-from` and cross-sprint `blocks`. | 02, 04, 07 |
| N7 | Repo override of a package formula | `.atm-bd/formula/`, committed to git. `.atm-bd/` also holds the untracked per-checkout `current-phase.toml`, so `.gitignore` has `.atm-bd/*` then `!.atm-bd/formula/`. (`.atm-beads/` was the sc-obs name; the folder is `.atm-bd/`.) | 06, 07 |
| N8 | The post-pour script | A script that takes one sprint, a list of sprint beads, or every sprint in a phase. It has a validate mode and creates only what is missing, so re-running it after sprints are added is safe. It runs after planning and before plan review; planning stays out of it. | 05, 07 |
| N9 | Sanity | A simple gate: a sanity bead only signals that the sanity agent must run on its parent sprint. Its result reads like "bead-7.deliverable-2 NOT complete". Ideally JEV-only once JEV is qualified, with JEV's output holding all the data. No `discovered-from` edge and nothing beyond what exists today. | 04, 05, 07 |
| N10 | Who closes a blocking finding | quality-mgr, after the filing reviewer verifies the fix | 04, 05, 07 |

The dev-sanity role points at a team member with no agent file, today
`atm-sanity`. dev-sanity may later collapse into one agent file, since
dev-sanity-llm and dev-sanity-jev are merged.

Future (not a decision, noted in 06): the atm-bd app will run a cron task that
analyzes state and sends the lead any assignments it missed. Sanity and
quality-mgr beads will be assigned automatically with
`atm task assign --template --vars`.

Note on E1 option B: with the post-pour script, option B is feasible. The
formula pours the sanity bead, and the post-pour script adds its `validates`
edge. Its trade-off is unchanged: plain `bd ready` stops being the queue.

## Open decisions

Each decision is numbered and drawn on the diagram it affects. C, E and T
items come from the review brief. N items surfaced while drawing.

| # | Decision | Options | On |
| --- | --- | --- | --- |
| C1 | Verdict source | (a) derive the verdict from status and graph. That misjudges PASS with minor findings, because minor findings stay open. It turns a FAIL into a PASS retroactively when the findings close. A sanity FAIL keeps the bead open. Fix rounds file no findings. (b) Required schema metadata written when the checker closes: `verdict` (PASS, FAIL or CANNOT_RUN) and `round`, or the ATM close status. The graph is then only a validate-time consistency check. | 04, 05 |
| C2 | Round history | one checker bead per round, never reopened, or the reopen and append-notes flow used today | 04, 05 |
| C3 | What QA validates | (a) the checked bead, at the same PR head the sanity check checked, or (b) the sanity bead. Separately, whether the sanity-then-QA order is its own edge. | 04, 05 |
| C4 | QA findings under an already-closed checked bead | `parent-child` acts as a closure gate, or only groups the findings. Is severity required finding metadata? | 03, 04 |
| C5 | Integration branch authority | (a) `current-phase.toml`, or (b) root bead `metadata.integration_branch` is authoritative and the toml is validated against it | 02, 06 |
| C6 | ATM alignment scope | Check only ATM tasks whose id is a bead under the root. An `in_progress` bead must have a live task. Statuses must agree. ATM tasks with no bead are ignored. | 06 |
| C7 | Types for workflow-issue class beads (chore?) and for the phase release bead | Pick a type for each, so classification needs no catch-all | 01, 02 |
| C8 | Phase-d label data | One-time migration script after phase-d ends, with no runtime label parsing; or keep reading labels | 01, 03 |
| E1 | Edge per pair: the same pair cannot carry both "sanity `validates` dev" and "sanity `blocks` on dev" | A, B or C. Each is drawn with its trade-off in 05; none is recommended. | 04, 05, 07 |
| T1 | Classification | Use `issue_type` (built-in, or custom via `bd config set types.custom`, which is per database) or schema metadata. Either way, no `stage:` labels. | 02, 04 |
| N2 | Ids of poured beads | `sprints.jsonl` names each sanity bead id at plan time. Native `bd mol bond --ref` makes ids like `<parent>.<ref>.<step>`, and plain `bd mol pour` makes generated ids. | 02, 07 |
| N3 | Which bead validates against `SprintBead` | the sprint container (deliverables, branch, `pr_target`), or the dev child. `SanityBead.metadata.dev_bead` must name the bead its `blocks` edge points at. | 04 |
| N5 | Intermediate workflow container | #613 asks whether children attach directly under the sprint or under a molecule root | 07 |
| N6 | Encoding "tight" in `sprints.jsonl` | add a field to the tuple, or name the predecessor's sprint id instead of its sanity id | 02 |
| N11 | Finding-group pours | The post-pour script is defined over sprint beads. Does it, or the lead by hand, run the finding-group pour and its edges when QA files a blocking finding? | 05, 07 |

Live bugs D1 to D7 are deliberately left out of these diagrams.
