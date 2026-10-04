# 3. Sprint level, as-is

No formula pours anything at sprint level today. Every bead comes from a
template, from a package script, or from a hand `bd create`.

## 3a. Phase-d data: sprint p-d-29

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000

  ROOT["p-phase-d (phase root)"]:::tmpl
  DEV["p-d-29 = sprint bead = dev bead<br/>task, stage:dev + stage:sprint<br/>model: SprintBead<br/>close_reason: Development complete at PR797 sha"]:::tmpl
  SAN["p-d-29-sanity<br/>task, stage:dev-sanity<br/>model: SanityBead<br/>close_reason: PASS at sha"]:::tmpl
  QA1["p-d-29-qa1<br/>task, stage:qa<br/>metadata: checked_bead, commit, round, branch, layer<br/>close_reason: FAIL: 30 findings filed"]:::tmpl
  F["p-d-29-qa1-f1 .. f30<br/>bug, stage:finding, severity:*<br/>metadata: severity, sprint_bead, found_at_commit, reviewer, finding_ref, screen"]:::tmpl
  FIX["p-d-29-qa1-fixes<br/>task, stage:dev<br/>one batched fix for all findings<br/>hand bd create"]:::hand

  DEV -->|parent-child| ROOT
  SAN -->|parent-child| ROOT
  SAN -->|blocks| DEV
  QA1 -->|parent-child| DEV
  F -->|parent-child| DEV
  F -->|discovered-from| QA1
  FIX -->|parent-child| DEV
```

**Legend.** These nodes are real phase-d beads (`p` = `obs`). The sprint bead
and the dev bead are the same bead. The sanity bead is a sibling of the dev
bead under the root, not its child. QA has no edge to the sanity bead.
Findings sit flat under the dev bead. Fixes were batched into one bead, with
no triple per finding (3c shows the fix beads in detail). Phase-wide counts: QA `blocks` sanity on 365 edges;
finding `discovered-from` QA on 779 edges; no finding is `discovered-from` a
sanity bead; only 2 `validates` edges. The verdict and the pinned sha are
parsed from `close_reason`.

**Open decisions**

1. C8: migrate the label-and-close_reason data once, after phase-d ends, or
   keep parsing it at runtime.
2. C1: the verdict in `close_reason` versus required metadata.

## 3b. What the package templates and scripts create today (main 775a073)

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000
  classDef script fill:#e6f4ea,stroke:#188038,color:#000

  ROOT["p-phase-d (phase root)"]:::tmpl
  DEV["p-d-29 dev = sprint bead<br/>sprint-bead.json.j2"]:::tmpl
  SAN["p-d-29-sanity<br/>dev-sanity-bead.json.j2"]:::tmpl
  SF["sanity finding (bug, stage:finding)<br/>sanity-create-findings<br/>metadata: severity (default blocking), sprint_bead,<br/>sanity_finding.sanity_bead, commit_checked"]:::script
  QA["p-d-29-qaN (round N)<br/>qa-bead.json.j2, created at sanity PASS"]:::tmpl
  F["p-d-29-qaN-fK (bug)<br/>finding-bead.json.j2"]:::tmpl
  FS["fix sanity bead<br/>dev-sanity-bead.json.j2<br/>dev_bead = parent = the finding"]:::tmpl
  FQ["fix QA bead, round = N+1<br/>qa-bead.json.j2, checked_bead = the finding"]:::tmpl
  FF["finding filed by a later round<br/>sprint_bead = metadata.sprint_bead"]:::tmpl

  DEV -->|parent-child| ROOT
  SAN -->|parent-child| ROOT
  SAN -->|blocks| DEV
  SF -->|parent-child| DEV
  QA -->|parent-child| DEV
  F -->|parent-child| DEV
  F -->|discovered-from| QA
  FS -->|parent-child| F
  FQ -->|parent-child| F
  FF -->|parent-child| DEV
  FF -->|discovered-from| FQ
```

**Legend.** Green comes from a package script, blue from a template. Where the
templates differ from the phase-d data:

- A sanity FAIL files findings with `sanity-create-findings` as children of the
  checked bead (`--parent <checked bead>`). They have no edge to the sanity
  bead; the sanity bead id is only in `metadata.sanity_finding.sanity_bead`.
  The sanity bead stays open on FAIL, because closing it would release
  dependent sprints. The lead reopens the checked bead for the fix.
- The fix is the finding bead itself. No separate fix bead exists. The fixer
  closes the finding, then the lead creates its sanity bead (`parent` and
  `dev_bead` = the finding) and its QA bead (a child of the finding, round =
  the filing QA round + 1).
- A fix-verification QA round files no new findings. A regressed finding is
  reopened with `bd reopen`, so one bead carries several rounds.
- Any finding filed later (the "fix-round findings" box) is a child of the
  original sprint bead (`sprint_bead` follows `metadata.sprint_bead` back), not
  of the finding or QA it came from.
- QA is a child of the bead it checks and `blocks` nothing.
- For a fix sanity bead, `dev-sanity-bead.json.j2` declares both
  `parent-child` and `blocks` to the finding. That is the same pair, and bd
  keeps one type per pair, so only `parent-child` is drawn.

**Open decisions**

1. C4: findings are children of an already-closed checked bead. bd allows the
   child to be added, but the parent's close happened first, so
   `parent-child` groups the findings here and does not act as a closure gate.
2. C2: the reopen and append-notes flow versus one checker bead per round.

Q3 (decided): sanity-FAIL findings stay children of the dev bead. bd will not
close a bead while a child is open, so they hold the dev bead open, and in the
target model the dev bead holds its sprint open (04, 4d).

## 3c. Phase-d data: the fix beads

Checked 2026-10-03 against all 14 fix beads in sc-obs phase-d.

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000

  SPR["p-d-29 = sprint bead = dev bead"]:::tmpl
  F1["p-d-29-qa1-f1 .. fN<br/>findings"]:::tmpl
  FIXA["p-d-29-qa1-fixes<br/>one fix bead for several findings"]:::hand
  FIXAS["p-d-29-qa1-fixes-sanity"]:::hand
  FIXAQ["p-d-29-qa1-fixes-qa"]:::hand

  SPR35["p-d-35 = sprint bead = dev bead"]:::tmpl
  F4["p-d-35-qa1-f4 finding"]:::tmpl
  FIXB["p-d-35-qa3-fixes<br/>fix bead under a finding"]:::hand
  FIXBS["p-d-35-qa3-fixes-sanity"]:::hand
  FIXBQ["p-d-35-qa3-fixes-qa"]:::hand

  F1 -->|parent-child| SPR
  FIXA -->|parent-child| SPR
  FIXAS -->|parent-child| FIXA
  FIXAQ -->|parent-child| FIXA
  F4 -->|parent-child| SPR35
  FIXB -->|parent-child| F4
  FIXBS -->|parent-child| FIXB
  FIXBQ -->|parent-child| FIXB
```

**Legend.** Three facts from the phase-d data:

1. A fix bead's parent is either the sprint bead (`p-d-29-qa1-fixes`,
   `p-d-30-qa2-fixes`, `p-d-31-qa3-fixes`) or a finding (`p-d-35-qa3-fixes`
   under `p-d-35-qa1-f4`, `p-d-31-qa5-fixes` under `p-d-31-qa1-f4`,
   `p-d-35-qa1-fixes-code` under `p-d-35-qa1-f3`).
2. The fix's sanity and QA beads are `parent-child` children of the fix
   (`<fix>-sanity`, `<fix>-qa`), not siblings under the sprint.
3. One fix bead usually covers several findings (`qaN-fixes`), and no finding
   has an edge to its fix bead (0 of 14). Which findings a fix covers is not
   recorded in the graph.

So the to-be flat model (04), one finding and one fix with `fix ← sanity ←
qa` as siblings under the sprint, is new structure relative to phase-d.
Migrating the phase-d data is post-phase-d work (C8).
