# 4. Sprint level, to-be

In Rand's target model the sprint bead is a container. It cannot close until
every blocking finding is fixed, and the team lead closes it once they are all
closed (Q4, decided). Its children are:

- the dev task that is actually assigned;
- the sanity task (the brief's "severity-task" is read as sanity);
- the QA task.

When QA fails, its blocking findings become `parent-child` children of the
sprint bead. bd refuses to close a parent while a child is open (verified on
bd 1.3.0), and that is what holds the sprint open. Every blocking finding gets
its own fix, sanity and QA beads, independent of every other finding (Q1,
decided). Important and minor findings are filed against the phase, not the
sprint (Q2, decided; drawn in 02b). Model names marked "proposed" do not exist
in `bead_schema.py` yet.

Marking (see the README): thick arrows and purple dashed nodes are poured by
sc-compose (mock for now). Dotted arrows are added by the post-pour script.
Solid arrows and nodes are created by hand, by a template or by a script.

## 4a. The sprint group, with the schema model of each node

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000

  ROOT["p-phase-d (phase root)<br/>model: RootBead (proposed)<br/>plan_scope, phase, integration_branch"]:::tmpl
  SPR["p-d-29 sprint container<br/>model: SprintBead (N3)<br/>Deliverables, acceptance_criteria,<br/>requirements, adrs, worktree, branch, pr_target, difficulty<br/>type: T1<br/>closed by the team lead (Q4)"]:::tmpl

  subgraph POUR["poured by sc-compose (mock): sprint formula onto p-d-29"]
    DEV["dev: the assigned dev task<br/>model: SprintBead or DevBead (proposed) (N3)<br/>assignee: dev member"]:::poured
    SAN["sanity: gate, run sanity on p-d-29<br/>SanityBead (dev_bead, as today)"]:::poured
    QA["qa round 1<br/>model: QaBead (proposed)<br/>checked_bead, commit, round, branch, layer<br/>+ C1: verdict"]:::poured
  end

  SPR -->|parent-child| ROOT
  DEV ==>|parent-child| SPR
  SAN ==>|parent-child| SPR
  QA ==>|parent-child| SPR
  SAN ==>|"E1: blocks (poured) or validates (post-pour)"| DEV
  QA ==>|blocks| SAN
  QA -.->|"validates (C3)"| DEV
```

**Legend.** `QA blocks sanity` puts QA after sanity. QA-to-dev and
QA-to-sanity are different pairs, so the post-pour script can also give QA a
`validates` edge to the bead it checks. Inside one pair, sanity to dev can
carry only one type (E1, drawn in 05). Under options A and C the formula pours
it as `blocks`. Under option B the formula pours only the sanity bead, and the
post-pour script adds its `validates` edge. The existing `SanityBead` validator
requires a `blocks` edge to `metadata.dev_bead`, so option B would need that
model changed, and option C keeps it unchanged.

**Open decisions**

1. E1: the type of the sanity-to-dev edge: A, B or C (05).
2. N3: does `SprintBead` validate the container or the dev child?
3. C1: are verdict and round required metadata on QA when it closes, or
   derived from status and graph? (Sanity is a simple gate and gets no new
   fields: N9, decided.)
4. C3: does QA validate the dev bead, at the same PR head sanity checked, or
   the sanity bead? Is "sanity before QA" its own `blocks` edge, as drawn?
5. T1: classify dev, sanity and QA by `issue_type` (custom types) or by schema
   metadata, with no `stage:` labels.

## 4b. QA FAIL: one independent fix group per blocking finding (Q1, decided)

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef closed fill:#e0e0e0,stroke:#757575,color:#000

  SPR["p-d-29 sprint container<br/>cannot close while a child is open"]:::tmpl
  QA["p-d-29 qa round 1<br/>closed, verdict FAIL"]:::closed
  F3["p-d-29-qa1-f3 blocking finding<br/>model: FindingBead (proposed)<br/>severity, sprint_bead, found_at_commit,<br/>reviewer, finding_ref, requirements, adrs, screen"]:::tmpl
  F7["p-d-29-qa1-f7 blocking finding"]:::tmpl

  subgraph POUR3["poured by sc-compose (mock): finding formula onto f3"]
    FX3["f3 fix r1<br/>model: DevBead or FixBead (proposed)"]:::poured
    FS3["f3 fix sanity r1: gate"]:::poured
    FQ3["f3 fix qa r1<br/>model: QaBead, checked_bead = fix (C3)"]:::poured
  end
  subgraph POUR7["poured by sc-compose (mock): finding formula onto f7"]
    FX7["f7 fix r1"]:::poured
    FS7["f7 fix sanity r1"]:::poured
    FQ7["f7 fix qa r1"]:::poured
  end

  QA -->|parent-child| SPR
  F3 -->|parent-child| SPR
  F7 -->|parent-child| SPR
  F3 -->|discovered-from| QA
  F7 -->|discovered-from| QA
  FX3 ==>|parent-child| F3
  FS3 ==>|parent-child| F3
  FQ3 ==>|parent-child| F3
  FS3 ==>|"E1"| FX3
  FQ3 ==>|blocks| FS3
  FQ3 -.->|"validates (C3)"| FX3
  FX7 ==>|parent-child| F7
  FS7 ==>|parent-child| F7
  FQ7 ==>|parent-child| F7
  FS7 ==>|"E1"| FX7
  FQ7 ==>|blocks| FS7
  FQ7 -.->|"validates (C3)"| FX7
```

**Legend.** Grey nodes are closed. QA files each blocking finding from
`finding-bead.json.j2`, and that import creates the finding's `parent-child`
edge to the sprint and its `discovered-from` edge to QA (solid). Each finding
then gets its own poured group, which shares no edge with any other
finding's group: one finding, one fix, as in the old triage/TTL model. The
group attaches under the finding (Q1, confirmed). quality-mgr closes the
finding after the filing reviewer verifies the fix (N10, decided). bd keeps the
finding open until its fix, sanity and QA close, and the finding keeps the
sprint open. If two findings must be fixed in order, the existing
inter-finding `blocks` edge (`blocked_by` in `finding-bead.json.j2`) sits
between the findings, not between their groups.

**Open decisions**

1. C4: severity becomes required `FindingBead` metadata. Under this model,
   `parent-child` to the sprint is a closure gate, not only grouping, because
   the sprint is still open when the finding is filed.
2. C3: does the fix QA check the fix bead or the finding?
3. E1: the fix-sanity-to-fix edge type, the same choice as in 4a.

## 4c. A second fix round: a new group, never a reopen

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef closed fill:#e0e0e0,stroke:#757575,color:#000

  SPR["p-d-29 sprint container"]:::tmpl
  F["p-d-29-qa1-f3 blocking finding<br/>stays open across rounds"]:::tmpl

  subgraph R1["poured by sc-compose (mock): finding formula, round 1"]
    FX1["fix r1<br/>closed"]:::closed
    FS1["fix sanity r1: gate<br/>closed"]:::closed
    FQ1["fix qa r1<br/>closed, verdict FAIL, round 1"]:::closed
  end
  subgraph R2["poured by sc-compose (mock): finding formula, round 2"]
    FX2["fix r2"]:::poured
    FS2["fix sanity r2"]:::poured
    FQ2["fix qa r2<br/>round 2"]:::poured
  end

  F -->|parent-child| SPR
  FX1 ==>|parent-child| F
  FS1 ==>|parent-child| F
  FQ1 ==>|parent-child| F
  FS1 ==>|"E1"| FX1
  FQ1 ==>|blocks| FS1
  FX2 ==>|parent-child| F
  FS2 ==>|parent-child| F
  FQ2 ==>|parent-child| F
  FS2 ==>|"E1"| FX2
  FQ2 ==>|blocks| FS2
```

**Legend.** When a fix QA round passes, quality-mgr closes the finding after
the filing reviewer verifies the fix (N10, decided). When fix QA round 1
closes with FAIL, the finding stays open, and
sc-compose pours the finding formula again with `round = 2`. No round-1 bead
is reopened, so its verdict and evidence stay intact. The next round number is
the highest existing round under the finding, plus 1. Today the template
instead reopens the finding with `bd reopen` (03). A fix-round QA files no new
findings, as today.

**Open decisions**

1. C2: one checker bead per round, never reopened (as drawn), versus the
   current reopen flow.
2. C1: with C2, a round's outcome is read from that round's QA `verdict`, not
   from the finding's status.
3. N2: how round-2 ids are made unique (a round suffix input to the formula).

## 4d. Sanity FAIL: the closure chain (Q3, decided)

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef script fill:#e6f4ea,stroke:#188038,color:#000

  SPR["p-d-29 sprint container<br/>cannot close: dev is open"]:::tmpl
  DEV["p-d-29 dev<br/>reopened by the lead after sanity FAIL<br/>cannot close: sanity findings are open"]:::poured
  SAN["p-d-29 sanity: gate<br/>stays open on FAIL, as today"]:::poured
  SF1["p-d-29.deliverable-2 NOT complete<br/>sanity-create-findings"]:::script
  SF2["p-d-29.deliverable-5 NOT complete"]:::script

  DEV ==>|parent-child| SPR
  SAN ==>|parent-child| SPR
  SAN ==>|"E1"| DEV
  SF1 -->|parent-child| DEV
  SF2 -->|parent-child| DEV
  SF2 -->|blocks| SF1
```

**Legend.** `sanity-create-findings` (green, a package script) files one
finding per undone deliverable as a child of the checked bead, and adds
`blocks` only between those findings when one depends on another. bd will not
close a bead while any child is open. So the sanity findings hold the dev bead
open, the dev bead holds the sprint container open, and the team lead cannot
close the sprint (Q4) until the dev bead closes. The dev fixes each finding in
place on the reopened dev bead, as today (`dev-fix.xml.j2`). Sanity findings
get no poured fix group.

N9 (decided): sanity is a simple gate. A sanity bead only signals that the
sanity agent must run on its parent sprint. Its result reads like
"p-d-29.deliverable-2 NOT complete". Ideally it becomes JEV-only once JEV is
qualified, and JEV's output then holds all the data. It gets no
`discovered-from` edge and no fields beyond what `SanityBead` has today. The
dev-sanity role points at a team member with no agent file, today
`atm-sanity`. dev-sanity may later collapse into one agent file, since
dev-sanity-llm and dev-sanity-jev are merged.
