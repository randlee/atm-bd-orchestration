# 7. The sc-compose beads formula (detail)

Sources:

- randlee/sc-compose #551: proposal to author bd formulas with sc-compose.
- randlee/sc-compose #613: attaching sprint workflows to existing parents,
  with resume-safe expansion.
- sc-compose ADR-0021 (accepted, `docs/adrs/0021-beads-formula-composition-integration.md`
  at sc-compose 58f4d00): the `sc-compose/beads/v1` request contract.
- `sc-compose bead --help` (1.6.1) and `bd formula schema step` (bd 1.3.0).

Neither formula exists yet. The attach operation #613 asks for does not exist
in sc-compose 1.6.1, which offers `render`, `validate`, `preview-pour` and
`pour`. Until it exists, a mock script stands in for the sc-compose pour. A
separate agent is writing that mock now.

Decided (Rand): formulas live in the package for now (N1). Pouring has three
stages (N4):

1. sc-compose pours the formula (the mock for now);
2. a post-pour step adds the edges a formula cannot express: `validates`,
   `discovered-from` and cross-sprint `blocks`;
3. everything else is created by hand or by a script.

## 7a. The three stages, inputs, and where the formula is defined

```mermaid
flowchart LR
  classDef file fill:#f1f3f4,stroke:#5f6368,stroke-dasharray:4 3,color:#000
  classDef future fill:#fce8e6,stroke:#c5221f,stroke-dasharray:2 2,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef post fill:#fff8e1,stroke:#b06000,stroke-dasharray:1 3,color:#000
  classDef hand fill:#fff4e5,stroke:#e8710a,color:#000

  subgraph SRC["formula source"]
    PKG[/"package default (decided, N1)<br/>randlee/atm-bd-orchestration<br/>plugins/atm-bd-orchestration/skills/atm-bd-orchestration/formulas/<br/>sprint-group.formula.toml.j2<br/>finding-group.formula.toml.j2"/]:::file
    OVR[/"repo override (FUTURE)<br/>a consuming repo's own copy of a package formula<br/>path not decided"/]:::future
  end

  REQ[/"request JSON, schema sc-compose/beads/v1<br/>template, rendered_formula, formula_name<br/>compose_variables: members, sprint or finding fields, schema version<br/>bead_variables: parent, sprint, phase, stack, round<br/>pour_authorization CreatePersistentBeads"/]:::file

  subgraph S1["stage 1: poured by sc-compose (mock for now)"]
    POUR["render, bd cook --dry-run, bd where,<br/>attach under parent (#613; mock until built)<br/>pours: beads + parent-child + blocks between its own steps"]:::poured
  end
  subgraph S2["stage 2: post-pour step"]
    PP["adds validates, discovered-from,<br/>cross-sprint blocks (from sprints.jsonl)<br/>reads the pour receipt for poured ids"]:::post
  end
  subgraph S3["stage 3: hand or script"]
    HS["templates + bd import (sprint container, findings),<br/>package scripts (sanity-create-findings),<br/>lead bd create / bd dep add"]:::hand
  end
  RCPT[/"receipt: stages, outcome,<br/>parent id to poured ids (#613)"/]:::file
  OUT[/"rendered formula (ADR-0021):<br/>active-beads-dir/formulas/name.formula.toml"/]:::file

  PKG --> REQ
  OVR -. "future: replaces the default" .-> REQ
  REQ --> POUR
  POUR --> OUT
  POUR --> RCPT
  RCPT --> PP
```

**Legend.** Stage 1 (purple) is the pour. Its edges are drawn as thick arrows
in every diagram. Stage 2 (amber) is the post-pour step. Its edges are drawn
as dotted arrows. Stage 3 (orange) is everything made by hand or by a script,
drawn as solid arrows. ADR-0021 fixes the rendered output path,
`<active-beads-dir>/formulas/<formula-name>.formula.toml`; the package
directory holds the source the request renders from. #551 notes that bd
formulas have no foreach and no list variables. Neither group formula needs
one: each pours a fixed three steps.

What a formula step can express (`bd formula schema step`, bd 1.3.0):

- `title`, `type` (built-in, or a custom type already in `types.custom`; any
  other type is flattened to `task` with a warning), `labels`, `metadata`,
  `assignee`, `priority`;
- `needs` or `depends_on`, which take only sibling step ids and pour `blocks`
  edges.

So the pour itself cannot create `validates`, `discovered-from`, or an edge to
a bead outside the formula (#613: "A formula dependency on an external sprint
fails as an unknown step"). Those are stage 2.

**Open decisions**

1. N7: where a future repo override lives, and how the package default is chosen
   when no override exists.
2. N8: whether the post-pour step is a package script or part of the mock and,
   later, of the sc-compose attach operation.

## 7b. Sprint formula: the exact beads and edges, by stage

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000
  classDef open fill:#fce8e6,stroke:#c5221f,stroke-dasharray:2 2,color:#000

  SPR["p-d-29 sprint container (stage 3: plan import)<br/>bead_variables.parent = p-d-29"]:::tmpl
  MOL["molecule root (N5: only if attach<br/>goes through an intermediate container)"]:::open
  subgraph POUR["poured by sc-compose (mock): sprint-group formula"]
    DEV["step dev<br/>type: T1, assignee: dev member<br/>metadata: sprint, phase, stack"]:::poured
    SAN["step sanity, needs dev (A, C)<br/>type: T1, assignee: sanity member<br/>metadata.dev_bead = dev id"]:::poured
    QA["step qa, needs sanity<br/>type: T1, assignee: qa_member<br/>metadata: checked_bead, round = 1"]:::poured
  end
  NEXT["next sprint container (stage 3)"]:::tmpl

  DEV ==>|parent-child| SPR
  SAN ==>|parent-child| SPR
  QA ==>|parent-child| SPR
  SAN ==>|"blocks (needs dev): E1 options A and C"| DEV
  SAN -.->|"validates: E1 option B"| DEV
  QA ==>|"blocks (needs sanity)"| SAN
  QA -.->|"validates (C3)"| DEV
  NEXT -.->|"blocks (normal or tight, from sprints.jsonl)"| SAN
  MOL -.- SPR
```

**Legend.** Thick arrows are stage 1, dotted arrows are stage 2, solid nodes
are stage 3. Exactly one of the two sanity-to-dev edges exists, depending on
E1. Under option B the formula's sanity step has no `needs dev`, and the
post-pour step adds `validates`. The "tight" variant points the cross-sprint
`blocks` at the sprint container instead of the sanity bead (02). Today
`bd mol pour` creates a new parentless molecule with generated ids, and a
sprint variable does not attach it (#613 gap 1). So the stage 1 `parent-child`
edges to the existing sprint need the attach operation, and the mock provides
it until then.

**Open decisions**

1. E1: A, B or C (05). All three are feasible with the post-pour step.
2. N2: the ids of the poured beads must be deterministic and must match the
   sanity id that `sprints.jsonl` names at plan time. Native
   `bd mol bond --ref` gives `<parent>.<ref>.<step>`, for example
   `p-d-29.group.sanity`; plain `pour` gives generated ids.
3. N5: #613 asks sc-compose to document whether children attach directly
   under the sprint or under an intermediate workflow container (the molecule
   root).
4. Metadata values in a step (`metadata.dev_bead = dev id`) assume variable
   substitution inside `metadata`. bd documents substitution for title,
   description, notes and assignee only. Unverified; if it is unsupported,
   the post-pour step writes them.

## 7c. Finding formula: the exact beads and edges for one blocking finding

```mermaid
flowchart TB
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef poured fill:#f3e8fd,stroke:#8430ce,stroke-width:3px,stroke-dasharray:6 3,color:#000

  SPR["p-d-29 sprint container"]:::tmpl
  QA1["p-d-29 qa round 1 (closed, FAIL)"]:::tmpl
  F["p-d-29-qa1-f3 blocking finding (stage 3: QA, finding-bead.json.j2)<br/>bead_variables.parent = the finding (Q1)<br/>bead_variables.round = n"]:::tmpl
  subgraph POUR["poured by sc-compose (mock): finding-group formula, round n"]
    FX["step fix<br/>id suffix -rn"]:::poured
    FS["step fix-sanity, needs fix (A, C)<br/>metadata.dev_bead = fix id"]:::poured
    FQ["step fix-qa, needs fix-sanity<br/>metadata: checked_bead, round = n"]:::poured
  end

  F -->|parent-child| SPR
  F -->|discovered-from| QA1
  FX ==>|parent-child| F
  FS ==>|parent-child| F
  FQ ==>|parent-child| F
  FS ==>|"blocks (needs fix): E1 A, C"| FX
  FQ ==>|"blocks (needs fix-sanity)"| FS
  FQ -.->|"validates (C3)"| FX
```

**Legend.** One pour per blocking finding, independent of every other finding
(Q1, decided). The finding itself is stage 3: QA files it from
`finding-bead.json.j2`, and that import creates its `parent-child` and
`discovered-from` edges. The post-pour step adds `discovered-from` only when a
bead is not created by that template. A second round is the same formula
poured again with `round = n+1` (04c). Important and minor findings get no
pour; they wait under the phase feature bead (Q2, 02b).

**Open decisions**

1. N2: round-unique ids (`-r1`, `-r2`) as a formula input.
2. C3: whether the fix QA validates the fix bead or the finding.

## 7d. Resume-safe attach onto an existing parent (#613)

```mermaid
flowchart TB
  classDef ok fill:#e6f4ea,stroke:#188038,color:#000
  classDef bad fill:#fce8e6,stroke:#c5221f,color:#000

  REQ["attach request: parent id, formula name + revision, vars"]
  PREV["preview: the resulting parent-child tree and the blocks edges,<br/>with no write"]
  AUTH{"explicit persistent-write<br/>authorization?"}
  R0["refuse"]:::bad
  EACH["for each expected node and edge"]
  EXISTS{"already exists<br/>under this parent?"}
  SAME{"same formula revision<br/>and scope?"}
  NOOP["no-op: never reset status,<br/>notes, claims or evidence"]:::ok
  CONFLICT["refuse: conflicting revision or scope"]:::bad
  CREATE["create only the missing node or edge"]:::ok
  RCPT["receipt: parent id to poured ids"]:::ok

  REQ --> PREV --> AUTH
  AUTH -- no --> R0
  AUTH -- yes --> EACH --> EXISTS
  EXISTS -- yes --> SAME
  SAME -- yes --> NOOP
  SAME -- no --> CONFLICT
  EXISTS -- no --> CREATE
  NOOP --> RCPT
  CREATE --> RCPT
```

**Legend.** These are the behaviors #613 requires. Running the same request
again changes nothing, and a run that stopped partway resumes by creating only
what is missing. #613 observed that native `bd mol bond --type parallel --ref`
attaches deterministically, but repeating it reopened a closed child and
cleared its notes on bd 1.3.0. So bond cannot be used blindly for resume. That
behavior is an upstream bd concern, and sc-compose must not expose it as a
safe retry. The mock that stands in for sc-compose must keep the same rules,
and the post-pour step (stage 2) must be idempotent in the same way: it adds
only edges that are missing.

**Open decisions**

1. N5: direct attach, or attach under an intermediate workflow container.
2. N2: stable identity. Resume matching needs ids, or a recorded formula
   revision and scope, that a second run can find again.
