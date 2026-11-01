---
name: plan-accept
version: 1.0.0
description: Return status/plan-accepted or status/plan-rejected.
---

# plan-accept

## Purpose
Return status/plan-accepted or status/plan-rejected.

## Inputs
- plan bead id

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "status/plan-accepted"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One label. Do not open a pull request.
