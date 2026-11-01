---
name: issue-arch-classify
version: 1.0.0
description: Return one arch label.
---

# issue-arch-classify

## Purpose
Return one arch label.

## Inputs
- title, body

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "arch/none"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One of arch/none, arch/impact, arch/already-exists.
