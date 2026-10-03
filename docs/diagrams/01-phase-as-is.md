# 1. Phase level, as-is

Source: sc-observability phase-d beads (`p` = `obs`), plus the package as it is
at `main` 775a073 (`atm-beads` `plan-root.json.j2`, `sprint-bead.json.j2`,
`dev-sanity-bead.json.j2`; `atm-bd-orchestration` "Plan Gate", "Phase-End
Review" and `workflow-issue-bead.json.j2`). No formula pours anything today:
every bead below comes from a template plus `bd import`, or from a hand
`bd create`.

## 1a. Root, sprints, plan review, phase-end review

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000
  classDef file fill:#f1f3f4,stroke:#5f6368,stroke-dasharray:4 3,color:#000

  EPIC["p-c4v<br/>epic (parent of the phase)"]:::hand
  ROOT["p-phase-d (phase root)<br/>issue_type feature (epic or feature)<br/>labels: phase-d, scope:feature<br/>metadata: plan_scope, phase, integration_branch<br/>template: plan-root.json.j2"]:::tmpl

  PQA["p-phase-d-plan-qa, p-phase-d-plan-qa-2 .. -8<br/>task, label stage:plan-review<br/>verdict only in close_reason<br/>hand bd create"]:::hand
  PFIX["p-phase-d-plan-fix-*<br/>task, label stage:plan-fix<br/>hand bd create"]:::hand

  D28["p-d-28 = sprint bead = dev bead<br/>task, labels stage:dev + stage:sprint<br/>model: SprintBead<br/>template: sprint-bead.json.j2"]:::tmpl
  S28["p-d-28-sanity<br/>task, label stage:dev-sanity<br/>model: SanityBead (metadata.dev_bead = p-d-28)<br/>template: dev-sanity-bead.json.j2"]:::tmpl
  D29["p-d-29 = sprint bead = dev bead<br/>task, stage:dev + stage:sprint"]:::tmpl
  S29["p-d-29-sanity<br/>task, stage:dev-sanity"]:::tmpl

  REV["p-phase-d-review<br/>task, label stage:review<br/>verdict only in close_reason<br/>hand bd create"]:::hand
  RF["p-phase-d-review-r1 .. r3<br/>bug, stage:finding, severity:*<br/>template: finding-bead.json.j2"]:::tmpl

  SJ[/"plans/phase-d/sprints.jsonl<br/>one tuple per sprint:<br/>[sprint, sanity_bead_id, [prerequisite sprints]]<br/>committed on origin/integrate/phase-d"/]:::file

  ROOT -->|parent-child| EPIC
  PQA -->|parent-child| ROOT
  PFIX -->|parent-child| ROOT
  D28 -->|parent-child| ROOT
  S28 -->|parent-child| ROOT
  D29 -->|parent-child| ROOT
  S29 -->|parent-child| ROOT
  S28 -->|blocks| D28
  S29 -->|blocks| D29
  D28 -->|blocks| PQA
  D29 -->|blocks| PQA
  D29 -->|blocks| S28
  REV -->|parent-child| ROOT
  RF -->|parent-child| ROOT
  RF -->|discovered-from| REV

  ROOT -. "metadata.integration_branch + repo_config plans_dir<br/>locate (validate-plan --root)" .-> SJ
  SJ -. "names dev id p-sprint and sanity id;<br/>each prerequisite must be a blocks edge" .-> D29
```

**Legend.** Blue nodes come from a template plus `bd import`. Orange nodes come
from a hand `bd create`. The parallelogram is a committed file, and dashed
arrows to and from it are lookups, not bd edges. Today classification is by
`stage:` label, because dev, sanity, QA, plan review and review are all
`issue_type` task. The cross-sprint edge is the next sprint's dev bead
`blocks` on this sprint's sanity bead (`p-d-29 -> p-d-28-sanity`). There is no
`current-phase.toml` today. The root is passed as `--root`, and
`validate-plan` reads `sprints.jsonl` from `origin/<metadata.integration_branch>`.
A phase-end finding is a child of the root when it spans sprints, and of the
cited dev bead otherwise.

**Open decisions**

1. C8: phase-d's label-based classification is either converted by a one-time
   migration script after phase-d ends, with no runtime label parsing, or
   labels stay a runtime input.
2. C1: plan-review and phase-end review verdicts are either parsed from
   `close_reason` as today, or written as required `verdict` and `round`
   metadata.

## 1b. Release bead and workflow-issue class beads

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000

  ROOT["p-phase-d (phase root)"]:::tmpl
  D18["p-d-18 (sprint = dev bead)<br/>task, stage:dev + stage:sprint"]:::tmpl
  REL["p-d-18-release-prep<br/>task, no labels, no template<br/>(phase-d has no single phase release bead)"]:::hand
  WFR["p-workflow-issues<br/>epic, label workflow-issue<br/>no parent, outside every phase"]:::hand
  WF["&lt;task&gt;-wf-&lt;SIGNATURE&gt;<br/>e.g. p-phase-d-flaky-audit-f2-wf-PLAN_INVALID<br/>task, label workflow-issue only<br/>no metadata<br/>template: workflow-issue-bead.json.j2"]:::tmpl

  D18 -->|parent-child| ROOT
  REL -->|parent-child| D18
  WF -->|parent-child| WFR
```

**Legend.** A workflow-issue class bead groups refusals that share a failure
signature. Assignment templates reuse an existing class bead and append
evidence to its notes, so the class bead carries no edge to the refused task.
The release work in phase-d is an unlabeled task under one sprint, with no
template and no fixed place.

**Open decisions**

1. C7: pick a type for workflow-issue class beads (`chore`, a custom type, or
   `task` plus a schema model) and for a phase release bead, so classification
   needs no catch-all for unlabeled beads like `p-d-18-release-prep`.
