---
name: issue-duplicate-judge
version: 1.0.0
description: Return dup/none or dup/#N.
---

# issue-duplicate-judge

## Purpose
Return dup/none or dup/#N.

## Inputs
- title, body, open issue numbers

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "dup/none"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One label. Do not classify kind, area, size, or priority.
