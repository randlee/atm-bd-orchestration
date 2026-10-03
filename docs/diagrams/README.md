# Bead relationship diagrams (for review)

These diagrams are for Rand to review. They change no code. Nothing in them is
adopted until Rand approves it; every choice still open is listed below under
"Open decisions" and is drawn on the diagram it affects.

The to-be diagrams draw Rand's target model. The sprint bead is a container
with three children: the assigned dev task, the sanity task and the QA task.
Blocking findings from a failed QA become children of the sprint bead, so the
sprint cannot close until they are fixed. Each blocking finding gets its own
fix, sanity and QA group. A dependent sprint `blocks` either on the
predecessor's initial sanity bead ("normal") or on its sprint bead
("tight"). An sc-compose beads formula pours both kinds of group.

The starting point is the existing schema and validator:
`plugins/atm-bd-orchestration/skills/atm-beads/scripts/bead_schema.py`
(`SprintBead`, `SanityBead`) and `validate-plan`. The validation work these
diagrams prepare is to extend that schema with finding (including severity)
and QA models, and to add an ATM-to-bead alignment check.

| File | Level | Shows |
| --- | --- | --- |
| [01-phase-as-is.md](01-phase-as-is.md) | phase | root, sprints, cross-sprint edges, plan review, phase-end review, release, workflow-issue beads, `sprints.jsonl`, as they are today |
| [02-phase-to-be.md](02-phase-to-be.md) | phase | the same with sprint containers, poured triples and `current-phase.toml` |
| [03-sprint-as-is.md](03-sprint-as-is.md) | sprint | phase-d data for one sprint, and what the package templates and scripts create today |
| [04-sprint-to-be.md](04-sprint-to-be.md) | sprint | the sprint triple, the blocking-finding triple, a second fix round, with schema models |
| [05-lifecycle.md](05-lifecycle.md) | sprint | ready, claim and close order; where verdict, severity and round are written; where the logs are appended; edge-per-pair options A, B and C |
| [06-correlation.md](06-correlation.md) | phase | bead id equals ATM task id, `current-phase.toml`, the ATM-to-bead alignment check |
| [07-sc-compose-formula.md](07-sc-compose-formula.md) | detail | formula inputs, file location, the exact beads and edges poured for a sprint and for a blocking finding, resume-safe attach |

## Conventions used in every diagram

- `p` is a neutral bead prefix. The example data is sc-observability phase-d,
  where `p` is `obs` (for example `p-d-29` is `obs-d-29`).
- An arrow goes from the bead that holds the dependency record to the bead it
  depends on, and its label is the exact bd dependency type. `A -->|blocks| B`
  means A waits for B. `A -->|parent-child| B` means A is a child of B.
  `A -->|discovered-from| B` means A was found while working B.
- Who creates a bead or edge:
  - **poured**: a dashed, bold node inside a subgraph titled
    "poured by `<formula>`". A thick arrow (`==>`) is an edge the formula pours.
  - **script**: a dotted arrow (`-.->`) is an edge a package script adds,
    because a formula cannot express it (see 07).
  - **template**: a rendered `.json.j2` template loaded with `bd import`.
  - **hand**: the lead runs `bd create` or `bd dep add`.
  - Files (not beads) are drawn as parallelograms. A dashed arrow to or from a
    file is a lookup, not a bd edge.
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

## Open decisions

Each decision is numbered and drawn on the diagram it affects. C, E and T
items come from the review brief. Q items are questions put to Rand about his
target model. N items surfaced while drawing.

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
| Q1 | Where each blocking finding's fix, sanity and QA group attaches | (a) under the finding, which then works as a container and closure gate, or (b) under the sprint, with an edge tying the finding to its group | 04, 07 |
| Q2 | Do `important` findings count as blocking? | Policy treats important as a FAIL. Important and minor findings must not be children of the sprint, or they block its close. Where do they live? | 04, 07 |
| Q3 | Sanity-FAIL findings | They are children of the dev bead today. Do they also go under the sprint and get a group? | 03, 04, 05 |
| Q4 | Who closes the sprint container, and when | bd never closes a parent automatically. The same question applies to a finding under Q1 (a). | 02, 04, 05 |
| T1 | Classification | Use `issue_type` (built-in, or custom via `bd config set types.custom`, which is per database) or schema metadata. Either way, no `stage:` labels. | 02, 04 |
| N1 | Where the formula source lives | (a) the package, (b) the sc-compose fragment library, or (c) each consuming repo. ADR-0021 fixes only where the rendered formula goes. | 02, 04, 07 |
| N2 | Ids of poured beads | `sprints.jsonl` names each sanity bead id at plan time. Native `bd mol bond --ref` makes ids like `<parent>.<ref>.<step>`, and plain `bd mol pour` makes generated ids. | 02, 07 |
| N3 | Which bead validates against `SprintBead` | the sprint container (deliverables, branch, `pr_target`), or the dev child. `SanityBead.metadata.dev_bead` must name the bead its `blocks` edge points at. | 04 |
| N4 | Who adds edges a formula cannot express | Formula steps can only `needs`/`depends_on` sibling steps (`blocks`). Cross-sprint `blocks`, `discovered-from` and `validates` must be added by (a) the sc-compose attach operation (#613) or (b) a package script after the pour. | 07 |
| N5 | Intermediate workflow container | #613 asks whether children attach directly under the sprint or under a molecule root | 07 |
| N6 | Encoding "tight" in `sprints.jsonl` | add a field to the tuple, or name the predecessor's sprint id instead of its sanity id | 02 |

Live bugs D1 to D7 are deliberately left out of these diagrams.
