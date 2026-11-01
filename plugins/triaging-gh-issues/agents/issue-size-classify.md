---
name: issue-size-classify
version: 1.0.0
description: Return one size label.
---

# issue-size-classify

## Purpose
Return one size label.

## Inputs
- title, body

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "size/s"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One of size/s, size/m, size/l, size/xl.
