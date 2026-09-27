# Select the analysis for the decision

All commands below run against the helper's explicit, freshly exported JSONL.
Inspect installed `bv --help` / `bv --robot-schema` for supported flags and
output shapes before adding queries. Version differences must not silently
turn missing fields into zero findings.

| Robot command | Decision it supports |
| --- | --- |
| `--robot-triage` | Candidates, reasons, quick wins, blockers-to-clear, and graph health |
| `--robot-alerts` | Staleness, priority mismatch, and other alerts; examine type/severity and supporting IDs |
| `--robot-plan` | Dependency-respecting parallel tracks and what each unlocks |
| `--robot-insights` | Centrality, bottlenecks, cycles, articulation, and critical-path/slack metrics |
| `--robot-priority` | Suggested priority changes with reasons and confidence |
| `--robot-blocker-chain <id>` | Root prerequisites preventing a specific bead from advancing |
| `--robot-next` | A single candidate when the scope and readiness checks are already established |
| `--robot-label-flow` | Dependencies crossing labels; useful for another team's prerequisites |
| `--robot-suggest` | Candidate duplicate, missing dependency, or cycle corrections requiring review |

Triage nests its decision data under `triage`; insights and priority have
different shapes. Do not apply one jq expression to every command. Read metric
status flags (`computed`, `approx`, `timeout`, `skipped`) and source authority.
An empty cycle list with cycle computation skipped does not prove acyclicity.

## Meaning of the metrics

- **PageRank:** recursive structural importance, useful for finding foundational
  prerequisites. Confirm the actual dependent IDs and edge direction.
- **Betweenness:** paths concentrated through a bead; inspect it as a possible
  bottleneck, including whether it is a gate instead of implementation work.
- **Critical path / slack:** scheduling structure in the graph. Without actual
  durations and a documented unit, these are not calendar deadlines or days late.
- **Articulation / k-core:** connections and clusters worth investigating for
  cross-bead integration; they do not prove user impact or missing code.
- **Cycles:** examine the participating scheduling edges and intended handoffs.
  Resolve the underlying dependency mistake instead of deleting arbitrary edges.

The source skills combine these metrics with priority and user consequence.
Do not use a universal density threshold or centrality score as proof of graph
correctness. A high-impact backlog item can remain outside the current plan.

## Follow-up analyses

Recipes (`actionable`, `high-impact`, `bottlenecks`) help explore different
views, but filtering can hide prerequisites. Keep a full snapshot for chain
inspection. Capture exact query scope alongside every result.

History, diff, burndown, and forecast commands need appropriate history and
sprint data. A fresh Dolt export proves current issue state, not that local Git
contains historical bead snapshots. Verify those inputs before using `--as-of`
or treating bead-to-commit correlations as evidence of completion.

Feedback commands change future ranking; script emission can suggest mutations.
Neither is required for ordinary prioritization. Do not execute emitted claims
or record feedback without the corresponding authorized action.

## Scope to children of an epic

BV v0.25.0 has no native epic-children filter. The bundled helper filters the
export **before running BV**:

```bash
python3 <skill-dir>/scripts/analyze.py --repo <live-checkout> --epic <epic-id>
```

`issues.jsonl` preserves the full live export. `epic.jsonl` contains the epic and
all recursive descendants identified by `parent-child` relationships, with only
edges between included records. It does not infer membership from ID prefixes,
labels, or blocking edges. The root may be stored as a feature or epic; its
hierarchy determines membership. `receipt.json` records membership and every excluded
cross-boundary edge, in either direction. No live bead is changed.

Triage, alerts, plans, insights, and priorities use `epic.jsonl`. Metrics therefore
cover the selected hierarchy. External blockers and downstream impact are not
included in those metrics; inspect `excluded_dependencies` and add
`--target <candidate-id>` for a blocker-chain check against the full export.
Confirm live `bd ready` before dispatch. An epic with no descendants yields
only the root, which is not a coding assignment.

For direct children only, `bd list --parent <epic-id> --all -n 0 --json` is a
useful membership query; the helper's epic scope is recursive. `--graph-root`
selects a dependency subgraph for graph output and is not a hierarchy filter.
Use `--label` as an alternative when the requested scope is a label; the helper
rejects combining it with `--epic` to avoid silently excluding descendants.
