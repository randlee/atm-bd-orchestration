# Correlation: beads, ATM tasks and the current phase

```mermaid
flowchart LR
  classDef tmpl fill:#e8f0fe,stroke:#3367d6,color:#000
  classDef file fill:#f1f3f4,stroke:#5f6368,stroke-dasharray:4 3,color:#000
  classDef atm fill:#fef7e0,stroke:#f9ab00,color:#000

  subgraph ATMBD[".atm-bd/"]
    TOML[/"current-phase.toml (untracked, per checkout)<br/>root = p-phase-x<br/>sprints = path of sprints.jsonl<br/>integration_branch"/]:::file
    FORM[/"formula/ (tracked): repo formula overrides"/]:::file
  end
  ROOT["p-phase-x root bead<br/>metadata.integration_branch"]:::tmpl
  SJ[/"sprints.jsonl on the integration branch"/]:::file
  BEAD["bead under the root<br/>id = p-x-2.group-sanity"]:::tmpl
  TASK["ATM task<br/>task id = p-x-2.group-sanity"]:::atm

  TOML -. "root" .-> ROOT
  TOML -. "sprints" .-> SJ
  ROOT -->|"descendant (parent-child chain)"| BEAD
  BEAD <-. "bead id == ATM task id" .-> TASK
```

`.atm-bd/current-phase.toml` is per checkout and untracked, so every worktree
resolves its own phase root. The consuming repository's `.gitignore` has
`.atm-bd/*` followed by `!.atm-bd/formula/`. Work is assigned with
`atm task assign <member> --task-id <bead id>`; the claim at dispatch sets the
bead's assignee.

| Bead | ATM task held by | Template |
| --- | --- | --- |
| dev | a dev, by `difficulty` | `dev-template.xml.j2` (`dev-fix.xml.j2` after a sanity FAIL) |
| fix | a dev, by `difficulty` | `fix-assignment.xml.j2` |
| sanity | dev-sanity | `dev-sanity-template.xml.j2` |
| qa | quality-mgr | `qa-template.xml.j2` |
| important or minor finding | an idle dev, by priority | `fix-assignment.xml.j2` |
| sprint container | none; the team lead closes it | none |
