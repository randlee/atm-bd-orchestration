---
name: issue-gap-classify
version: 1.0.0
description: Return one gap label.
---

# issue-gap-classify

## Purpose
Return one gap label.

## Inputs
- title, body

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "status/needs-info"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One of status/needs-info, status/needs-repro, status/needs-design.
