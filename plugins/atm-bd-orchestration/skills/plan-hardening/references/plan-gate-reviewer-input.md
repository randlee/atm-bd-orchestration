# Plan Gate Reviewer Input

The existing Plan Gate supplies `plan-scope-reviewer` with the JSON envelope
rendered by
`skills/atm-bd-orchestration/templates/plan-scope-reviewer-assignment.json.j2`.
Its `phase_root_doc` and `plan_docs` are captured `bd show --json` output for
the root and sprint containers, not markdown plan sources. The template owns
this transport envelope; the reviewer agent's single input contract remains
the source of review rules.

## Inputs JSON for Plan Gate

```json
{
  "scope": {"phase": "phase id", "sprint": null},
  "plan": "beads",
  "root": "<phase root bead id>",
  "phase_root_doc": "<root bd JSON capture>",
  "plan_docs": ["<sprint-container bd JSON capture>"],
  "reference_docs": ["<planning rules or architecture reference>"],
  "worktree_path": "<absolute checkout>",
  "branch": "<branch>",
  "commit": "<commit>",
  "round_index": 1,
  "carry_forward_findings": [],
  "findings_scope_locked": false,
  "notes": ""
}
```

When `findings_scope_locked` is true, verify only `carry_forward_findings`
against their original acceptance criteria. Do not make a new plan-shape
review or file new findings. The assignment template requires a nonempty
carry-forward list after round 1 and sets `findings_scope_locked` from that
list; round 1 remains an unlocked full review.
