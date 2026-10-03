# 2. Phase level, to-be

This is Rand's target model at phase level. The sprint bead is a container.
The plan import creates it from a template, as today. At plan completion,
sc-compose pours the sprint formula onto it (a mock script stands in until
the sc-compose attach operation exists), and the post-pour script adds the
edges a formula cannot express (07). The script runs after planning and before
plan review (N8, decided). The container cannot close while any
child is open, and blocking findings become children of the sprint (04). The
team lead closes the sprint once all of its blocking findings are closed (Q4,
decided). Important and minor findings live at the phase level and never
block a sprint (Q2, decided; 2b).

The classes below still say `task` or `epic`, because the type is an open
decision (T1, C7).

## 2a. Root, sprint containers, cross-sprint edges ("normal" and "tight")

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000

  ROOT["p-phase-d (phase root)<br/>epic or feature<br/>model: RootBead (proposed)<br/>metadata: plan_scope, phase, integration_branch"]:::tmpl
  PQA["p-phase-d-plan-qa<br/>plan review checker, one bead per round (C2)<br/>model: QaBead (proposed)"]:::hand

  SA["p-d-28 sprint container<br/>model: SprintBead (N3)<br/>template: sprint-bead.json.j2<br/>closed by the team lead (Q4)"]:::tmpl
  subgraph POURA["poured by sc-compose (mock): sprint formula onto p-d-28"]
    DA["p-d-28 dev"]:::poured
    NA["p-d-28 sanity (initial)"]:::poured
    QA_A["p-d-28 qa"]:::poured
  end

  SB["p-d-29 sprint container<br/>normal dependency on p-d-28"]:::tmpl
  subgraph POURB["poured by sc-compose (mock): sprint formula onto p-d-29"]
    DB["p-d-29 dev"]:::poured
    NB["p-d-29 sanity (initial)"]:::poured
    QB["p-d-29 qa"]:::poured
  end

  SC["p-d-30 sprint container<br/>tight dependency on p-d-28"]:::tmpl

  SA -->|parent-child| ROOT
  SB -->|parent-child| ROOT
  SC -->|parent-child| ROOT
  PQA -->|parent-child| ROOT
  SA -->|blocks| PQA
  DA ==>|parent-child| SA
  NA ==>|parent-child| SA
  QA_A ==>|parent-child| SA
  DB ==>|parent-child| SB
  NB ==>|parent-child| SB
  QB ==>|parent-child| SB
  NA ==>|"E1: blocks (poured) or validates (post-pour)"| DA
  QA_A ==>|blocks| NA
  NB ==>|"E1: blocks (poured) or validates (post-pour)"| DB
  QB ==>|blocks| NB

  SB -.->|"blocks (normal)"| NA
  SC -.->|"blocks (tight)"| SA
```

**Legend.** Purple dashed nodes and thick arrows are poured by sc-compose
(mock for now). Dotted arrows are added by the post-pour script: here the
cross-sprint `blocks` edges, read from `sprints.jsonl`. Blue nodes come from a
template plus `bd import`, orange from a hand `bd create`, and solid arrows
from either.

- **normal**: the dependent sprint container `blocks` on the predecessor's
  initial sanity bead, so it starts as soon as the predecessor's code passes
  its first sanity check.
- **tight**: the dependent sprint container `blocks` on the predecessor's
  sprint container, so it waits until the team lead closes it, which happens
  once every blocking finding is closed (Q4).

Verified on bd 1.3.0: a `blocks` edge on a container hides all of its
children from `bd ready`. So both cross-sprint edges can sit on the dependent
container, not on its dev child. The intra-sprint edges are drawn in detail in
04.

**Open decisions**

1. N2: today `sprints.jsonl` names the sanity bead id at plan time
   (`[sprint, sanity_bead_id, deps]`). The "normal" edge needs that id to
   exist when the post-pour script runs, so the formula's sanity id has to be
   deterministic and known in advance. Options: the formula takes the id as
   an input, or the tuple names the sprint and the id is derived.
2. N6: `sprints.jsonl` has no way to say "tight". Options: add a fourth tuple
   field (for example `{"tight": ["d-28"]}`), or name the predecessor's sprint
   id instead of its sanity id.
3. T1 and C7: the container type. `epic` is listed by `bd ready` once it is
   unblocked, as the phase root is today. A custom type would keep dispatch
   from treating it as work.
4. E1: the sanity-to-dev edge type (05).

## 2b. Phase-wide beads, non-blocking findings, and the files that point in

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000
  classDef file fill:#f1f3f4,stroke:#5f6368,stroke-dasharray:4 3,color:#000

  ROOT["p-phase-d (phase root)<br/>metadata.integration_branch"]:::tmpl
  SPR["p-d-29 sprint container"]:::tmpl
  QA["p-d-29 qa (closed)"]:::tmpl
  FEAT["phase-d non-blocking findings<br/>feature bead under the phase (Q2)"]:::hand
  IMP["important or minor finding<br/>model: FindingBead (proposed), metadata.severity<br/>priority from severity: important 2, minor 4<br/>picked up by idle dev agents by priority"]:::tmpl
  REV["p-phase-d-review r1, r2, ...<br/>phase-end review checker, one bead per round (C2)<br/>model: QaBead (proposed)"]:::hand
  RF["phase-end finding<br/>model: FindingBead (proposed)"]:::tmpl
  REL["phase release bead<br/>type: C7"]:::hand
  WFR["p-workflow-issues<br/>workflow-issues root, outside the phase"]:::hand
  WF["workflow-issue class bead<br/>type: C7"]:::tmpl
  TOML[/".atm-bd/current-phase.toml (untracked, per checkout)<br/>root, sprints (relative path), integration_branch"/]:::file
  SJ[/"plans/phase-d/sprints.jsonl<br/>on origin/integration_branch"/]:::file

  SPR -->|parent-child| ROOT
  QA -->|parent-child| SPR
  FEAT -->|parent-child| ROOT
  IMP -->|parent-child| FEAT
  IMP -->|discovered-from| QA
  REV -->|parent-child| ROOT
  RF -->|parent-child| ROOT
  RF -->|discovered-from| REV
  REL -->|parent-child| ROOT
  REL -->|blocks| REV
  WF -->|parent-child| WFR

  TOML -. "root =" .-> ROOT
  TOML -. "sprints =" .-> SJ
  TOML -. "integration_branch must equal (C5)" .-> ROOT
  ROOT -. "integration_branch locates" .-> SJ
```

**Legend.** Q2 (decided): important and minor findings are filed against the
phase, normally under a feature bead, not under the sprint. They are never
children of a sprint container, so they never hold one open. QA files them
from `finding-bead.json.j2` with `parent` = the feature bead and
`discovered-from` = the QA bead that found them. Both edges are created by
the template import, not by a formula. Phase-wide checkers and the release
bead are made by hand or from templates. `current-phase.toml` is the
per-checkout pointer to the root (06). The `REL blocks REV` edge (release
waits for the phase-end review) is drawn as a candidate, not as today's
behavior.

**Open decisions**

1. C5: either `current-phase.toml` is the authority for the integration
   branch, or root `metadata.integration_branch` is authoritative and the toml
   is validated against it.
2. C7: the types of the release bead, of workflow-issue class beads, and of
   the non-blocking-findings feature bead.
3. Should the release bead be modeled as a phase child that `blocks` on the
   phase-end review, or left outside the phase graph?
