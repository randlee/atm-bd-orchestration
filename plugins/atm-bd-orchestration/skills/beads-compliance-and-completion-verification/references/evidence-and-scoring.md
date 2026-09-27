# Evidence, calibration, and remediation priority

## Evidence record

Keep one record per bead and criterion; retain raw proof alongside summaries.

| Field | Meaning |
| --- | --- |
| bead / criterion | Stable ID and exact acceptance text, including an approved amendment if applicable |
| checked commit | Code revision actually examined; identify PR head/base where relevant |
| citation | File and line, test name, CI run, sanity/QA artifact, or merge record |
| command / environment | What executed, where, with which tools and relevant inputs |
| result | Exit code and observed/asserted behavior; paths to raw stdout/stderr |
| verdict | PASS, PARTIAL, FAIL, or UNVERIFIED, with reason |
| consequence | User-visible or integration effect of the actual gap |
| next action | Exact missing work or check, scope, owner if known |

Record development, sanity, QA, and integration/merge separately. A status label
or score must never stand in for these stages. A FAIL needs contrary evidence;
an unavailable test environment is UNVERIFIED, not an invented implementation failure.

## Optional source rubric

Use scoring only when it helps compare a requested audit set. Publish and freeze
the rubric for the pass; criterion-level verdicts remain authoritative.

| Dimension | Source default weight |
| --- | ---: |
| Implementation against specification | 300 |
| Required tests present and meaningful | 250 |
| No stubs or prohibited substitutes | 150 |
| Test depth on the bead's surface | 150 |
| Required documentation/telemetry/migrations | 100 |
| Cross-bead integration | 50 |

The source uses a 0–1000 score and default review threshold of 700. Treat a low
heuristic score as a review candidate until corroborated; a high score cannot
override a failed mandatory acceptance criterion. Declare how non-applicable
dimensions and missing evidence are handled. Do not penalize a docs-only bead
for absent runtime tests, or infer an individual failure from global coverage.

Before a large-count headline, inspect the bottom 5–10 candidates, or all if
fewer. Reconcile commit-message conventions, stale citations, missing tooling,
and deliberately staged work. Retain corrections to the audit, not just changes
to the product. Do not attribute blame from an automated score.

## Order confirmed remediation

Combine severity, concrete user consequence, stored priority, and downstream
work released. The source formula is a useful optional comparison:

```
(1000 - verified_score) * consequence_multiplier * clamp(open_dependents, 1, 10)
    + priority_bonus
```

Source multipliers: critical user-facing 2.0, user-facing 1.5, infrastructure
1.3, developer-facing 1.0, internal optimization 0.7, unused code candidate 0.3.
Source bonuses: P0 +200, P1 +100, P2/P3 0, P4 -50. Label the result a heuristic;
do not compute it from incomplete scores or let it expand approved scope.
Explain the consequence and blocker IDs even when presenting a numeric rank.

For work that stays stuck, identify the cause before repeating a dispatch:
missing owner, unmet dependency, vague acceptance, conflicting scope, or a
failed approach. Improve the assignment or resolve the decision through the
lead. Abandoned or duplicate work needs an explicit disposition, not closure
solely to improve graph health.

## Stop conditions

Report the scoped audit complete when each requested criterion has a supported
verdict, uncertain results are explicit, and any authorized remediation is
recorded and validated. For repeated audits, convergence means no new confirmed
gaps or contract contradictions under the same scope/rubric, with stable
evidence and an independent check. Respect repository review-round limits.
Convergence does not mean unresolved remediation has been implemented.
