---
name: issue-overlap-judge
version: 1.0.0
description: Return overlap/none or overlap/<bead>.
---

# issue-overlap-judge

## Purpose
Return overlap/none or overlap/<bead>.

## Inputs
- title, candidate bead ids

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "overlap/none"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One label. Do not invent a parent when no bead exists.
