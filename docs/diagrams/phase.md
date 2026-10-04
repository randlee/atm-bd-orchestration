# Phase level

The plan import creates the phase root and the sprint containers from
templates. `scripts/bead-groups` then pours each sprint's group and adds the
post-pour edges (formula.md); it runs after planning and before plan review.
When QA fails, quality-mgr pours one fix group per blocking finding under the
sprint before it closes qa. Important and minor findings sit at phase level.

## Root, sprint containers, normal and tight

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000

  ROOT["p-phase-x (phase root)<br/>metadata: plan_scope, phase, integration_branch"]:::tmpl
  PQA["p-phase-x-plan-qa<br/>plan review"]:::tmpl

  SA["p-x-1 sprint container<br/>closed by the team lead"]:::tmpl
  subgraph POURA["poured: sprint-group onto p-x-1"]
    DA["p-x-1.group-dev"]:::poured
    NA["p-x-1.group-sanity (initial)"]:::poured
    QA_A["p-x-1.group-qa"]:::poured
  end
  subgraph POURF["poured by quality-mgr: finding-group onto p-x-1, one blocking finding"]
    FXA["p-x-1.qa1-f3-r1-fix"]:::poured
    FSA["p-x-1.qa1-f3-r1-sanity"]:::poured
    FQA["p-x-1.qa1-f3-r1-qa"]:::poured
  end

  SB["p-x-2 sprint container<br/>normal dependency on p-x-1"]:::tmpl
  SC["p-x-3 sprint container<br/>tight dependency on p-x-1"]:::tmpl

  SA -->|parent-child| ROOT
  SB -->|parent-child| ROOT
  SC -->|parent-child| ROOT
  PQA -->|parent-child| ROOT
  SA -->|blocks| PQA
  DA ==>|parent-child| SA
  NA ==>|parent-child| SA
  QA_A ==>|parent-child| SA
  NA ==>|blocks| DA
  QA_A ==>|blocks| NA
  FXA ==>|parent-child| SA
  FSA ==>|parent-child| SA
  FQA ==>|parent-child| SA
  FSA ==>|blocks| FXA
  FQA ==>|blocks| FSA

  SB -.->|"blocks (normal)"| NA
  SC -.->|"blocks (tight)"| SA
```

- **normal**: the dependent container `blocks` on the predecessor's initial
  sanity bead, so it starts once the predecessor's code passes its first
  sanity check. Fix groups do not affect it.
- **tight**: the dependent container `blocks` on the predecessor's sprint
  container, so it waits until the team lead closes it, after every blocking
  fix group is closed.

A `blocks` edge on a container hides all its children from `bd ready`, so both
cross-sprint edges sit on the dependent container. `bead-groups` reads the
predecessors from the phase's `sprints.jsonl` and the choice from the
container's `metadata.coupling` (default `normal`).

## Phase-wide beads and non-blocking findings

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef file fill:#f1f3f4,stroke:#5f6368,stroke-dasharray:4 3,color:#000

  ROOT["p-phase-x (phase root)<br/>metadata.integration_branch"]:::tmpl
  SPR["p-x-2 sprint container"]:::tmpl
  QA["p-x-2.group-qa (closed)"]:::tmpl
  FEAT["feature bead for the phase's non-blocking findings"]:::tmpl
  IMP["important or minor finding<br/>metadata.severity, priority from severity<br/>picked up by an idle dev by priority"]:::tmpl
  REV["p-phase-x-review<br/>phase-end review"]:::tmpl
  RF["phase-end finding"]:::tmpl
  WFR["p-workflow-issues<br/>outside the phase"]:::tmpl
  WF["workflow-issue class bead"]:::tmpl
  TOML[/".atm-bd/current-phase.toml (untracked)<br/>root, sprints, integration_branch"/]:::file
  SJ[/"sprints.jsonl<br/>on the integration branch"/]:::file

  SPR -->|parent-child| ROOT
  QA ==>|parent-child| SPR
  FEAT -->|parent-child| ROOT
  IMP -->|parent-child| FEAT
  IMP -->|discovered-from| QA
  REV -->|parent-child| ROOT
  RF -->|parent-child| ROOT
  RF -->|discovered-from| REV
  WF -->|parent-child| WFR

  TOML -. "root" .-> ROOT
  TOML -. "sprints" .-> SJ
```

quality-mgr creates important and minor finding beads from
`finding-bead.json.j2` before it closes the qa bead that found them. They are
never children of a sprint, so they never hold one open.
