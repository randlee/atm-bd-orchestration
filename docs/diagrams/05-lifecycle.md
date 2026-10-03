# 5. Lifecycle (sprint level)

## 5a. Ready, claim and close order

```mermaid
sequenceDiagram
  autonumber
  participant L as lead
  participant B as bd
  participant A as ATM
  participant D as dev member
  participant S as sanity member
  participant Q as quality-mgr
  participant G as logs in .sc

  Note over L,B: plan import: sprint container from sprint-bead.json.j2,<br/>then the sprint formula attaches dev, sanity, qa (07)
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
    S->>B: bd close sanity, verdict PASS + round (C1, today close_reason "PASS at sha")
  else FAIL
    S->>B: file sanity findings (Q3), sanity stays open today (C1, C2)
  end
  S->>A: atm task close same-id
  L->>B: bd ready
  B-->>L: qa
  L->>A: atm task assign Q --task-id qa-bead-id
  Q->>B: claim qa
  Q->>B: file findings: FindingBead, metadata.severity, parent-child sprint (blocking), discovered-from qa
  Q->>G: append .sc/qa-log/phase-p.jsonl and phase-p-stats.jsonl
  Q->>B: bd close qa, verdict + round (C1, today metadata.round + close_reason "FAIL: n findings filed")
  Q->>A: atm task close same-id completed
  loop each open blocking finding
    L->>B: pour finding formula, round n (07)
    Note over L,Q: fix, fix sanity, fix qa run in the same order as dev, sanity, qa<br/>and append the same logs. Fix qa FAIL means pour round n+1, never reopen (C2).
    L->>B: close the finding after its fix qa PASS (Q4)
  end
  L->>B: bd close sprint container when no child is open (Q4)
```

**Legend.** Each `atm task` id equals the bead id (06). Where each fact is
written:

| Fact | Bead | Field today | Field to-be |
| --- | --- | --- | --- |
| sanity verdict, pinned sha | sanity bead | `close_reason` "PASS at sha" | `metadata.verdict`, `metadata.commit` (C1) |
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
2. C2: if a sanity FAIL closes its bead, the sanity bead's `blocks` edge
   releases the next sprint's "normal" dependency (02). Either a sanity FAIL
   keeps the bead open, as today, or gating reads `verdict` instead of
   status.
3. Q3: where sanity-FAIL findings live, and whether they get a group.
4. Q4: who closes a finding and the sprint container, and when.

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
stops being the queue. The `SanityBead` model, which requires a `blocks`
edge, must change. A formula step cannot pour `validates` (N4).

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
