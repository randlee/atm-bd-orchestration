# 5. Lifecycle (sprint level)

## 5a. Ready, claim and close order

```mermaid
sequenceDiagram
  autonumber
  participant L as lead
  participant B as bd
  participant A as ATM
  participant D as dev member
  participant S as dev-sanity role (member atm-sanity)
  participant Q as quality-mgr
  participant G as logs in .sc

  Note over L,B: planning: sprint containers from sprint-bead.json.j2 and bd import
  L->>B: post-pour script over the phase's sprint beads (N8): sc-compose (mock) pours<br/>each missing dev, sanity, qa group, then the script adds the missing edges (07)
  Note over L,Q: plan review (plan-review bead), after the post-pour script. Re-running it<br/>after sprints are added creates only what is missing.
  L->>B: bd ready
  B-->>L: dev (sanity and qa are gated: E1, qa blocks sanity)
  L->>A: atm task assign D --task-id dev-bead-id
  D->>B: claim dev (in_progress)
  D->>A: atm task start dev-bead-id
  D->>B: bd close dev
  D->>A: atm task close same-id completed
  L->>B: bd ready
  B-->>L: sanity
  L->>A: atm task assign S --task-id sanity-bead-id
  S->>B: claim sanity
  S->>G: append .sc/sanity-log/phase-p.jsonl (sanity-run-history)
  alt PASS
    S->>B: bd close sanity: PASS (simple gate, N9)
  else FAIL
    S->>B: sanity-create-findings: "p-d-29.deliverable-2 NOT complete", children of dev (Q3)<br/>sanity stays open, as today
    L->>B: reopen dev, assign dev-fix. Dev cannot close until its sanity findings close (Q3)
  end
  S->>A: atm task close same-id
  L->>B: bd ready
  B-->>L: qa
  L->>A: atm task assign Q --task-id qa-bead-id
  Q->>B: claim qa
  Q->>B: blocking findings: FindingBead, parent-child sprint, discovered-from qa
  Q->>B: important and minor findings: parent-child phase feature bead, discovered-from qa (Q2)
  Q->>G: append .sc/qa-log/phase-p.jsonl and phase-p-stats.jsonl
  Q->>B: bd close qa, verdict + round (C1, today metadata.round + close_reason "FAIL: n findings filed")
  Q->>A: atm task close same-id completed
  loop each open blocking finding, independently (Q1)
    L->>B: sc-compose pour (mock) finding formula, round n, then its post-pour edges (N11, 07)
    Note over L,Q: fix, fix sanity, fix qa run in the same order as dev, sanity, qa<br/>and append the same logs. Fix qa FAIL means pour round n+1, never reopen (C2).
    Q->>B: filing reviewer verifies the fix, then quality-mgr closes the finding (N10)
  end
  L->>B: team lead closes the sprint container once all its blocking findings are closed (Q4)
  Note over L,D: important and minor findings stay under the phase feature bead.<br/>Idle dev agents pick them up by priority. They never hold a sprint open (Q2).
```

**Legend.** Each `atm task` id equals the bead id (06). Where each fact is
written:

| Fact | Bead | Field today | Field to-be |
| --- | --- | --- | --- |
| sanity result | sanity bead (a simple gate) | `close_reason` "PASS at sha"; FAIL leaves child findings "deliverable-N NOT complete" | unchanged; ideally JEV-only later, with JEV output holding the data (N9) |
| QA verdict | QA bead | `close_reason` "PASS/FAIL: n findings filed" | `metadata.verdict` (C1) |
| round | QA bead | `metadata.round` | `metadata.round` on every checker (C1, C2) |
| severity | finding bead | `metadata.severity` + `severity:` label | `metadata.severity`, required (C4) |

The logs are an OTel contract, and their formats do not change. QA appends
`.sc/qa-log/phase-<p>.jsonl` and `.sc/qa-log/phase-<p>-stats.jsonl` when it
closes (`qa-template.xml.j2`). The sanity member appends the sanity ledger
`.sc/sanity-log/phase-<p>.jsonl` through `sanity-run-history` when the sanity
check closes.

**Open decisions**

1. C1: verdict and round as required metadata written when the checker
   closes (or the ATM close status), or derived from status and graph.
2. C2: one QA bead per round, never reopened.
3. N11: who runs the finding-group pour and its edges: the post-pour script
   or the lead by hand.

Decided (Rand): Q1, one independent group per blocking finding; Q2,
important and minor findings sit under a phase feature bead; Q3, sanity
findings hold the dev bead open and so hold the sprint open; Q4, the team
lead closes the sprint once all of its blocking findings are closed; N8, the
post-pour script runs after planning and before plan review; N9, sanity is a
simple gate that keeps the bead open on FAIL, as today; N10, quality-mgr
closes a blocking finding after the filing reviewer verifies the fix.

The dev-sanity role points at a team member with no agent file, today
`atm-sanity`. dev-sanity may later collapse into one agent file, since
dev-sanity-llm and dev-sanity-jev are merged.

## 5b. E1: the edge-per-pair options for dev and sanity inside the sprint

bd 1.3.0 keeps one dependency type per pair, and `validates` does not gate
`bd ready`. So "sanity validates dev" and "sanity is blocked by dev" cannot
both sit on the same pair. Both children's `parent-child` edges go to the
sprint, which is a different pair, so they do not conflict.

**Option A: create the sanity bead when dev closes**

```mermaid
flowchart LR
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef late fill:#fce8e6,stroke:#c5221f,stroke-dasharray:2 2,color:#000
  SPR["sprint container"]:::tmpl
  DEV["dev (poured at plan time)"]:::poured
  SAN["sanity (created at dev close)"]:::late
  NEXT["next sprint container"]:::tmpl
  DEV ==>|parent-child| SPR
  SAN -->|parent-child| SPR
  SAN -->|validates| DEV
  NEXT -.->|"blocks (normal): target missing at import"| SAN
```

Trade-off: this breaks the plan graph. The next sprint's dev beads have a
`blocks` edge on this sanity bead when the plan is imported, and the bead does
not exist yet.

**Option B: the plan-time sanity bead carries only `validates`**

```mermaid
flowchart LR
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef file fill:#f1f3f4,stroke:#5f6368,stroke-dasharray:4 3,color:#000
  SPR["sprint container"]:::tmpl
  DEV["dev"]:::poured
  SAN["sanity: in bd ready while dev is open"]:::poured
  QS[/"package queue script:<br/>open checker whose validated bead is closed"/]:::file
  DEV ==>|parent-child| SPR
  SAN ==>|parent-child| SPR
  SAN -.->|validates| DEV
  QS -. "replaces bd ready for checkers" .-> SAN
```

Trade-off: the edge correlates sanity to dev explicitly, but plain `bd ready`
stops being the queue. The option is feasible with the post-pour script:
sc-compose pours the sanity bead, and the post-pour script adds its `validates`
edge (dotted). The `SanityBead` model, which requires a `blocks` edge, must
change.

**Option C: keep the existing schema**

```mermaid
flowchart LR
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  SPR["sprint container"]:::tmpl
  DEV["dev"]:::poured
  SAN["sanity<br/>metadata.dev_bead = dev"]:::poured
  QA["qa (created at sanity PASS)"]:::tmpl
  DEV ==>|parent-child| SPR
  SAN ==>|parent-child| SPR
  SAN ==>|blocks| DEV
  QA -->|parent-child| SPR
  QA -->|validates| DEV
  QA -->|blocks| SAN
```

Trade-off: no new edge, no new script, and `bd ready` stays the queue. But
"what does this sanity check" is read from a `blocks` edge plus
`metadata.dev_bead`, not from a dedicated edge type. The sanity bead's
`blocks` edge to its checked bead, together with the required `SanityBead`
`metadata.dev_bead`, handles both gating and correlation. QA is created at
sanity PASS, so it can carry `validates` to the checked bead without a
conflict. If the formula pours QA at plan time instead, the same edges still
hold, because QA-to-dev and QA-to-sanity are different pairs.

**Open decisions**

1. E1: A, B or C. No option is recommended here.
2. T1: custom issue types are supported (`bd config set types.custom`, per
   database), and the withdrawn contract dropped them. Given "no `stage:`
   labels", does classification of dev, sanity and QA use `issue_type`
   (custom or built-in) or schema metadata?
