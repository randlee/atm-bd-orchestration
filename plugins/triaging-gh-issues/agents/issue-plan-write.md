---
name: issue-plan-write
version: 1.0.0
description: Return status/planned and one plan bead id.
---

# issue-plan-write

## Purpose
Return status/planned and one plan bead id.

## Inputs
- title, body, area

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "status/planned", "plan_bead": "<id>"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- data.plan_bead is one id. Backlog follows area/.
- Do not set status/plan-accepted.
