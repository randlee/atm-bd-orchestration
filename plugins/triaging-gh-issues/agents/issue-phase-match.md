---
name: issue-phase-match
version: 1.0.0
description: Return phase/none or phase/<bead>.
---

# issue-phase-match

## Purpose
Return phase/none or phase/<bead>.

## Inputs
- title, active phase bead ids

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "phase/none"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One label. An active phase root is open.
