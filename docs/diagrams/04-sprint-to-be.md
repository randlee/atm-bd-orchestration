# 4. Sprint level, to-be

In Rand's target model the sprint bead is a container. It cannot close until
every blocking finding is fixed. Its children are:

- the dev task that is actually assigned;
- the sanity task (the brief's "severity-task" is read as sanity);
- the QA task.

When QA fails, its blocking findings become `parent-child` children of the
sprint bead. bd refuses to close a parent while a child is open (verified on
bd 1.3.0), and that is what holds the sprint open. Each blocking finding gets
its own fix, sanity and QA group. Model names marked "proposed" do not exist
in `bead_schema.py` yet.

## 4a. The sprint group, with the schema model of each node

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000

  ROOT["p-phase-d (phase root)<br/>model: RootBead (proposed)<br/>plan_scope, phase, integration_branch"]:::tmpl
  SPR["p-d-29 sprint container<br/>model: SprintBead (N3)<br/>Deliverables, acceptance_criteria,<br/>requirements, adrs, worktree, branch, pr_target, difficulty<br/>type: T1"]:::tmpl

  subgraph POUR["poured by sprint formula (N1) onto p-d-29"]
    DEV["dev: the assigned dev task<br/>model: SprintBead or DevBead (proposed) (N3)<br/>assignee: dev member"]:::poured
    SAN["sanity (initial)<br/>model: SanityBead<br/>metadata.dev_bead = dev<br/>+ C1: verdict, round"]:::poured
    QA["qa round 1<br/>model: QaBead (proposed)<br/>checked_bead, commit, round, branch, layer<br/>+ C1: verdict"]:::poured
  end

  SPR -->|parent-child| ROOT
  DEV ==>|parent-child| SPR
  SAN ==>|parent-child| SPR
  QA ==>|parent-child| SPR
  SAN ==>|"E1: blocks or validates"| DEV
  QA ==>|blocks| SAN
  QA -.->|"validates (C3)"| DEV
```

**Legend.** The purple dashed nodes and the thick arrows are poured by the
sprint formula. The plan import creates the sprint container from a template.
`QA blocks sanity` puts QA after sanity. The QA-to-dev pair and the QA-to-sanity
pair are different pairs, so QA can also carry `validates` to the bead it
checks (dotted, because a formula step cannot pour a `validates` edge, N4).
Inside one pair, sanity to dev can carry only one type (E1, drawn in 05).
The existing `SanityBead` validator requires a `blocks` edge to
`metadata.dev_bead`. E1 option B (only `validates`) would therefore need that
model changed, and option C keeps it unchanged.

**Open decisions**

1. E1: the type of the sanity-to-dev edge: A, B or C (05).
2. N3: does `SprintBead` validate the container or the dev child?
3. C1: are verdict and round required metadata on sanity and QA when they
   close, or derived from status and graph?
4. C3: does QA validate the dev bead, at the same PR head sanity checked, or
   the sanity bead? Is "sanity before QA" its own `blocks` edge, as drawn?
5. T1: classify dev, sanity and QA by `issue_type` (custom types) or by schema
   metadata, with no `stage:` labels.
6. Q4: who closes the sprint container, and when? bd does not close a parent
   automatically.

## 4b. QA FAIL: blocking findings under the sprint, and a group per finding

Q1 is open: does each finding's fix, sanity and QA group sit under the finding
or under the sprint? Both layouts are shown.

**Q1 option (a): the group under the finding**

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef closed fill:#e0e0e0,stroke:#757575,color:#000

  SPR["p-d-29 sprint container<br/>cannot close while a child is open"]:::tmpl
  QA["p-d-29 qa round 1<br/>closed, verdict FAIL"]:::closed
  F["p-d-29-qa1-f3 blocking finding<br/>model: FindingBead (proposed)<br/>severity, sprint_bead, found_at_commit,<br/>reviewer, finding_ref, requirements, adrs, screen"]:::tmpl

  subgraph POURF["poured by finding formula (N1) onto p-d-29-qa1-f3"]
    FX["fix round 1<br/>model: DevBead or FixBead (proposed)"]:::poured
    FS["fix sanity round 1<br/>model: SanityBead, dev_bead = fix"]:::poured
    FQ["fix qa round 1<br/>model: QaBead, checked_bead = fix (C3)"]:::poured
  end

  QA -->|parent-child| SPR
  F -->|parent-child| SPR
  F -.->|discovered-from| QA
  FX ==>|parent-child| F
  FS ==>|parent-child| F
  FQ ==>|parent-child| F
  FS ==>|"E1: blocks or validates"| FX
  FQ ==>|blocks| FS
```

**Q1 option (b): the group under the sprint**

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef closed fill:#e0e0e0,stroke:#757575,color:#000

  SPR["p-d-29 sprint container"]:::tmpl
  QA["p-d-29 qa round 1<br/>closed, verdict FAIL"]:::closed
  F["p-d-29-qa1-f3 blocking finding<br/>model: FindingBead (proposed)"]:::tmpl

  subgraph POURF["poured by finding formula (N1) onto p-d-29"]
    FX["fix round 1"]:::poured
    FS["fix sanity round 1"]:::poured
    FQ["fix qa round 1"]:::poured
  end

  QA -->|parent-child| SPR
  F -->|parent-child| SPR
  F -.->|discovered-from| QA
  FX ==>|parent-child| SPR
  FS ==>|parent-child| SPR
  FQ ==>|parent-child| SPR
  FS ==>|"E1: blocks or validates"| FX
  FQ ==>|blocks| FS
  F -.->|blocks| FQ
```

**Legend.** Grey nodes are closed. The finding is filed by QA from
`finding-bead.json.j2`, and its `discovered-from` edge to QA is added outside
the formula (dotted). In (a), the finding is itself a container. bd will not
close it until its group is closed, and the sprint cannot close until the
finding closes. In (b), the finding needs an explicit edge to its group. The
drawing uses `finding blocks fix-qa`, so the finding becomes ready to close
only after its fix QA closes. Without that edge, nothing ties the finding to
its group except metadata.

**Open decisions**

1. Q1: the group under the finding (a) or under the sprint (b)?
2. Q2: do `important` findings count as blocking here? Policy treats
   important as a FAIL. Important and minor findings must not be children of
   the sprint, or they hold it open. Where do they live: under the QA bead,
   under the root, or under a non-gating holder bead?
3. Q3: sanity-FAIL findings are children of the dev bead today (03). Do they
   also go under the sprint container and get a group of their own?
4. C4: severity becomes required `FindingBead` metadata. Under this model,
   `parent-child` to the sprint is a closure gate, not only grouping, because
   the sprint is still open when the finding is filed.
5. C3: does the fix QA check the fix bead or the finding?

## 4c. A second fix round: a new group, never a reopen

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef closed fill:#e0e0e0,stroke:#757575,color:#000

  SPR["p-d-29 sprint container"]:::tmpl
  F["p-d-29-qa1-f3 blocking finding<br/>stays open across rounds"]:::tmpl

  subgraph R1["poured by finding formula, round 1"]
    FX1["fix r1<br/>closed"]:::closed
    FS1["fix sanity r1<br/>closed, verdict PASS"]:::closed
    FQ1["fix qa r1<br/>closed, verdict FAIL, round 1"]:::closed
  end
  subgraph R2["poured by finding formula, round 2"]
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

**Legend.** Drawn with Q1 option (a). When fix QA round 1 closes with FAIL,
the finding stays open, and the finding formula is poured again with
`round = 2`. No round-1 bead is reopened, so its verdict and evidence stay
intact. The next round number is the highest existing round under the
finding, plus 1. Today the template instead reopens the finding with
`bd reopen` (03). A fix-round QA files no new findings, as today.

**Open decisions**

1. C2: one checker bead per round, never reopened (as drawn), versus the
   current reopen flow.
2. C1: with C2, a round's outcome is read from that round's QA `verdict`, not
   from the finding's status.
3. N2: how round-2 ids are made unique (a round suffix input to the formula).
