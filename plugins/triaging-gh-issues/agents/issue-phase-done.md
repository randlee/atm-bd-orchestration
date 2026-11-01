---
name: issue-phase-done
version: 1.0.0
description: Return phase-done/no or phase-done/yes.
---

# issue-phase-done

## Purpose
Return phase-done/no or phase-done/yes.

## Inputs
- phase bead id, pr, commit

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "phase-done/yes", "pr": "1", "commit": "<full-sha>"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- On yes, data also has pr and commit. One label.
